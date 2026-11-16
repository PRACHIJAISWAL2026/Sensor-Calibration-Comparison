"""
io_utils.py
-----------
Reading and writing files.  (CO2: file I/O, lists and dictionaries)
"""
import csv
import json
import os

from .validation import REQUIRED_COLUMNS


def load_rows(path):
    """Read the CSV into a list of dictionaries. Stops early if a column is missing."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV is missing required column(s): {missing}")
        return list(reader)


def save_rows(path, rows, fieldnames):
    """Write a list of dicts to a CSV file."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_json(path, data):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
