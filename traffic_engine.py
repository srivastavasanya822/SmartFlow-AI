import numpy as np

from signal_agent import choose_phase

DIRECTIONS = ["N", "S", "E", "W"]

MIN_GREEN = 10
MAX_GREEN = 35
YELLOW_TIME = 3
ALL_RED_TIME = 1
CAR_SPEED = 0.012
CAR_GAP = 0.055

STOP_POINTS = {
    "N": 0.29,
    "S": 0.29,
    "E": 0.355,
    "W": 0.355,
}


def create_simulation(mode="AI", arrival_rate=0.12, seed=42):
    if mode not in ("AI", "Fixed"):
        raise ValueError("mode must be 'AI' or 'Fixed'")

    if not 0 <= arrival_rate <= 1:
        raise ValueError("arrival_rate must be between 0 and 1")

    return {
        "mode": mode,
        "arrival_rate": arrival_rate,
        "rng": np.random.default_rng(seed),
        "time": 0,
        "phase": "NS_GREEN",
        "pending_phase": None,
        "transition_remaining": 0,
        "green_elapsed": 0,
        "vehicles": [],
        "next_id": 1,
        "arrivals": 0,
        "emergency_arrivals": 0,
        "completed": 0,
        "wait_samples": [],
        "emergency_wait_samples": [],
        "queue_history": [],
    }


def is_green_for(direction, phase):
    if direction in ("N", "S"):
        return phase == "NS_GREEN"
    return phase == "EW_GREEN"


def get_queue_counts(state):
    queues = {direction: 0 for direction in DIRECTIONS}

    for vehicle in state["vehicles"]:
        direction = vehicle["direction"]
        stop = STOP_POINTS[direction]

        if (
            vehicle["progress"] >= stop - 0.06
            and vehicle["progress"] <= stop + 0.005
        ):
            if not is_green_for(direction, state["phase"]):
                queues[direction] += 1

    return queues


def get_waiting_times(state):
    waiting = {direction: 0.0 for direction in DIRECTIONS}

    for vehicle in state["vehicles"]:
        direction = vehicle["direction"]
        stop = STOP_POINTS[direction]

        is_near_stop = (
            vehicle["progress"] >= stop - 0.06
            and vehicle["progress"] <= stop + 0.005
        )

        if is_near_stop and not is_green_for(
            direction, state["phase"]
        ):
            waiting[direction] += vehicle["wait"]

    return waiting


def get_emergency_directions(state):
    result = set()

    for vehicle in state["vehicles"]:
        if vehicle["is_emergency"]:
            result.add(vehicle["direction"])

    return result


def add_arrivals(state):
    rng = state["rng"]

    for direction in DIRECTIONS:
        if rng.random() < state["arrival_rate"]:
            emergency = rng.random() < 0.05

            vehicle = {
                "id": state["next_id"],
                "direction": direction,
                "progress": 0.0,
                "wait": 0,
                "is_emergency": emergency,
            }

            state["vehicles"].append(vehicle)
            state["next_id"] += 1
            state["arrivals"] += 1

            if emergency:
             state["emergency_arrivals"] += 1


def desired_phase(state):
    if state["mode"] == "Fixed":
        return (
            "NS_GREEN"
            if (state["time"] // 30) % 2 == 0
            else "EW_GREEN"
        )

    queues = get_queue_counts(state)
    waiting = get_waiting_times(state)
    emergencies = get_emergency_directions(state)

    return choose_phase(
        queues=queues,
        waiting_times=waiting,
        emergency_directions=emergencies,
        current_phase=state["phase"],
        green_elapsed=state["green_elapsed"],
        min_green=MIN_GREEN,
        max_green=MAX_GREEN,
    )


def advance_signal(state):
    phase = state["phase"]

    if phase.endswith("_YELLOW"):
        state["transition_remaining"] -= 1

        if state["transition_remaining"] <= 0:
            state["phase"] = "ALL_RED"
            state["transition_remaining"] = ALL_RED_TIME

        return

    if phase == "ALL_RED":
        state["transition_remaining"] -= 1

        if state["transition_remaining"] <= 0:
            state["phase"] = state["pending_phase"]
            state["pending_phase"] = None
            state["green_elapsed"] = 0

        return

    target = desired_phase(state)

    if target != phase and state["green_elapsed"] >= MIN_GREEN:
        state["pending_phase"] = target
        state["phase"] = (
            "NS_YELLOW" if phase == "NS_GREEN" else "EW_YELLOW"
        )
        state["transition_remaining"] = YELLOW_TIME
        return

    state["green_elapsed"] += 1


def advance_vehicles(state):
    vehicles = state["vehicles"]

    # Each vehicle moves along its entry-to-exit path.
    for vehicle in sorted(
        vehicles, key=lambda item: item["progress"], reverse=True
    ):
        direction = vehicle["direction"]
        progress = vehicle["progress"]
        stop = STOP_POINTS[direction]

        proposed = min(1.0, progress + CAR_SPEED)

        # Vehicles must stop before a red/yellow/all-red approach.
        if (
            progress < stop
            and proposed >= stop
            and not is_green_for(direction, state["phase"])
        ):
            proposed = stop - 0.005

        # Maintain space between vehicles travelling in the same direction.
        blocked = any(
            other["direction"] == direction
            and other["id"] != vehicle["id"]
            and other["progress"] > progress
            and other["progress"] - progress < CAR_GAP
            for other in vehicles
        )

        if blocked:
            vehicle["wait"] += 1
            continue

        if proposed == progress:
            vehicle["wait"] += 1
            continue

        vehicle["progress"] = proposed

    remaining = []

    for vehicle in vehicles:
        if vehicle["progress"] >= 1.0:
            state["completed"] += 1
            state["wait_samples"].append(vehicle["wait"])

            if vehicle["is_emergency"]:
                state["emergency_wait_samples"].append(
                    vehicle["wait"]
                )
        else:
            remaining.append(vehicle)

    state["vehicles"] = remaining


def step_simulation(state):
    state["time"] += 1

    add_arrivals(state)
    advance_signal(state)
    advance_vehicles(state)

    queues = get_queue_counts(state)
    state["queue_history"].append(sum(queues.values()))

    return state


def run_simulation(mode="AI", arrival_rate=0.12, seed=42, duration=600):
    state = create_simulation(mode, arrival_rate, seed)

    for _ in range(duration):
        step_simulation(state)

    return state