import unittest

from emergency_routing import astar


class RoutingTests(unittest.TestCase):

    def test_shortest_route(self):
        graph = {
            "A": {"B": 4, "C": 2},
            "B": {"A": 4, "D": 5, "E": 10},
            "C": {"A": 2, "D": 3},
            "D": {"B": 5, "C": 3, "E": 2},
            "E": {"B": 10, "D": 2},
        }

        route, cost = astar(
            graph,
            "A",
            "E",
            lambda node, goal: 0,
        )

        self.assertEqual(route, ["A", "C", "D", "E"])
        self.assertEqual(cost, 7)

    def test_unreachable_destination(self):
        route, cost = astar(
            {"A": {}, "B": {}},
            "A",
            "B",
            lambda node, goal: 0,
        )

        self.assertIsNone(route)
        self.assertEqual(cost, float("inf"))


if __name__ == "__main__":
    unittest.main()