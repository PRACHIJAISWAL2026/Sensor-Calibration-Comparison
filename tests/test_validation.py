"""Tests for the validation functions (CO1)."""
import unittest

from calibration.validation import check_pair, to_float, validate_rows


class TestToFloat(unittest.TestCase):
    def test_normal_numbers(self):
        self.assertEqual(to_float("12.5"), 12.5)
        self.assertEqual(to_float(3), 3.0)

    def test_bad_values_give_none(self):
        for bad in ["", "abc", None, "nan", "inf"]:
            self.assertIsNone(to_float(bad), msg=f"{bad!r} should be rejected")


class TestCheckPair(unittest.TestCase):
    def test_good_pair(self):
        self.assertEqual(check_pair("20", "21.3"), (True, "ok"))

    def test_missing_raw(self):
        ok, reason = check_pair("20", "")
        self.assertFalse(ok)
        self.assertIn("raw", reason)

    def test_missing_reference(self):
        ok, reason = check_pair("", "20")
        self.assertFalse(ok)
        self.assertIn("reference", reason)

    def test_sensor_error_code(self):
        ok, _ = check_pair("20", "-999")
        self.assertFalse(ok)

    def test_impossible_high_reading(self):
        ok, _ = check_pair("20", "480")
        self.assertFalse(ok)

    def test_boundaries_are_allowed(self):
        self.assertTrue(check_pair("-40", "150")[0])


class TestValidateRows(unittest.TestCase):
    def test_splits_good_and_bad(self):
        rows = [
            {"run_id": "A", "sensor_id": "S1", "sample_id": "1", "reference": "10", "raw": "11"},
            {"run_id": "A", "sensor_id": "S1", "sample_id": "2", "reference": "20", "raw": "N/A"},
            {"run_id": "", "sensor_id": "S1", "sample_id": "3", "reference": "30", "raw": "31"},
        ]
        good, rejected = validate_rows(rows)
        self.assertEqual(len(good), 1)
        self.assertEqual(len(rejected), 2)
        self.assertEqual(good[0]["raw"], 11.0)          # converted to float
        self.assertEqual(rejected[0]["line"], 3)        # header is line 1, first row line 2


if __name__ == "__main__":
    unittest.main()
