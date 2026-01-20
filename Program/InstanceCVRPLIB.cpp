//
// Created by chkwon on 3/22/22.
//

#include <fstream>
#include <cmath>
#include "InstanceCVRPLIB.h"

InstanceCVRPLIB::InstanceCVRPLIB(std::string pathToInstance, bool isRoundingInteger = true)
{
	std::string content, content2, content3;
	double serviceTimeData = 0.;
	int dimension = -1;
	int totalNodes = -1;

	// Read INPUT dataset
	std::ifstream inputFile(pathToInstance);
	if (inputFile.is_open())
	{
		getline(inputFile, content);
		getline(inputFile, content);
		getline(inputFile, content);
		for (inputFile >> content ; content != "NODE_COORD_SECTION" ; inputFile >> content)
		{
			if (!content.empty() && content.back() == ':') content.pop_back();
			auto readValueToken = [&]() {
				std::string token;
				inputFile >> token;
				if (token == ":") inputFile >> token;
				return token;
			};
			if (content == "DIMENSION") { content2 = readValueToken(); dimension = std::stoi(content2); }
			else if (content == "EDGE_WEIGHT_TYPE")	{ content2 = readValueToken(); content3 = content2; }
			else if (content == "CAPACITY")	{ content2 = readValueToken(); vehicleCapacity = std::stod(content2); }
			else if (content == "STATIONS")	{ content2 = readValueToken(); nbStations = std::stoi(content2); }
			else if (content == "ENERGY_CAPACITY")	{ content2 = readValueToken(); energyCapacity = std::stod(content2); }
			else if (content == "ENERGY_CONSUMPTION")	{ content2 = readValueToken(); energyConsumption = std::stod(content2); }
			else if (content == "DISTANCE") { content2 = readValueToken(); durationLimit = std::stod(content2); isDurationConstraint = true; }
			else if (content == "SERVICE_TIME")	{ content2 = readValueToken(); serviceTimeData = std::stod(content2); }
			else if (content == "NAME" || content == "COMMENT" || content == "TYPE" || content == "OPTIMAL_VALUE" || content == "VEHICLES")
			{
				// Skip remainder of line for metadata entries
				std::getline(inputFile, content2);
			}
			else throw std::string("Unexpected data in input file: " + content);
		}
		if (dimension <= 0) throw std::string("Number of nodes is undefined");
		if (nbStations < 0) throw std::string("Number of stations is invalid");
		totalNodes = dimension;
		// nbClients should exclude depot and stations
		nbClients = totalNodes - 1 - nbStations;
		if (nbClients <= 0) throw std::string("Number of clients is undefined");
		if (vehicleCapacity == 1.e30) throw std::string("Vehicle capacity is undefined");

		// Coordinates for all nodes (customers, depot, stations)
		x_coords = std::vector<double>(totalNodes);
		y_coords = std::vector<double>(totalNodes);
		// Demands/service times only for depot + customers
		demands = std::vector<double>(nbClients + 1);
		service_time = std::vector<double>(nbClients + 1);

		// Reading node coordinates
		// depot must be the first element
		// 		- i = 0 in the for-loop below, or
		// 		- node_number = 1 in the .vrp file
		// customers are
		// 		- i = 1, 2, ..., nbClients in the for-loop below, or
		// 		- node_number = 2, 3, ..., nb_Clients in the .vrp file
		int node_number;
		for (int i = 0; i < totalNodes; i++)
		{
			inputFile >> node_number >> x_coords[i] >> y_coords[i];
			if (node_number != i + 1) throw std::string("The node numbering is not in order.");
		}

		// Reading demand information
		inputFile >> content;
		if (content != "DEMAND_SECTION") throw std::string("Unexpected data in input file: " + content);
		for (int i = 0; i <= nbClients; i++)
		{
			inputFile >> content >> demands[i];
			service_time[i] = (i == 0) ? 0. : serviceTimeData ;
		}

		// Calculating 2D Euclidean Distance
		dist_mtx = std::vector < std::vector< double > >(totalNodes, std::vector <double>(totalNodes));
		for (int i = 0; i < totalNodes; i++)
		{
			for (int j = 0; j < totalNodes; j++)
			{
				dist_mtx[i][j] = std::sqrt(
					(x_coords[i] - x_coords[j]) * (x_coords[i] - x_coords[j])
					+ (y_coords[i] - y_coords[j]) * (y_coords[i] - y_coords[j])
				);

				if (isRoundingInteger) dist_mtx[i][j] = round(dist_mtx[i][j]);
			}
		}

		// Read station indices (ECVRP) if present
		inputFile >> content;
		if (content == "STATION_COORD_SECTION" || content == "STATIONS_COORD_SECTION")
		{
			while (inputFile >> content)
			{
				if (content == "DEPOT_SECTION") break;
				stationIndices.push_back(std::stoi(content) - 1);
			}
		}

		// Reading depot information (list terminated by -1)
		if (content != "DEPOT_SECTION") throw std::string("Unexpected data in input file: " + content);
		bool foundDepot = false;
		while (inputFile >> content)
		{
			if (content == "-1") break;
			if (!foundDepot)
			{
				if (content != "1") throw std::string("Expected depot index 1 instead of " + content);
				foundDepot = true;
			}
		}
		if (!foundDepot) throw std::string("Depot section missing depot index");
		// Consume EOF token if present
		if (inputFile >> content)
		{
			if (content != "EOF") throw std::string("Unexpected data in input file: " + content);
		}
		if (nbStations == 0 && !stationIndices.empty())
		{
			nbStations = (int)stationIndices.size();
			nbClients = totalNodes - 1 - nbStations;
		}
	}
	else
		throw std::string("Impossible to open instance file: " + pathToInstance);
}
