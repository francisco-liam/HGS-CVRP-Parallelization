//
// Created by chkwon on 3/22/22.
//

#ifndef INSTANCECVRPLIB_H
#define INSTANCECVRPLIB_H
#include<string>
#include<vector>

class InstanceCVRPLIB
{
public:
	std::vector<double> x_coords;
	std::vector<double> y_coords;
	std::vector< std::vector<double> > dist_mtx;
	std::vector<double> service_time;
	std::vector<double> demands;
	std::vector<int> stationIndices;                    // Indices of charging stations (1-based as in file)
	double durationLimit = 1.e30;							// Route duration limit
	double vehicleCapacity = 1.e30;							// Capacity limit
	double energyCapacity = 0.0;							// Battery capacity (ECVRP)
	double energyConsumption = 0.0;							// Energy consumption (ECVRP)
	bool isDurationConstraint = false;						// Indicates if the problem includes duration constraints
	int nbClients ;											// Number of clients (excluding the depot)
	int nbStations = 0;									// Number of charging stations (ECVRP)

	InstanceCVRPLIB(std::string pathToInstance, bool isRoundingInteger);
};


#endif //INSTANCECVRPLIB_H
