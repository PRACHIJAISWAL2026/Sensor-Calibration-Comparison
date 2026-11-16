"""
run.py
------
The CalibrationRun class.  (CO3: classes + special methods)

One "run" = one trial where we compared a single sensor against the reference
instrument at several points (e.g. 25 temperatures from 0 to 100 deg C).
"""
import numpy as np


class CalibrationRun:
    """
    Holds the paired readings of one calibration trial.

    Why these special methods?
      __init__     - checks the data the moment the object is created, so a
                     broken run (different lengths, empty) can never exist.
      __len__      - len(run) gives the number of paired samples, which is
                     exactly what we need for "does this run have enough points?"
      __getitem__  - run[3] returns the 4th (reference, raw) pair, and slicing
                     like run[:5] works too.
      __iter__     - lets us write `for ref, raw in run:` instead of juggling
                     two lists with indexes.
      __repr__     - prints something readable when debugging.
    """

    def __init__(self, run_id, sensor_id, reference, raw):
        if len(reference) != len(raw):
            raise ValueError("reference and raw must have the same length")
        if len(reference) == 0:
            raise ValueError("a run needs at least one pair")
        self.run_id = run_id
        self.sensor_id = sensor_id
        self.reference = [float(x) for x in reference]
        self.raw = [float(x) for x in raw]

    def __len__(self):
        return len(self.raw)

    def __getitem__(self, index):
        pairs = list(zip(self.reference, self.raw))
        return pairs[index]

    def __iter__(self):
        for pair in zip(self.reference, self.raw):
            yield pair

    def __repr__(self):
        return f"CalibrationRun(run_id={self.run_id!r}, sensor_id={self.sensor_id!r}, n={len(self)})"

    # ---- small helpers used by the NumPy parts of the project ----
    def reference_array(self):
        return np.array(self.reference)

    def raw_array(self):
        return np.array(self.raw)

    def raw_error(self):
        """Error of the uncorrected sensor: raw - reference (NumPy array)."""
        return self.raw_array() - self.reference_array()

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "sensor_id": self.sensor_id,
            "n_samples": len(self),
        }


def build_runs(good_rows, min_points=5):
    """
    Group the cleaned rows into CalibrationRun objects.

    A run with fewer than `min_points` valid pairs left is dropped, because a
    straight-line fit on 2 or 3 points tells us nothing.
    Returns (runs, dropped) where dropped is a list of (run_id, how_many_points).
    """
    grouped = {}
    for row in good_rows:
        key = (row["run_id"], row["sensor_id"])
        if key not in grouped:
            grouped[key] = {"reference": [], "raw": []}
        grouped[key]["reference"].append(row["reference"])
        grouped[key]["raw"].append(row["raw"])

    runs = []
    dropped = []
    for (run_id, sensor_id), data in grouped.items():
        if len(data["raw"]) < min_points:
            dropped.append((run_id, len(data["raw"])))
            continue
        runs.append(CalibrationRun(run_id, sensor_id, data["reference"], data["raw"]))
    return runs, dropped
