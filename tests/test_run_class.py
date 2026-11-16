"""Tests for CalibrationRun and its special methods (CO3)."""
import unittest

from calibration.run import CalibrationRun, build_runs


class TestCalibrationRun(unittest.TestCase):
    def setUp(self):
        self.run = CalibrationRun("R1", "S1", [0, 10, 20], [1, 11, 21])

    def test_len(self):
        self.assertEqual(len(self.run), 3)

    def test_getitem_and_slice(self):
        self.assertEqual(self.run[1], (10.0, 11.0))
        self.assertEqual(self.run[:2], [(0.0, 1.0), (10.0, 11.0)])

    def test_iter(self):
        self.assertEqual(list(self.run), [(0.0, 1.0), (10.0, 11.0), (20.0, 21.0)])

    def test_repr_mentions_id(self):
        self.assertIn("R1", repr(self.run))

    def test_mismatched_lengths_rejected(self):
        with self.assertRaises(ValueError):
            CalibrationRun("R2", "S1", [1, 2, 3], [1, 2])

    def test_empty_run_rejected(self):
        with self.assertRaises(ValueError):
            CalibrationRun("R3", "S1", [], [])

    def test_raw_error(self):
        self.assertEqual(self.run.raw_error().tolist(), [1.0, 1.0, 1.0])


class TestBuildRuns(unittest.TestCase):
    def test_small_runs_are_dropped(self):
        rows = []
        for i in range(6):
            rows.append({"run_id": "BIG", "sensor_id": "S1", "reference": float(i), "raw": float(i)})
        for i in range(2):
            rows.append({"run_id": "TINY", "sensor_id": "S1", "reference": float(i), "raw": float(i)})
        runs, dropped = build_runs(rows, min_points=5)
        self.assertEqual([r.run_id for r in runs], ["BIG"])
        self.assertEqual(dropped, [("TINY", 2)])


if __name__ == "__main__":
    unittest.main()
