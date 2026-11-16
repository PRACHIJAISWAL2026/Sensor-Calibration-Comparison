# Sensor Calibration Comparison

Python Programming Laboratory – end-semester group project
Institute of Engineering & Management, Kolkata · B.Tech ECE · Section B · Session 2026-27

> **Heads-up: all data in this project is SIMULATED.** No real sensor was measured.
> We invented three temperature sensors with a known offset, scale error and noise
> so we know the "right answer" and can check that our code finds it.

## What is this project about?

Cheap sensors are rarely perfect. A temperature sensor might read 2 °C too high, or
read 3% too low at the top of its range. **Calibration** means comparing the sensor
against a trusted reference instrument and working out a correction.

This program does that, and then asks the honest question:

> *Does the correction really make the sensor better on data it has never seen?*

To answer it fairly we keep 30% of the samples aside (the **held-out set**), fit the
correction on the other 70%, and measure the error on the held-out part. We compare
three options:

| Method | Idea |
|---|---|
| raw (no correction) | use the sensor as it is |
| offset only | subtract the average shift, assume scale is perfect |
| offset + scale | fit a straight line and undo both errors |

## Project structure

```
Sensor-Calibration-Comparison/
├── main.py                  # run this: CSV -> validation -> fit -> evaluation -> plots
├── generate_data.py         # creates the SIMULATED dataset (data/sensor_runs.csv)
├── calibration/
│   ├── validation.py        # check each pair of readings          (CO1)
│   ├── io_utils.py          # CSV / JSON reading and writing       (CO2)
│   ├── run.py               # CalibrationRun class + special methods (CO3)
│   ├── fitting.py           # NumPy: offset, scale, error metrics  (CO4)
│   ├── analysis.py          # Pandas summaries + held-out testing  (CO5)
│   └── plots.py             # Matplotlib figures                   (CO6)
├── data/sensor_runs.csv     # simulated data (300 rows, 7 deliberately broken)
├── outputs/                 # sample results: 4 plots, CSV/JSON tables, analysis.txt
├── tests/                   # 35 unit and end-to-end tests
├── report/                  # PDF report + the script that builds it
├── CONTRIBUTIONS.md         # who did what
└── requirements.txt
```

## How to run it

You need Python 3.9 or newer.

```bash
# 1. (optional) make a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux

# 2. install the libraries
pip install -r requirements.txt

# 3. create the simulated dataset (same result every time, seed = 42)
python generate_data.py

# 4. run the whole analysis
python main.py
```

Plots and tables appear in the `outputs/` folder. Options:

```bash
python main.py --data my_file.csv --test-fraction 0.25 --seed 3
```

### Run the tests

```bash
python -m unittest discover -s tests -t . -v
```

(`pytest` also works if you have it installed.)

### Using your own data

Any CSV with these exact column names will work:

```
run_id,sensor_id,sample_id,reference,raw
S1_R1,S1,1,0.0,2.13
```

Rows with missing, non-numeric or impossible values (outside −40 to 150) are skipped
and listed in `outputs/rejected_rows.csv`.

## The class and why we used special methods (CO3)

`CalibrationRun` (in `calibration/run.py`) holds one trial of one sensor.

* `__init__` – refuses to build a run if the two lists have different lengths or are empty
* `__len__` – `len(run)` = number of paired samples; used to drop runs that are too short
* `__getitem__` – `run[3]` or `run[:5]` returns (reference, raw) pairs
* `__iter__` – lets us write `for ref, raw in run:`
* `__repr__` – readable output when debugging

## Sample results (seed 7, 30% held-out)

| Sensor | Raw MAE | Offset-only MAE | Offset + scale MAE |
|---|---|---|---|
| S1 | 0.84 °C | 0.70 °C | **0.32 °C** |
| S2 | 1.22 °C | 1.23 °C | **0.71 °C** |
| S3 | 2.29 °C | 1.98 °C | **1.35 °C** |

What we noticed:

* Offset + scale was best for all three sensors, and beat offset-only in at least 97% of 200 random splits.
* For S2, offset-only was actually slightly *worse* than doing nothing, because S2's main
  problem is its scale error (+3%), not a constant shift.
* S3 is still the worst after correction. Its simulated response is slightly curved, and a
  straight line can't remove curvature (see `outputs/04_residuals_after_correction.png`).

The full written analysis is in `outputs/analysis.txt` and in the PDF report.

## Limitations

* Data are simulated, so the numbers prove the pipeline works, not how real sensors behave.
* Only a straight-line (linear) correction is implemented.
* Fitting is ordinary least squares, so a few extreme outliers that pass validation could pull the line.
* Only one random train/test split is shown in the plots (the 200-split check backs it up).

## Bloom-level evidence (where to find it)

| Level | Where |
|---|---|
| BL2 explain | Section 4 of the report, comments in each module |
| BL3 implement | `main.py` pipeline |
| BL4 analyse | per-run repeatability table, rejected-row list, residual plot |
| BL5 evaluate | three-method comparison + 200-split stability check |
| BL6 create | whole repo, reproducible with two commands (`generate_data.py`, `main.py`) |

## Team

See `CONTRIBUTIONS.md`.
