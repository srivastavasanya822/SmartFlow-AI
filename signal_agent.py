
"""
SmartFlow AI - Intelligent Signal Agent

Features:
1. Rule-based signal control
2. Search over possible signal configurations
3. Utility based on queue length and waiting time
4. Emergency vehicle priority
"""

from itertools import product

PHASES = ("NS_GREEN", "EW_GREEN")


def calculate_utility(phase, queues, waiting_times):
    """Lower cost means better traffic flow."""

    if phase == "NS_GREEN":
        active = ("N", "S")
        inactive = ("E", "W")
    else:
        active = ("E", "W")
        inactive = ("N", "S")

    active_queue = sum(queues.get(d, 0) for d in active)
    inactive_queue = sum(queues.get(d, 0) for d in inactive)

    active_wait = sum(waiting_times.get(d, 0) for d in active)
    inactive_wait = sum(waiting_times.get(d, 0) for d in inactive)

    cost = (
        2.0 * inactive_queue
        + 0.08 * inactive_wait
        - 0.25 * active_queue
        - 0.04 * active_wait
    )

    return cost


def rule_based_decision(
    queues,
    waiting_times,
    emergency_directions,
    current_phase,
    green_elapsed,
    min_green,
    max_green,
):
    """Apply minimum-green, emergency and maximum-green rules."""

    emergency_directions = set(emergency_directions)

    # Rule 1: Respect minimum green time first.
    if green_elapsed < min_green:
        return current_phase

    # Rule 2: Give emergency vehicles priority after minimum green.
    if emergency_directions:
        if emergency_directions.intersection(("N", "S")):
            return "NS_GREEN"
        return "EW_GREEN"

    # Rule 3: Force a change after maximum green time.
    if green_elapsed >= max_green:
        return (
            "EW_GREEN"
            if current_phase == "NS_GREEN"
            else "NS_GREEN"
        )

    # Rule 4: Compare traffic queues and waiting times.
    ns_wait = sum(
        waiting_times.get(d, 0) for d in ("N", "S")
    )
    ew_wait = sum(
        waiting_times.get(d, 0) for d in ("E", "W")
    )

    ns_queue = sum(
        queues.get(d, 0) for d in ("N", "S")
    )
    ew_queue = sum(
        queues.get(d, 0) for d in ("E", "W")
    )

    ns_score = 2 * ns_queue + 0.08 * ns_wait
    ew_score = 2 * ew_queue + 0.08 * ew_wait

    return "NS_GREEN" if ns_score >= ew_score else "EW_GREEN"


def search_best_phase(queues, waiting_times, current_phase):
    """Search possible two-step signal configurations."""

    best_first_phase = current_phase
    best_cost = float("inf")

    for sequence in product(PHASES, repeat=2):
        first_phase, second_phase = sequence

        first_cost = calculate_utility(
            first_phase, queues, waiting_times
        )

        second_cost = calculate_utility(
            second_phase, queues, waiting_times
        )

        total_cost = first_cost + 0.5 * second_cost

        if total_cost < best_cost:
            best_cost = total_cost
            best_first_phase = first_phase

    return best_first_phase


def choose_phase(
    queues,
    waiting_times,
    emergency_directions,
    current_phase,
    green_elapsed,
    min_green=10,
    max_green=35,
):
    """Main intelligent signal agent."""

    rule_decision = rule_based_decision(
        queues,
        waiting_times,
        emergency_directions,
        current_phase,
        green_elapsed,
        min_green,
        max_green,
    )

    # Never override minimum green time.
    if green_elapsed < min_green:
        return current_phase

    # Emergency priority takes precedence after minimum green.
    if emergency_directions:
        return rule_decision

    # Maximum green rule.
    if green_elapsed >= max_green:
        return rule_decision

    # Search for the best next signal configuration.
    return search_best_phase(
        queues,
        waiting_times,
        current_phase,
    )
