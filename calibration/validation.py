"""
validation.py
-------------
Functions that check one row of the CSV at a time.  (CO1: functions + control flow)

A "pair" is one reference value (the true value from a trusted instrument)
together with the raw value our cheap sensor reported for it.  If either half
of the pair is broken we throw the whole pair away and remember why, so we can
report it later instead of silently losing data.
"""
import math

# Plausible limits for the temperature sensors we are simulating (deg C).
# A reading of -999 or 480 is a sensor glitch, not a real temperature.
SENSOR_MIN = -40.0
SENSOR_MAX = 150.0

REQUIRED_COLUMNS = ["run_id", "sensor_id", "sample_id", "reference", "raw"]


def to_float(value):
    """Try to turn `value` into a normal finite number. Return None if we can't."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def check_pair(reference, raw):
    """
    Check one (reference, raw) pair.

    Returns (True, "ok") or (False, "<reason it was rejected>").
    """
    ref = to_float(reference)
    reading = to_float(raw)

    if ref is None:
        return False, "reference missing or not a number"
    if reading is None:
        return False, "raw reading missing or not a number"
    if not (SENSOR_MIN <= ref <= SENSOR_MAX):
        return False, "reference outside allowed range"
    if not (SENSOR_MIN <= reading <= SENSOR_MAX):
        return False, "raw reading outside allowed range"
    return True, "ok"


def validate_rows(rows):
    """
    Go through every row (a dict from csv.DictReader).

    Returns two lists:
      good     - cleaned rows with reference/raw converted to float
      rejected - one dict per bad row with the line number and the reason
    """
    good = []
    rejected = []

    # line 1 of the file is the header, so the first data row is line 2
    for line_number, row in enumerate(rows, start=2):
        run_id = (row.get("run_id") or "").strip()
        sensor_id = (row.get("sensor_id") or "").strip()

        if run_id == "" or sensor_id == "":
            rejected.append({
                "line": line_number,
                "run_id": run_id,
                "reference": row.get("reference"),
                "raw": row.get("raw"),
                "reason": "run_id or sensor_id is empty",
            })
            continue

        ok, reason = check_pair(row.get("reference"), row.get("raw"))
        if not ok:
            rejected.append({
                "line": line_number,
                "run_id": run_id,
                "reference": row.get("reference"),
                "raw": row.get("raw"),
                "reason": reason,
            })
            continue

        good.append({
            "run_id": run_id,
            "sensor_id": sensor_id,
            "sample_id": row.get("sample_id"),
            "reference": to_float(row["reference"]),
            "raw": to_float(row["raw"]),
        })

    return good, rejected
