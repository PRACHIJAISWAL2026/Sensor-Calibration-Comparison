"""
generate_data.py
----------------
Creates the dataset used in this project:  data/sensor_runs.csv

*** IMPORTANT: THE DATA IS SIMULATED. ***
No real sensor was measured. We invent three temperature sensors with a known
offset, scale error and noise, so that we know the "right answer" and can check
that our calibration code finds it. Any report or presentation must say that
the readings are simulated.

How a fake reading is made:
    raw = offset + scale * reference + curvature*(reference-50)^2 + random noise

We also break a handful of rows ON PURPOSE (missing values, "N/A", -999 sensor
glitches, ...) so the validation code has something to catch.

Run:  python generate_data.py
"""
import csv
import os
import random

SEED = 42
RUNS_PER_SENSOR = 4
POINTS_PER_RUN = 25          # reference temperatures from 0 to 100 deg C

# "True" behaviour of each simulated sensor.
SENSORS = {
    "S1": {"offset": 2.0,  "scale": 0.97, "noise": 0.6, "curve": 0.0},
    "S2": {"offset": -1.5, "scale": 1.03, "noise": 0.8, "curve": 0.0},
    # S3 is noisier AND slightly curved, so a straight-line fix can't fully cure it.
    "S3": {"offset": 0.5,  "scale": 0.95, "noise": 1.2, "curve": 0.0008},
}

# Rows we damage on purpose: (run_id, sample_id) -> (column, bad value)
BROKEN_ROWS = {
    ("S1_R1", 7):  ("raw", ""),            # missing raw reading
    ("S1_R2", 12): ("raw", "N/A"),         # text instead of a number
    ("S1_R4", 9):  ("reference", "abc"),   # garbage reference
    ("S2_R1", 3):  ("raw", "-999"),        # classic sensor error code
    ("S2_R3", 20): ("reference", ""),      # missing reference
    ("S3_R2", 5):  ("raw", "480"),         # impossible temperature
    ("S3_R4", 15): ("raw", "nan"),         # not-a-number
}

OUTPUT_PATH = os.path.join("data", "sensor_runs.csv")


def make_rows():
    rng = random.Random(SEED)
    rows = []
    for sensor_id, p in SENSORS.items():
        for r in range(1, RUNS_PER_SENSOR + 1):
            run_id = f"{sensor_id}_R{r}"
            for i in range(1, POINTS_PER_RUN + 1):
                reference = round((i - 1) * 100 / (POINTS_PER_RUN - 1), 1)
                raw = (p["offset"] + p["scale"] * reference
                       + p["curve"] * (reference - 50) ** 2
                       + rng.gauss(0, p["noise"]))
                row = {"run_id": run_id, "sensor_id": sensor_id, "sample_id": i,
                       "reference": reference, "raw": round(raw, 2)}
                if (run_id, i) in BROKEN_ROWS:
                    column, bad_value = BROKEN_ROWS[(run_id, i)]
                    row[column] = bad_value
                rows.append(row)
    return rows


def main():
    rows = make_rows()
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["run_id", "sensor_id", "sample_id", "reference", "raw"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH} ({len(BROKEN_ROWS)} deliberately broken).")
    print("Reminder: this data is SIMULATED.")


if __name__ == "__main__":
    main()
