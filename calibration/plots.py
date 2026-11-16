"""
plots.py
--------
All the Matplotlib figures.  (CO6: visualisation)

Every plot has a title, axis labels with units, and a legend, and is saved as a PNG.
"""
import os

import matplotlib
matplotlib.use("Agg")   # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np

from .analysis import METHOD_FULL, METHOD_OFFSET, METHOD_RAW, METHODS

RAW_COLOR = "#c0392b"
OFFSET_COLOR = "#e69f00"
FULL_COLOR = "#1f5fa8"


def _save(fig, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_raw_vs_corrected(details, out_dir):
    """Held-out points: sensor reading vs true reference, before and after correction."""
    sensors = sorted(details)
    fig, axes = plt.subplots(1, len(sensors), figsize=(4.6 * len(sensors), 4.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, sid in zip(axes, sensors):
        d = details[sid]
        ref = d["reference_test"]
        lo, hi = ref.min() - 3, ref.max() + 3
        ax.plot([lo, hi], [lo, hi], color="gray", linestyle="--", label="perfect sensor (y = x)")
        ax.scatter(ref, d["raw_test"], marker="x", color=RAW_COLOR, label="raw reading")
        ax.scatter(ref, d["corrected"][METHOD_FULL], marker="o", s=22,
                   color=FULL_COLOR, label="corrected (offset + scale)")
        ax.set_title(f"Sensor {sid} (held-out samples)")
        ax.set_xlabel("Reference temperature (deg C)")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Sensor value (deg C)")
    axes[0].legend(fontsize=8, loc="upper left")
    return _save(fig, out_dir, "01_raw_vs_corrected_scatter.png")


def plot_error_histograms(details, out_dir):
    """Distribution of held-out errors, raw vs corrected."""
    sensors = sorted(details)
    fig, axes = plt.subplots(1, len(sensors), figsize=(4.6 * len(sensors), 4.2), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, sid in zip(axes, sensors):
        errs = details[sid]["errors"]
        all_vals = np.concatenate([errs[METHOD_RAW], errs[METHOD_FULL]])
        bins = np.linspace(all_vals.min() - 0.2, all_vals.max() + 0.2, 16)
        ax.hist(errs[METHOD_RAW], bins=bins, alpha=0.6, color=RAW_COLOR, label="raw")
        ax.hist(errs[METHOD_FULL], bins=bins, alpha=0.6, color=FULL_COLOR, label="corrected")
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_title(f"Sensor {sid}: error distribution")
        ax.set_xlabel("Error = value - reference (deg C)")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Number of held-out samples")
    axes[0].legend(fontsize=8)
    return _save(fig, out_dir, "02_error_histograms.png")


def plot_mae_comparison(results_df, out_dir):
    """Grouped bar chart: MAE of the three methods for each sensor."""
    sensors = sorted(results_df["sensor_id"].unique())
    x = np.arange(len(sensors))
    width = 0.26
    colors = {METHOD_RAW: RAW_COLOR, METHOD_OFFSET: OFFSET_COLOR, METHOD_FULL: FULL_COLOR}

    fig, ax = plt.subplots(figsize=(7, 4.4))
    for i, method in enumerate(METHODS):
        vals = [results_df[(results_df.sensor_id == s) & (results_df.method == method)]["MAE"].iloc[0]
                for s in sensors]
        bars = ax.bar(x + (i - 1) * width, vals, width, label=method, color=colors[method])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.03, f"{v:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Sensor {s}" for s in sensors])
    ax.set_ylabel("Mean absolute error on held-out data (deg C)")
    ax.set_title("Which correction works best?")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, out_dir, "03_mae_comparison.png")


def plot_residuals(details, out_dir):
    """Error left over after correction, against the reference. Curvature shows up here."""
    sensors = sorted(details)
    fig, axes = plt.subplots(1, len(sensors), figsize=(4.6 * len(sensors), 4.0), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, sid in zip(axes, sensors):
        d = details[sid]
        ax.axhline(0, color="black", linewidth=0.8)
        ax.scatter(d["reference_test"], d["errors"][METHOD_FULL], color=FULL_COLOR, s=22)
        ax.set_title(f"Sensor {sid}: leftover error")
        ax.set_xlabel("Reference temperature (deg C)")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Error after correction (deg C)")
    return _save(fig, out_dir, "04_residuals_after_correction.png")


def make_all_plots(details, results_df, out_dir):
    return [
        plot_raw_vs_corrected(details, out_dir),
        plot_error_histograms(details, out_dir),
        plot_mae_comparison(results_df, out_dir),
        plot_residuals(details, out_dir),
    ]
