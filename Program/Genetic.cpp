#include <csignal>
#include <thread>
#include <vector>
#include <random>
#include "Genetic.h"

// Global pointer to allow signal handler to set terminateFlag
static std::atomic<bool>* globalTerminateFlag = nullptr;

void signalHandler(int signum) {
	if (globalTerminateFlag) {
		globalTerminateFlag->store(true);
	}
}


// Worker thread function for parallel HGS
// Exception-safe worker thread with global termination
void Genetic::workerThread(
	Params& params,
	Population& population,
	int threadId,
	unsigned int baseSeed,
	std::atomic<bool>& terminateFlag,
	std::string* exceptionMsgPtr
) {
	try {
		// Thread-local Split and LocalSearch
		Split split(params);
		LocalSearch localSearch(params);
		// Thread-local RNG
		std::minstd_rand rng(baseSeed + threadId);

		// Main worker loop (termination condition to be set by caller)
		int penaltyInterval = params.ap.nbIterPenaltyManagement > 0 ? params.ap.nbIterPenaltyManagement : 100;
		int traceInterval = params.ap.nbIterTraces > 0 ? params.ap.nbIterTraces : 100;
		int resetInterval = params.ap.nbIter > 0 ? params.ap.nbIter : 1000;

		//int numThreads = std::thread::hardware_concurrency();
		//if (numThreads < 1) numThreads = 2;
		
		int numThreads = 2;

		while (!terminateFlag.load()) {
			// Get current iteration at start of loop
			int iter = Genetic::nbIter.fetch_add(1);

			// Selection (copy parents immediately to avoid use-after-free)
			Individual parent1(population.getBinaryTournament());
			Individual parent2(population.getBinaryTournament());
			Individual offspring(params);

			// Crossover (OX) -- now thread-safe
			Genetic::crossoverOX(offspring, parent1, parent2, split, rng, params.nbClients);

			// Local search
			localSearch.run(offspring, params.penaltyCapacity, params.penaltyDuration);
			bool isNewBest = population.addIndividual(offspring, true);
			if (!offspring.eval.isFeasible && rng() % 2 == 0) {
				localSearch.run(offspring, params.penaltyCapacity * 10., params.penaltyDuration * 10.);
				if (offspring.eval.isFeasible) isNewBest = (population.addIndividual(offspring, false) || isNewBest);
			}

			// Update non-productive iteration counter
			if (isNewBest) {
				Genetic::nbIterNonProd.store(0);
			} else {
				Genetic::nbIterNonProd.fetch_add(1);
			}

			// Penalty management (only one thread does it)
			if (iter % penaltyInterval == 0) {
				bool expected = false;
				if (!Genetic::resetInProgress.load() && Genetic::resetInProgress.compare_exchange_strong(expected, true)) {
					population.managePenalties();
					Genetic::resetInProgress.store(false);
				}
			}

			// Progress reporting (only one thread does it, but not tied to threadId)
			static std::atomic<int> lastReportedIter{0};
			if (iter % traceInterval == 0) {
				int expected = lastReportedIter.load();
				if (iter > expected && lastReportedIter.compare_exchange_strong(expected, iter)) {
					population.printState(iter, Genetic::nbIterNonProd.load());
				}
			}

			// Reset logic (barrier: all threads must reach this point before reset)
			if (Genetic::nbIterNonProd.load() >= resetInterval) {
		       // Early termination: if timeLimit == 0 and nbIterNonProd >= params.ap.nbIter, set terminateFlag
		       if (params.ap.timeLimit == 0 && Genetic::nbIterNonProd.load() >= params.ap.nbIter) {
			       terminateFlag.store(true);
			       break;
		       }
				// Phase 1: Barrier - all threads increment and wait
				int arrived = Genetic::resetBarrierCount.fetch_add(1) + 1;
				if (arrived < numThreads) {
					std::unique_lock<std::mutex> lock(Genetic::resetBarrierMutex);
					Genetic::resetBarrierCV.wait(lock, [&]{ return Genetic::resetBarrierCount.load() >= numThreads; });
				}
				// Phase 2: Only one thread performs the reset
				if (arrived == numThreads) {
					std::unique_lock<std::mutex> lock(Genetic::resetMutex);
					bool expected = false;
					if (!Genetic::resetInProgress.load() && Genetic::resetInProgress.compare_exchange_strong(expected, true)) {
						population.restart();
						Genetic::nbIterNonProd.store(0);
						Genetic::resetInProgress.store(false);
						Genetic::resetCV.notify_all();
					}
					// Release all threads from the barrier
					Genetic::resetBarrierCV.notify_all();
					Genetic::resetBarrierCount.store(0);
				} else {
					// Wait for reset to complete and barrier to be released
					std::unique_lock<std::mutex> lock(Genetic::resetBarrierMutex);
					Genetic::resetBarrierCV.wait(lock, [&]{ return Genetic::resetBarrierCount.load() == 0; });
				}
			}
		}
	} catch (const std::exception& ex) {
		terminateFlag.store(true);
		if (exceptionMsgPtr) {
			*exceptionMsgPtr = ex.what();
		}
	} catch (...) {
		terminateFlag.store(true);
		if (exceptionMsgPtr) {
			*exceptionMsgPtr = "Unknown exception in worker thread.";
		}
	}
}

void Genetic::run()
{	
	// INITIAL POPULATION
	population.generatePopulation();

	if (params.verbose) std::cout << "----- STARTING PARALLEL GENETIC ALGORITHM" << std::endl;

	std::atomic<bool> terminateFlag(false);
	// Set up signal handler for Ctrl+C
	globalTerminateFlag = &terminateFlag;
	std::signal(SIGINT, signalHandler);
	//int numThreads = std::thread::hardware_concurrency();
	//if (numThreads < 1) numThreads = 2; // fallback

	int numThreads = params.ap.numThreads > 0 ? params.ap.numThreads : 2;
	if (numThreads < 1) numThreads = 2;

	unsigned int baseSeed = params.ap.seed;
	std::vector<std::thread> workers;
	std::vector<std::string> exceptionMsgs(numThreads);

	// Launch worker threads
	for (int i = 0; i < numThreads; ++i) {
		workers.emplace_back(workerThread, std::ref(params), std::ref(population), i, baseSeed, std::ref(terminateFlag), &exceptionMsgs[i]);
	}

	// Monitor progress and termination
	clock_t startTime = clock();
	double timeLimit = params.ap.timeLimit;
	while (!terminateFlag.load() && (timeLimit == 0 || (double)(clock() - startTime) / (double)CLOCKS_PER_SEC < timeLimit)) {
		std::this_thread::sleep_for(std::chrono::seconds(1));
		// Optionally: print progress, check for convergence, etc.
		// population.printState(...); // Uncomment and add arguments if desired
	}
	terminateFlag = true;

	// Join all threads
	for (auto& t : workers) t.join();

	// Report any exception from worker threads
	for (int i = 0; i < numThreads; ++i) {
		if (!exceptionMsgs[i].empty()) {
			std::cerr << "Exception in worker thread " << i << ": " << exceptionMsgs[i] << std::endl;
		}
	}

    if (params.verbose) std::cout << "----- PARALLEL GENETIC ALGORITHM FINISHED. TIME SPENT: " << (double)(clock() - startTime) / (double)CLOCKS_PER_SEC << std::endl;
}

void Genetic::crossoverOX(Individual & result, const Individual & parent1, const Individual & parent2, Split& split, std::minstd_rand& rng, int nbClients)
{
	// Frequency table to track the customers which have been already inserted
	std::vector <bool> freqClient = std::vector <bool> (nbClients + 1, false);

	// Picking the beginning and end of the crossover zone
	std::uniform_int_distribution<> distr(0, nbClients-1);
	int start = distr(rng);
	int end = distr(rng);

	// Avoid that start and end coincide by accident
	while (end == start) end = distr(rng);

	// Copy from start to end
	int j = start;
	while (j % nbClients != (end + 1) % nbClients)
	{
		result.chromT[j % nbClients] = parent1.chromT[j % nbClients];
		freqClient[result.chromT[j % nbClients]] = true;
		j++;
	}

	// Fill the remaining elements in the order given by the second parent
	for (int i = 1; i <= nbClients; i++)
	{
		int temp = parent2.chromT[(end + i) % nbClients];
		if (freqClient[temp] == false)
		{
			result.chromT[j % nbClients] = temp;
			j++;
		}
	}

	// Complete the individual with the Split algorithm
	split.generalSplit(result, parent1.eval.nbRoutes);
}

Genetic::Genetic(Params & params) : 
	params(params), 
	split(params),
	localSearch(params),
	population(params,this->split,this->localSearch),
	offspring(params){}

// Static atomic counters and synchronization primitives for parallelism
std::atomic<int> Genetic::nbIter{1};
std::atomic<int> Genetic::nbIterNonProd{0};
std::atomic<bool> Genetic::resetInProgress{false};
std::mutex Genetic::resetMutex;
std::condition_variable Genetic::resetCV;

// Barrier for coordinated reset
std::atomic<int> Genetic::resetBarrierCount{0};
std::mutex Genetic::resetBarrierMutex;
std::condition_variable Genetic::resetBarrierCV;

