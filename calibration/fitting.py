"""
fitting.py
----------
The NumPy part of the project.  (CO4: NumPy arrays and operations)

Model of a sensor:      raw = offset + scale * reference   (+ noise)
So to correct a reading: corrected = (raw - offset) / scale

We compare two ways of estimating the correction:
  1. offset only    - assume scale = 1, just remove the average shift
  2. offset + scale - fit a straight line through the points
"""
import numpy as np


def fit_offset_only(raw, reference):
    """Average difference between sensor and reference. Scale is fixed at 1."""
    raw = np.asarray(raw, dtype=float)
    reference = np.asarray(reference, dtype=float)
    offset = float(np.mean(raw - reference))
    return offset, 1.0


def fit_offset_scale(raw, reference):
    """
    Least-squares straight line  raw = offset + scale * reference.

    We regress raw on reference (not the other way round) because the
    reference instrument is the more accurate one, so it plays the role of
    the "x" variable.
    """
    raw = np.asarray(raw, dtype=float)
    reference = np.asarray(reference, dtype=float)
    if len(raw) < 2:
        raise ValueError("need at least 2 points to fit a line")
    scale, offset = np.polyfit(reference, raw, 1)
    if abs(scale) < 1e-9:
        raise ValueError("fitted scale is ~0, cannot invert the correction")
    return float(offset), float(scale)


def apply_correction(raw, offset, scale):
    """Undo the sensor's offset and scale error."""
    raw = np.asarray(raw, dtype=float)
    return (raw - offset) / scale


# ---------- error measures (all take an array of errors = value - reference) ----------

def mae(errors):
    return float(np.mean(np.abs(errors)))


def rmse(errors):
    return float(np.sqrt(np.mean(np.square(errors))))


def max_abs(errors):
    return float(np.max(np.abs(errors)))


def split_indices(n, test_fraction=0.3, seed=0):
    """
    Randomly split n samples into (train_idx, test_idx).
    The seed makes it repeatable, and the two sets never overlap.
    """
    if n < 2:
        raise ValueError("need at least 2 samples to split")
    rng = np.random.default_rng(seed)
    order = rng.permutation(n)
    n_test = int(round(n * test_fraction))
    n_test = min(max(n_test, 1), n - 1)   # keep at least 1 in each set
    return order[n_test:], order[:n_test]
