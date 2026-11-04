
import heapq
from itertools import count


# =====================================================
# SMARTFLOW AI - MULTI JUNCTION NETWORK
# A* Emergency Routing + Signal Priority
# =====================================================

JUNCTIONS = {
    "A": (100, 400),
    "B": (300, 150),
    "C": (300, 450),
    "D": (520, 300),
    "E": (700, 150),
}

ROAD_NETWORK = {
    "A": {"B": 4, "C": 2},
    "B": {"A": 4, "D": 5, "E": 10},
    "C": {"A": 2, "D": 3},
    "D": {"B": 5, "C": 3, "E": 2},
    "E": {"B": 10, "D": 2},
}

DIRECTIONS = ("N", "S", "E", "W")


def heuristic(node, goal):
    # Zero heuristic: safe Dijkstra-style A* search.
    # Road costs are measured in seconds.
    return 0


def astar(graph, start, goal, heuristic):
    if start not in graph or goal not in graph:
        raise ValueError("Invalid start or goal junction")

    sequence = count()

    frontier = [
        (heuristic(start, goal), next(sequence), start)
    ]

    came_from = {}
    cost_so_far = {start: 0}

    while frontier:
        _, _, current = heapq.heappop(frontier)

        if current == goal:
            route = [current]

            while current in came_from:
                current = came_from[current]
                route.append(current)

            route.reverse()
            return route, cost_so_far[goal]

        for neighbour, road_cost in graph[current].items():

            if road_cost < 0:
                raise ValueError(
                    "Road costs must be non-negative"
                )

            new_cost = cost_so_far[current] + road_cost

            if (
                neighbour not in cost_so_far
                or new_cost < cost_so_far[neighbour]
            ):
                cost_so_far[neighbour] = new_cost
                came_from[neighbour] = current

                priority = (
                    new_cost + heuristic(neighbour, goal)
                )

                heapq.heappush(
                    frontier,
                    (priority, next(sequence), neighbour)
                )

    return None, float("inf")


def get_approach_direction(previous, current):
    """Find the direction from which the ambulance enters."""

    x1, y1 = JUNCTIONS[previous]
    x2, y2 = JUNCTIONS[current]

    dx = x2 - x1
    dy = y2 - y1

    if abs(dx) >= abs(dy):
        return "W" if dx > 0 else "E"

    return "N" if dy > 0 else "S"


def direction_to_phase(direction):
    if direction in ("N", "S"):
        return "NS_GREEN"

    return "EW_GREEN"


class MultiJunctionController:

    def __init__(self):
        self.graph = ROAD_NETWORK

        self.signals = {
            junction: {
                "phase": "NS_GREEN",
                "emergency_priority": False,
                "priority_direction": None,
            }
            for junction in self.graph
        }

        self.emergency_route = []
        self.route_cost = 0
        self.current_index = 0

    def plan_emergency_route(self, start, goal):

        route, cost = astar(
            self.graph,
            start,
            goal,
            heuristic
        )

        if route is None:
            raise ValueError("No emergency route found")

        self.emergency_route = route
        self.route_cost = cost
        self.current_index = 0

        return route, cost

    def get_next_signal_request(self):

        if len(self.emergency_route) < 2:
            return None

        if self.current_index >= len(self.emergency_route) - 1:
            return None

        previous = self.emergency_route[self.current_index]
        current = self.emergency_route[self.current_index + 1]

        direction = get_approach_direction(
            previous,
            current
        )

        required_phase = direction_to_phase(direction)

        self.signals[current]["phase"] = required_phase
        self.signals[current]["emergency_priority"] = True
        self.signals[current]["priority_direction"] = direction

        return {
            "junction": current,
            "direction": direction,
            "phase": required_phase,
        }

    def ambulance_reached_junction(self):

        if self.current_index < len(self.emergency_route) - 1:

            previous_junction = self.emergency_route[
                self.current_index + 1
            ]

            self.signals[previous_junction][
                "emergency_priority"
            ] = False

            self.signals[previous_junction][
                "priority_direction"
            ] = None

            self.current_index += 1

        return self.get_next_signal_request()

    def get_route_status(self):

        return {
            "route": self.emergency_route,
            "route_cost": self.route_cost,
            "current_index": self.current_index,
            "signals": self.signals,
        }


if __name__ == "__main__":

    controller = MultiJunctionController()

    route, cost = controller.plan_emergency_route(
        "A",
        "E"
    )

    print("\nSMARTFLOW AI - EMERGENCY ROUTING")
    print("--------------------------------")

    print("Selected A* route:", " -> ".join(route))
    print("Estimated route cost:", cost, "seconds")

    print("\nEmergency signal requests:")

    request = controller.get_next_signal_request()

    while request:

        print(
            "Junction:", request["junction"],
            "| Direction:", request["direction"],
            "| Required signal:", request["phase"]
        )

        request = controller.ambulance_reached_junction()

    print("\nEmergency route planning completed.")
