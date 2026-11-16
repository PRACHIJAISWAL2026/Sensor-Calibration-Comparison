"""Tests for the NumPy fitting code (CO4)."""
import unittest

import numpy as np

from calibration.fitting import (apply_correction, fit_offset_only,
                                 fit_offset_scale, mae, rmse, split_indices)


class TestFitting(unittest.TestCase):
    def test_recovers_exact_offset_and_scale(self):
        # With zero noise the fit must find the injected values almost exactly.
        ref = np.linspace(0, 100, 30)
        raw = 3.0 + 0.9 * ref
        offset, scale = fit_offset_scale(raw, ref)
        self.assertAlmostEqual(offset, 3.0, places=6)
        self.assertAlmostEqual(scale, 0.9, places=6)

    def test_recovers_values_with_small_noise(self):
        rng = np.random.default_rng(0)
        ref = np.linspace(0, 100, 200)
        raw = -2.0 + 1.05 * ref + rng.normal(0, 0.3, size=200)
        offset, scale = fit_offset_scale(raw, ref)
        self.assertAlmostEqual(offset, -2.0, delta=0.2)
        self.assertAlmostEqual(scale, 1.05, delta=0.01)

    def test_correction_undoes_the_model(self):
        ref = np.array([0.0, 50.0, 100.0])
        raw = 2.0 + 0.97 * ref
        fixed = apply_correction(raw, 2.0, 0.97)
        np.testing.assert_allclose(fixed, ref)

    def test_offset_only_keeps_scale_one(self):
        offset, scale = fit_offset_only([11, 21, 31], [10, 20, 30])
        self.assertAlmostEqual(offset, 1.0)
        self.assertEqual(scale, 1.0)

    def test_fit_needs_two_points(self):
        with self.assertRaises(ValueError):
            fit_offset_scale([1.0], [1.0])

    def test_flat_sensor_cannot_be_inverted(self):
        with self.assertRaises(ValueError):
            fit_offset_scale([5, 5, 5, 5], [0, 10, 20, 30])

    def test_error_measures(self):
        errors = np.array([1.0, -1.0, 2.0, -2.0])
        self.assertAlmostEqual(mae(errors), 1.5)
        self.assertAlmostEqual(rmse(errors), np.sqrt(2.5))


class TestSplit(unittest.TestCase):
    def test_no_overlap_and_full_coverage(self):
        train, test = split_indices(100, 0.3, seed=1)
        self.assertEqual(len(test), 30)
        self.assertEqual(set(train) & set(test), set())
        self.assertEqual(set(train) | set(test), set(range(100)))

    def test_same_seed_same_split(self):
        a = split_indices(50, 0.3, seed=5)
        b = split_indices(50, 0.3, seed=5)
        np.testing.assert_array_equal(a[1], b[1])

    def test_tiny_sample_keeps_both_sets_nonempty(self):
        train, test = split_indices(3, 0.9, seed=0)
        self.assertGreaterEqual(len(train), 1)
        self.assertGreaterEqual(len(test), 1)


if __name__ == "__main__":
    unittest.main()
