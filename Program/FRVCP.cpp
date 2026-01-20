#include "FRVCP.h"
#include <limits>
#include <queue>
#include <unordered_map>
#include <tuple>

namespace
{
	bool isChargerNode(int node, const std::vector<int> &stations)
	{
		for (int s : stations)
			if (s == node) return true;
		return false;
	}
}

FRVCP::RouteResult FRVCP::buildRouteWithChargers(const Params &params, const std::vector<int> &route)
{
	RouteResult result;
	result.routeWithChargers.clear();
	result.distance = 0.0;
	result.feasible = true;

	// If energy constraints are not defined, return the original route
	if (params.energyCapacity <= 0.0 || params.energyConsumption <= 0.0)
	{
		result.routeWithChargers = route;
		// Compute direct distance along depot -> customers -> depot
		int prev = 0;
		for (int cust : route)
		{
			result.distance += params.timeCost[prev][cust];
			prev = cust;
		}
		result.distance += params.timeCost[prev][0];
		return result;
	}

	const double Bmax = params.energyCapacity;
	const double consumption = params.energyConsumption;
	const double vehicleCapacity = params.vehicleCapacity;

	const int m = (int)route.size();
	std::vector<double> loadAfterServed(m + 1, vehicleCapacity);
	for (int i = 0; i < m; ++i)
	{
		int cust = route[i];
		double demand = 0.0;
		if (cust >= 0 && cust < (int)params.cli.size())
			demand = params.cli[cust].demand;
		loadAfterServed[i + 1] = loadAfterServed[i] - demand;
	}

	struct State
	{
		int pos;
		int node;
		double soc;
		bool operator==(const State &o) const
		{
			return pos == o.pos && node == o.node && std::llround(soc * 1000000.0) == std::llround(o.soc * 1000000.0);
		}
	};

	auto loadAtNode = [&](const State &cur) -> double {
		if (cur.node == 0 || isChargerNode(cur.node, params.stationIndices))
			return loadAfterServed[cur.pos];
		if (cur.pos > 0 && cur.node == route[cur.pos - 1])
			return loadAfterServed[cur.pos - 1];
		return loadAfterServed[cur.pos];
	};

	auto energyCost = [&](int u, int v, double load) -> double {
		double d = params.timeCost[u][v];
		double rate = consumption;
		if (vehicleCapacity > 0.0)
			rate += load / vehicleCapacity;
		return d * rate;
	};
	struct StateHash
	{
		std::size_t operator()(const State &s) const
		{
			long long socKey = std::llround(s.soc * 1000000.0);
			return (std::hash<int>()(s.pos) * 1315423911u) ^ (std::hash<int>()(s.node) << 1) ^ (std::hash<long long>()(socKey) << 3);
		}
	};

	auto normalizeSoc = [&](int node, double soc) -> double {
		return (node == 0 || isChargerNode(node, params.stationIndices)) ? Bmax : soc;
	};

	State start{0, 0, Bmax};
	std::unordered_map<State, double, StateHash> dist;
	std::unordered_map<State, State, StateHash> parent;
	std::unordered_map<State, int, StateHash> parentNode;

	using QItem = std::pair<double, State>;
	auto cmp = [](const QItem &a, const QItem &b) { return a.first > b.first; };
	std::priority_queue<QItem, std::vector<QItem>, decltype(cmp)> pq(cmp);

	dist[start] = 0.0;
	pq.push({0.0, start});

	State goal{m, 0, 0.0};
	bool found = false;

	while (!pq.empty())
	{
		auto [dcur, cur] = pq.top();
		pq.pop();
		if (dcur != dist[cur]) continue;
		if (cur.pos == m && cur.node == 0)
		{
			goal = cur;
			found = true;
			break;
		}

		double soc = normalizeSoc(cur.node, cur.soc);
		double load = loadAtNode(cur);
		int nextCustomer = (cur.pos < m) ? route[cur.pos] : -1;

		// Transition to next customer if any
		if (cur.pos < m)
		{
			double e = energyCost(cur.node, nextCustomer, load);
			if (e <= soc)
			{
				State nxt{cur.pos + 1, nextCustomer, soc - e};
				nxt.soc = normalizeSoc(nxt.node, nxt.soc);
				double nd = dcur + params.timeCost[cur.node][nextCustomer];
				if (!dist.count(nxt) || nd < dist[nxt])
				{
					dist[nxt] = nd;
					parent[nxt] = cur;
					parentNode[nxt] = nextCustomer;
					pq.push({nd, nxt});
				}
			}
		}

		// Transition to depot when all customers served
		if (cur.pos == m && cur.node != 0)
		{
			double e = energyCost(cur.node, 0, load);
			if (e <= soc)
			{
				State nxt{m, 0, soc - e};
				nxt.soc = normalizeSoc(nxt.node, nxt.soc);
				double nd = dcur + params.timeCost[cur.node][0];
				if (!dist.count(nxt) || nd < dist[nxt])
				{
					dist[nxt] = nd;
					parent[nxt] = cur;
					parentNode[nxt] = 0;
					pq.push({nd, nxt});
				}
			}
		}

		// Transitions to chargers
		for (int c : params.stationIndices)
		{
			if (c == cur.node) continue;
			double e = energyCost(cur.node, c, load);
			if (e > soc) continue;
			State nxt{cur.pos, c, Bmax};
			double nd = dcur + params.timeCost[cur.node][c];
			if (!dist.count(nxt) || nd < dist[nxt])
			{
				dist[nxt] = nd;
				parent[nxt] = cur;
				parentNode[nxt] = c;
				pq.push({nd, nxt});
			}
		}
	}

	if (!found)
	{
		result.feasible = false;
		return result;
	}

	result.distance = dist[goal];
	// Reconstruct path nodes (excluding starting depot and ending depot)
	std::vector<int> rev;
	State cur = goal;
	while (!(cur.pos == start.pos && cur.node == start.node && cur.soc == start.soc))
	{
		int nodeVisited = parentNode[cur];
		if (nodeVisited != 0)
			rev.push_back(nodeVisited);
		cur = parent[cur];
	}
	result.routeWithChargers.assign(rev.rbegin(), rev.rend());
	return result;
}

bool FRVCP::shortestFeasiblePath(
	const Params &params,
	int fromNode,
	int toNode,
	std::vector<int> &path,
	double &distance)
{
	const double Bmax = params.energyCapacity;
	const double consumption = params.energyConsumption;
	const double vehicleCapacity = params.vehicleCapacity;
	const double fullLoadRate = (vehicleCapacity > 0.0) ? (consumption + 1.0) : consumption;

	// Build node list: from, chargers, to (unique)
	std::vector<int> nodes;
	nodes.reserve(params.stationIndices.size() + 2);
	nodes.push_back(fromNode);
	for (int s : params.stationIndices)
	{
		if (s != fromNode && s != toNode)
			nodes.push_back(s);
	}
	if (toNode != fromNode)
		nodes.push_back(toNode);

	const int n = (int)nodes.size();
	const double INF = std::numeric_limits<double>::infinity();
	std::vector<double> dist(n, INF);
	std::vector<int> prev(n, -1);
	std::vector<char> visited(n, 0);

	// Dijkstra
	dist[0] = 0.0;
	for (int iter = 0; iter < n; ++iter)
	{
		int u = -1;
		double best = INF;
		for (int i = 0; i < n; ++i)
		{
			if (!visited[i] && dist[i] < best)
			{
				best = dist[i];
				u = i;
			}
		}
		if (u == -1) break;
		visited[u] = 1;
		if (nodes[u] == toNode) break;

		for (int v = 0; v < n; ++v)
		{
			if (u == v) continue;
			double d = params.timeCost[nodes[u]][nodes[v]];
			double energy = d * fullLoadRate;
			if (energy > Bmax + 1e-9) continue;
			if (dist[u] + d < dist[v])
			{
				dist[v] = dist[u] + d;
				prev[v] = u;
			}
		}
	}

	// Find target index
	int targetIdx = -1;
	for (int i = 0; i < n; ++i)
		if (nodes[i] == toNode) { targetIdx = i; break; }
	if (targetIdx == -1 || dist[targetIdx] == INF)
		return false;

	// Reconstruct path
	std::vector<int> rev;
	for (int cur = targetIdx; cur != -1; cur = prev[cur])
		rev.push_back(nodes[cur]);
	path.assign(rev.rbegin(), rev.rend());
	distance = dist[targetIdx];
	return true;
}
