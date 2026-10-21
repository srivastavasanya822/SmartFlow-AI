from pathlib import Path

import pandas as pd

from metrics import calculate_metrics
from traffic_engine import run_simulation


SCENARIOS = {
    "Normal": 0.12,
    "Peak": 0.28,
}

MODES = ["Fixed", "AI"]


def run_experiments(duration=600, seeds=(42, 43, 44, 45, 46)):
    rows = []

    for scenario, arrival_rate in SCENARIOS.items():
        for seed in seeds:
            for mode in MODES:
                state = run_simulation(
                    mode=mode,
                    arrival_rate=arrival_rate,
                    seed=seed,
                    duration=duration,
                )

                row = calculate_metrics(state)
                row["scenario"] = scenario
                row["mode"] = mode
                row["seed"] = seed

                rows.append(row)

    return pd.DataFrame(rows)


def save_experiments(output_path="results/traffic_results.csv"):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    df = run_experiments()
    df.to_csv(output, index=False)

    print("\nExperiment results")
    print(
        df.groupby(["scenario", "mode"])[
            ["average_wait", "average_queue", "completed"]
        ].mean().round(2)
    )

    print(f"\nSaved results to: {output}")
    return df


if __name__ == "__main__":
    save_experiments()