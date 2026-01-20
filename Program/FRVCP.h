#ifndef FRVCP_H
#define FRVCP_H

#include <vector>
#include "Params.h"

class FRVCP
{
public:
	struct RouteResult
	{
		bool feasible = true;
		double distance = 0.0;
		std::vector<int> routeWithChargers; // route excluding depot, includes chargers
	};

	// Build a route with charging stations inserted using shortest feasible paths between customers.
	// Assumes full charge at depot and at each charging station. Cost is distance only.
	static RouteResult buildRouteWithChargers(const Params &params, const std::vector<int> &route);

private:
	static bool shortestFeasiblePath(
		const Params &params,
		int fromNode,
		int toNode,
		std::vector<int> &path,
		double &distance);
};

#endif
