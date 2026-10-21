import heapq
from itertools import count


def astar(graph, start, goal, heuristic):
    sequence = count()

    frontier = [
        (heuristic(start, goal), next(sequence), start)
    ]

    came_from = {}
    cost_so_far = {start: 0}

    while frontier:
        _, _, current = heapq.heappop(frontier)

        if current == goal:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            path.reverse()
            return path, cost_so_far[goal]

        for neighbour, road_cost in graph.get(current, {}).items():
            if road_cost < 0:
                raise ValueError("Road costs must be non-negative")

            new_cost = cost_so_far[current] + road_cost

            if (
                neighbour not in cost_so_far
                or new_cost < cost_so_far[neighbour]
            ):
                cost_so_far[neighbour] = new_cost
                came_from[neighbour] = current

                priority = new_cost + heuristic(neighbour, goal)

                heapq.heappush(
                    frontier,
                    (priority, next(sequence), neighbour)
                )

    return None, float("inf")


if __name__ == "__main__":
    road_network = {
        "A": {"B": 4, "C": 2},
        "B": {"A": 4, "D": 5, "E": 10},
        "C": {"A": 2, "D": 3},
        "D": {"B": 5, "C": 3, "E": 2},
        "E": {"B": 10, "D": 2},
    }

    # Zero heuristic provides a Dijkstra-style correctness check.
    def heuristic(node, goal):
        return 0

    route, cost = astar(
        road_network,
        "A",
        "E",
        heuristic
    )

    print("Selected route:", route)
    print("Estimated cost:", cost, "seconds")