"""End-to-end tests: generated data -> validation -> fit -> held-out evaluation."""
import csv
import os
import tempfile
import unittest

import generate_data
from calibration.analysis import (METHOD_FULL, METHOD_OFFSET, METHOD_RAW,
                                  evaluate_all)
from calibration.io_utils import load_rows
from calibration.run import build_runs
from calibration.validation import validate_rows
from main import run_pipeline


def make_clean_csv(path):
    rows = generate_data.make_rows()
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["run_id", "sensor_id", "sample_id", "reference", "raw"])
        writer.writeheader()
        writer.writerows(rows)


class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.csv_path = os.path.join(cls.tmp.name, "data.csv")
        make_clean_csv(cls.csv_path)
        rows = load_rows(cls.csv_path)
        cls.good, cls.rejected = validate_rows(rows)
        cls.runs, cls.dropped = build_runs(cls.good)
        cls.results, cls.details = evaluate_all(cls.runs, 0.3, 7)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_deliberately_broken_rows_are_caught(self):
        self.assertEqual(len(self.rejected), len(generate_data.BROKEN_ROWS))

    def test_no_bad_values_slip_through(self):
        for row in self.good:
            self.assertGreaterEqual(row["raw"], -40)
            self.assertLessEqual(row["raw"], 150)

    def test_twelve_runs_survive(self):
        self.assertEqual(len(self.runs), 12)
        self.assertEqual(self.dropped, [])

    def test_correction_improves_heldout_error_for_every_sensor(self):
        for sid in ["S1", "S2", "S3"]:
            part = self.results[self.results.sensor_id == sid].set_index("method")
            self.assertLess(part.loc[METHOD_FULL, "MAE"], part.loc[METHOD_RAW, "MAE"],
                            msg=f"offset+scale should beat raw for {sid}")

    def test_scale_correction_beats_offset_only(self):
        for sid in ["S1", "S2", "S3"]:
            part = self.results[self.results.sensor_id == sid].set_index("method")
            self.assertLess(part.loc[METHOD_FULL, "MAE"], part.loc[METHOD_OFFSET, "MAE"])

    def test_fitted_values_close_to_injected_values(self):
        # S1 has no curvature, so the fit should be near the injected truth.
        off, sc = self.details["S1"]["params"][METHOD_FULL]
        self.assertAlmostEqual(off, generate_data.SENSORS["S1"]["offset"], delta=0.5)
        self.assertAlmostEqual(sc, generate_data.SENSORS["S1"]["scale"], delta=0.02)

    def test_run_pipeline_writes_outputs(self):
        out = os.path.join(self.tmp.name, "out")
        summary = run_pipeline(self.csv_path, out, 0.3, 7, verbose=False)
        for name in ["results.json", "heldout_results.csv", "analysis.txt",
                     "01_raw_vs_corrected_scatter.png", "02_error_histograms.png",
                     "03_mae_comparison.png", "rejected_rows.csv"]:
            self.assertTrue(os.path.exists(os.path.join(out, name)), msg=name)
        self.assertEqual(summary["rejected_rows"], len(generate_data.BROKEN_ROWS))

    def test_missing_column_is_reported(self):
        bad_path = os.path.join(self.tmp.name, "bad.csv")
        with open(bad_path, "w") as f:
            f.write("run_id,sensor_id,reference\nA,S1,10\n")
        with self.assertRaises(ValueError):
            load_rows(bad_path)


if __name__ == "__main__":
    unittest.main()
