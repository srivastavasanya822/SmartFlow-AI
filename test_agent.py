import unittest

from signal_agent import choose_phase


class SignalAgentTests(unittest.TestCase):

    def test_minimum_green_is_respected(self):
        phase = choose_phase(
            queues={"N": 0, "S": 0, "E": 10, "W": 10},
            waiting_times={"N": 0, "S": 0, "E": 100, "W": 100},
            emergency_directions={"E"},
            current_phase="NS_GREEN",
            green_elapsed=5,
            min_green=10,
            max_green=35,
        )

        self.assertEqual(phase, "NS_GREEN")

    def test_emergency_priority_after_minimum_green(self):
        phase = choose_phase(
            queues={"N": 0, "S": 0, "E": 2, "W": 0},
            waiting_times={"N": 0, "S": 0, "E": 10, "W": 0},
            emergency_directions={"E"},
            current_phase="NS_GREEN",
            green_elapsed=12,
            min_green=10,
            max_green=35,
        )

        self.assertEqual(phase, "EW_GREEN")


if __name__ == "__main__":
    unittest.main()