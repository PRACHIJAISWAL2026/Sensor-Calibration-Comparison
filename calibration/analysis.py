"""
analysis.py
-----------
Pandas summaries and the held-out evaluation.  (CO5: Pandas, plus the BL4/BL5 work)

The big idea: a correction must be judged on data it has NOT seen.
If we fitted and tested on the same points the result would look better
than it really is.  So for every sensor we:
    1. pool all its runs,
    2. randomly keep 30% of the points aside (held-out),
    3. fit the correction on the other 70%,
    4. measure the error on the held-out 30%.
"""
import numpy as np
import pandas as pd

from .fitting import (apply_correction, fit_offset_only, fit_offset_scale,
                      mae, max_abs, rmse, split_indices)

METHOD_RAW = "raw (no correction)"
METHOD_OFFSET = "offset only"
METHOD_FULL = "offset + scale"
METHODS = [METHOD_RAW, METHOD_OFFSET, METHOD_FULL]


def pool_by_sensor(runs):
    """Return {sensor_id: (reference_array, raw_array)} using all runs of that sensor."""
    pooled = {}
    for run in runs:
        ref, raw = pooled.get(run.sensor_id, ([], []))
        ref = ref + run.reference
        raw = raw + run.raw
        pooled[run.sensor_id] = (ref, raw)
    return {sid: (np.array(r), np.array(w)) for sid, (r, w) in pooled.items()}


def evaluate_sensor(reference, raw, test_fraction=0.3, seed=7):
    """Fit on a training part, score on the held-out part. Returns a dict."""
    train, test = split_indices(len(reference), test_fraction, seed)
    ref_tr, raw_tr = reference[train], raw[train]
    ref_te, raw_te = reference[test], raw[test]

    off1, sc1 = fit_offset_only(raw_tr, ref_tr)
    off2, sc2 = fit_offset_scale(raw_tr, ref_tr)

    corrected = {
        METHOD_RAW: raw_te,
        METHOD_OFFSET: apply_correction(raw_te, off1, sc1),
        METHOD_FULL: apply_correction(raw_te, off2, sc2),
    }
    errors = {name: values - ref_te for name, values in corrected.items()}

    return {
        "n_train": int(len(train)),
        "n_test": int(len(test)),
        "params": {METHOD_OFFSET: (off1, sc1), METHOD_FULL: (off2, sc2)},
        "reference_test": ref_te,
        "raw_test": raw_te,
        "corrected": corrected,
        "errors": errors,
    }


def evaluate_all(runs, test_fraction=0.3, seed=7):
    """
    Run evaluate_sensor for every sensor.
    Returns (results_df, details) - a tidy DataFrame plus the raw arrays for plotting.
    """
    pooled = pool_by_sensor(runs)
    rows = []
    details = {}
    for sensor_id in sorted(pooled):
        ref, raw = pooled[sensor_id]
        detail = evaluate_sensor(ref, raw, test_fraction, seed)
        details[sensor_id] = detail
        for method in METHODS:
            err = detail["errors"][method]
            offset, scale = detail["params"].get(method, (0.0, 1.0))
            rows.append({
                "sensor_id": sensor_id,
                "method": method,
                "n_test": detail["n_test"],
                "offset": round(offset, 4),
                "scale": round(scale, 4),
                "MAE": round(mae(err), 4),
                "RMSE": round(rmse(err), 4),
                "max_abs_error": round(max_abs(err), 4),
            })
    return pd.DataFrame(rows), details


def repeated_split_check(reference, raw, n_splits=200, test_fraction=0.3):
    """
    One random split could be lucky.  So repeat the whole experiment with many
    different splits and count how often the fuller correction wins.
    """
    wins_vs_raw = 0
    wins_vs_offset = 0
    mae_full_list = []
    for s in range(n_splits):
        d = evaluate_sensor(reference, raw, test_fraction, seed=1000 + s)
        e = d["errors"]
        m_raw, m_off, m_full = mae(e[METHOD_RAW]), mae(e[METHOD_OFFSET]), mae(e[METHOD_FULL])
        wins_vs_raw += m_full < m_raw
        wins_vs_offset += m_full < m_off
        mae_full_list.append(m_full)
    return {
        "n_splits": n_splits,
        "full_beats_raw": wins_vs_raw / n_splits,
        "full_beats_offset_only": wins_vs_offset / n_splits,
        "mae_full_mean": float(np.mean(mae_full_list)),
        "mae_full_std": float(np.std(mae_full_list, ddof=1)),
    }


def runs_to_dataframe(runs):
    """One big table: every valid pair with its run and sensor."""
    records = []
    for run in runs:
        for ref, raw in run:
            records.append({"run_id": run.run_id, "sensor_id": run.sensor_id,
                            "reference": ref, "raw": raw})
    return pd.DataFrame(records)


def per_run_fits(runs):
    """Fit every run on its own - this shows how repeatable the sensor is trial to trial."""
    rows = []
    for run in runs:
        off, sc = fit_offset_scale(run.raw_array(), run.reference_array())
        rows.append({
            "run_id": run.run_id,
            "sensor_id": run.sensor_id,
            "n_samples": len(run),
            "offset": off,
            "scale": sc,
            "raw_MAE": mae(run.raw_error()),
        })
    return pd.DataFrame(rows)


def sensor_fit_summary(per_run_df):
    """Mean and spread of offset/scale across the repeated trials of each sensor."""
    summary = per_run_df.groupby("sensor_id").agg(
        runs=("run_id", "count"),
        offset_mean=("offset", "mean"),
        offset_std=("offset", "std"),
        scale_mean=("scale", "mean"),
        scale_std=("scale", "std"),
        raw_MAE_mean=("raw_MAE", "mean"),
    )
    return summary.round(4).reset_index()


def write_interpretation(results_df, stability):
    """Plain-English summary so the program explains its own numbers."""
    lines = []
    for sensor_id in sorted(results_df["sensor_id"].unique()):
        part = results_df[results_df["sensor_id"] == sensor_id].set_index("method")
        raw_m = part.loc[METHOD_RAW, "MAE"]
        off_m = part.loc[METHOD_OFFSET, "MAE"]
        full_m = part.loc[METHOD_FULL, "MAE"]
        gain = 100 * (raw_m - full_m) / raw_m
        extra = 100 * (off_m - full_m) / off_m
        win = stability[sensor_id]["full_beats_offset_only"] * 100
        lines.append(
            f"{sensor_id}: held-out MAE went from {raw_m:.2f} (raw) to {off_m:.2f} "
            f"(offset only) to {full_m:.2f} (offset + scale) deg C. "
            f"That is {gain:.0f}% better than raw; scale correction adds {extra:.0f}% "
            f"on top of offset-only and wins in {win:.0f}% of 200 random splits."
        )
    lines.append("")
    lines.append("Caution: the data are SIMULATED, so these numbers show that the "
                 "pipeline works, not how a real sensor behaves. A straight-line model "
                 "also cannot remove curvature in a sensor's response.")
    return "\n".join(lines)
