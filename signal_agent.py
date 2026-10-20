PHASES = {
    "NS_GREEN": ["N", "S"],
    "EW_GREEN": ["E", "W"],
}


def choose_phase(
    queues,
    waiting_times,
    emergency_directions,
    current_phase,
    green_elapsed,
    min_green=10,
    max_green=35,
):
    # Continue the current phase until minimum green time is met.
    if green_elapsed < min_green:
        return current_phase

    # Give priority to a direction containing an emergency vehicle.
    emergency_phases = [
        phase
        for phase, directions in PHASES.items()
        if any(
            direction in emergency_directions
            for direction in directions
        )
    ]

    if emergency_phases:
        return emergency_phases[0]

    # Avoid allowing one phase to stay green indefinitely.
    if green_elapsed >= max_green:
        return (
            "EW_GREEN"
            if current_phase == "NS_GREEN"
            else "NS_GREEN"
        )

    scores = {}

    for phase, directions in PHASES.items():
        queue_score = sum(queues[d] for d in directions)
        wait_score = sum(waiting_times[d] for d in directions)

        scores[phase] = 5 * queue_score + 0.2 * wait_score

    return max(scores, key=scores.get)