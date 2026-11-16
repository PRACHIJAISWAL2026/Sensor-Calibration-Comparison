"""
main.py
-------
Runs the whole pipeline from CSV to plots and a written analysis.

    python generate_data.py     (only needed once, creates data/sensor_runs.csv)
    python main.py

Useful options:
    python main.py --data my_file.csv --test-fraction 0.25 --seed 3
"""
import argparse
import os

from calibration.analysis import (evaluate_all, per_run_fits, pool_by_sensor,
                                  repeated_split_check, runs_to_dataframe,
                                  sensor_fit_summary, write_interpretation)
from calibration.io_utils import load_rows, save_json, save_rows
from calibration.plots import make_all_plots
from calibration.run import build_runs
from calibration.validation import validate_rows


def run_pipeline(data_path, out_dir="outputs", test_fraction=0.3, seed=7, verbose=True):
    # 1. read + validate
    rows = load_rows(data_path)
    good, rejected = validate_rows(rows)
    runs, dropped = build_runs(good)

    if not runs:
        raise SystemExit("No usable runs found - check your CSV.")

    # 2. fit corrections and test them on held-out data
    results_df, details = evaluate_all(runs, test_fraction, seed)
    per_run_df = per_run_fits(runs)
    fit_summary = sensor_fit_summary(per_run_df)

    pooled = pool_by_sensor(runs)
    stability = {sid: repeated_split_check(ref, raw, 200, test_fraction)
                 for sid, (ref, raw) in pooled.items()}

    # 3. save everything
    os.makedirs(out_dir, exist_ok=True)
    plot_paths = make_all_plots(details, results_df, out_dir)
    results_df.to_csv(os.path.join(out_dir, "heldout_results.csv"), index=False)
    fit_summary.to_csv(os.path.join(out_dir, "per_sensor_summary.csv"), index=False)
    per_run_df.to_csv(os.path.join(out_dir, "per_run_fits.csv"), index=False)
    if rejected:
        save_rows(os.path.join(out_dir, "rejected_rows.csv"), rejected,
                  ["line", "run_id", "reference", "raw", "reason"])

    text = write_interpretation(results_df, stability)
    with open(os.path.join(out_dir, "analysis.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")

    summary = {
        "input_rows": len(rows),
        "valid_rows": len(good),
        "rejected_rows": len(rejected),
        "rejection_reasons": {},
        "runs_used": len(runs),
        "runs_dropped": len(dropped),
        "test_fraction": test_fraction,
        "seed": seed,
        "heldout_results": results_df.to_dict(orient="records"),
        "per_sensor_summary": fit_summary.to_dict(orient="records"),
        "stability": stability,
        "rejected_detail": rejected,
    }
    for item in rejected:
        summary["rejection_reasons"][item["reason"]] = summary["rejection_reasons"].get(item["reason"], 0) + 1
    save_json(os.path.join(out_dir, "results.json"), summary)

    # 4. print a readable report
    if verbose:
        df = runs_to_dataframe(runs)
        print("=" * 60)
        print(" Sensor Calibration Comparison  (SIMULATED DATA)")
        print("=" * 60)
        print(f"Rows read: {len(rows)} | valid: {len(good)} | rejected: {len(rejected)}")
        for item in rejected:
            print(f"   line {item['line']:>3} ({item['run_id']}): {item['reason']}")
        print(f"Runs used: {len(runs)} | sensors: {df['sensor_id'].nunique()}")
        print("\nHeld-out results (test fraction = %.0f%%, seed = %d):" % (test_fraction * 100, seed))
        print(results_df.to_string(index=False))
        print("\nRepeatability across trials (offset/scale fitted per run):")
        print(fit_summary.to_string(index=False))
        print("\nAnalysis:")
        print(text)
        print("\nSaved plots and tables in:", os.path.abspath(out_dir))
    return summary


def parse_args():
    p = argparse.ArgumentParser(description="Sensor calibration comparison")
    p.add_argument("--data", default=os.path.join("data", "sensor_runs.csv"))
    p.add_argument("--out", default="outputs")
    p.add_argument("--test-fraction", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=7)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.data, args.out, args.test_fraction, args.seed)
