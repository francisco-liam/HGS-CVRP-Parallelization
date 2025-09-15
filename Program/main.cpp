#include "Genetic.h"
#include "commandline.h"
#include "LocalSearch.h"
#include "Split.h"
#include "InstanceCVRPLIB.h"
#include <fstream>
#include <algorithm>
using namespace std;

int main(int argc, char *argv[])
{
	try
	{
		// Reading the arguments of the program
		CommandLine commandline(argc, argv);

		// Print all algorithm parameter values
		if (commandline.verbose) print_algorithm_parameters(commandline.ap);

		// Reading the data file and initializing some data structures
		if (commandline.verbose) std::cout << "----- READING INSTANCE: " << commandline.pathInstance << std::endl;
		InstanceCVRPLIB cvrp(commandline.pathInstance, commandline.isRoundingInteger);

		Params params(cvrp.x_coords,cvrp.y_coords,cvrp.dist_mtx,cvrp.service_time,cvrp.demands,
			          cvrp.vehicleCapacity,cvrp.durationLimit,commandline.nbVeh,cvrp.isDurationConstraint,commandline.verbose,commandline.ap);

		// Running HGS
		Genetic solver(params);
		solver.run();
		
		// Exporting the best solution
		if (solver.population.getBestFound() != NULL)
		{
			if (params.verbose) std::cout << "----- WRITING BEST SOLUTION IN : " << commandline.pathSolution << std::endl;
			solver.population.exportCVRPLibFormat(*solver.population.getBestFound(),commandline.pathSolution);
			solver.population.exportSearchProgress(commandline.pathSolution + ".PG.csv", commandline.pathInstance);
		}

		// Write the recorded stats to a CSV file (sorted by iteration)
		if (!Genetic::feasibleStats.empty()) {
			auto stats = Genetic::feasibleStats;
			std::sort(stats.begin(), stats.end(), [](const auto& a, const auto& b) { return std::get<0>(a) < std::get<0>(b); });
			std::string statsFile = commandline.pathSolution;
			if (statsFile.size() >= 4 && statsFile.substr(statsFile.size() - 4) == ".sol")
				statsFile = statsFile.substr(0, statsFile.size() - 4) + "_stats.csv";
			else
				statsFile += "_stats.csv";
			if (params.verbose) std::cout << "----- WRITING STATS IN : " << statsFile << std::endl;
			std::ofstream csv(statsFile);
			csv << "Iteration,AvgFeasibleCost,MinFeasibleCost\n";
			for (const auto& tup : stats) {
				csv << std::get<0>(tup) << "," << std::get<1>(tup) << "," << std::get<2>(tup) << "\n";
			}
		}
	}
	catch (const string& e) { std::cout << "EXCEPTION | " << e << std::endl; }
	catch (const std::exception& e) { std::cout << "EXCEPTION | " << e.what() << std::endl; }
	return 0;
}
