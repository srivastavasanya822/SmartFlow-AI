import numpy as np


def calculate_metrics(state):
    waits = state["wait_samples"]
    emergency_waits = state["emergency_wait_samples"]
    queue_history = state["queue_history"]

    return {
        "arrivals": state["arrivals"],
        "completed": state["completed"],
        "average_wait": (
            float(np.mean(waits)) if waits else 0.0
        ),
        "average_queue": (
            float(np.mean(queue_history)) if queue_history else 0.0
        ),
        "maximum_queue": (
            int(max(queue_history)) if queue_history else 0
        ),
        "emergency_arrivals": state["emergency_arrivals"],
        
        "emergency_average_wait": (
            float(np.mean(emergency_waits))
            if emergency_waits else 0.0
        ),
    }