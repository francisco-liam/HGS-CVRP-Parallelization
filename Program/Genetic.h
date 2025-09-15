/*MIT License

Copyright(c) 2020 Thibaut Vidal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files(the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions :

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.*/

#ifndef GENETIC_H
#define GENETIC_H

#include "Population.h"
#include "Individual.h"
#include <thread>
#include <atomic>
#include <condition_variable>
#include <mutex>
#include <tuple>
#include <vector>

class Genetic
{
public:

	// Shared atomic counters and synchronization primitives for parallelism
	static std::atomic<int> nbIter;
	static std::atomic<int> nbIterNonProd;
	static std::atomic<bool> resetInProgress;
	static std::mutex resetMutex;
	static std::condition_variable resetCV;

	// Barrier for coordinated reset
	static std::atomic<int> resetBarrierCount;
	static std::mutex resetBarrierMutex;
	static std::condition_variable resetBarrierCV;

	// Thread-safe statistics storage for (iteration, avg feasible cost, min feasible cost)
	static std::vector<std::tuple<int, double, double, double>> feasibleStats;
	static std::mutex feasibleStatsMutex;

	Params & params;				// Problem parameters
	Split split;					// Split algorithm
	LocalSearch localSearch;		// Local Search structure
	Population population;			// Population (public for now to give access to the solutions, but should be be improved later on)
	Individual offspring;			// First individual to be used as input for the crossover

	// OX Crossover
	static void crossoverOX(Individual & result, const Individual & parent1, const Individual & parent2, Split& split, std::minstd_rand& rng, int nbClients);

    // Running the genetic algorithm until maxIterNonProd consecutive iterations or a time limit
    void run() ;

	// Constructor
	Genetic(Params & params);

private:
       // Worker thread function for parallel HGS
       static void workerThread(
	       Params& params,
	       Population& population,
	       int threadId,
	       unsigned int baseSeed,
	       std::atomic<bool>& terminateFlag,
	       std::string* exceptionMsgPtr = nullptr
       );
};

#endif
