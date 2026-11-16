"""
build_report.py
---------------
Builds the PDF project report from the real results in outputs/results.json.

Steps:
  1. Fill in TEAM below (names, roll numbers, ...).
  2. Run  python main.py  so outputs/ is up to date.
  3. Run  python report/build_report.py
The PDF is saved as report/Sensor_Calibration_Comparison_Report.pdf
"""
import json
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

# ---------------------------------------------------------------- EDIT ME
TEAM = {
    "names": ["", "", "", "", ""],      # up to 5 names, leave "" for blank lines
    "roll_no": "",
    "enrollment_no": "",
    "section": "B",
    "submitted_to": "",
    "date_of_submission": "",
}
# ------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "outputs")
PDF_PATH = os.path.join(HERE, "Sensor_Calibration_Comparison_Report.pdf")
TITLE = "SENSOR CALIBRATION COMPARISON"
NAVY = colors.HexColor("#1f3a5f")
LIGHT = colors.HexColor("#e8eef6")

with open(os.path.join(OUT, "results.json"), encoding="utf-8") as f:
    R = json.load(f)

# ---------------------------------------------------------------- styles
ss = getSampleStyleSheet()
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Times-Roman", fontSize=11,
                      leading=15, alignment=TA_JUSTIFY, spaceAfter=6)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Times-Bold", fontSize=16,
                    textColor=NAVY, spaceBefore=10, spaceAfter=8)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Times-Bold", fontSize=12.5,
                    textColor=NAVY, spaceBefore=8, spaceAfter=4)
cap = ParagraphStyle("cap", parent=body, fontName="Times-Italic", fontSize=9.5,
                     alignment=TA_CENTER, spaceAfter=10)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=16, bulletIndent=4, spaceAfter=3)
cell = ParagraphStyle("cell", parent=body, fontSize=9.5, leading=12, alignment=0, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Times-Bold")
code = ParagraphStyle("code", parent=body, fontName="Courier", fontSize=9, leading=12,
                      alignment=0, leftIndent=10, backColor=colors.HexColor("#f4f4f4"))


def P(text, style=body):
    return Paragraph(text, style)


def bullets(items):
    return [Paragraph(t, bullet, bulletText="\u2022") for t in items]


def table(data, widths, header=True):
    rows = []
    for i, r in enumerate(data):
        st = cellb if (header and i == 0) else cell
        rows.append([Paragraph(str(c), st) for c in r])
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.6, colors.black),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), LIGHT))
    t.setStyle(TableStyle(style))
    return t


def figure(filename, caption, width=16.5 * cm):
    path = os.path.join(OUT, filename)
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(path).getSize()
    img = Image(path, width=width, height=width * h / w)
    return KeepTogether([img, P(caption, cap)])


# ---------------------------------------------------------------- numbers
res = {}
for row in R["heldout_results"]:
    res[(row["sensor_id"], row["method"])] = row
RAW, OFF, FULL = "raw (no correction)", "offset only", "offset + scale"
sensors = sorted({k[0] for k in res})
stab = R["stability"]
fits = {r["sensor_id"]: r for r in R["per_sensor_summary"]}

sys.path.insert(0, ROOT)
import generate_data  # noqa: E402  (gives us the injected "true" values)
TRUTH = generate_data.SENSORS


def pct(a, b):
    return 100 * (a - b) / a


# ---------------------------------------------------------------- page furniture
def cover(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setLineWidth(3)
    canvas.rect(1.2 * cm, 1.2 * cm, w - 2.4 * cm, h - 2.4 * cm)
    canvas.setLineWidth(1)
    canvas.rect(1.45 * cm, 1.45 * cm, w - 2.9 * cm, h - 2.9 * cm)
    canvas.restoreState()


def later(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFont("Times-Roman", 8.5)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(w - 2 * cm, h - 1.3 * cm, TITLE)
    canvas.line(2 * cm, h - 1.5 * cm, w - 2 * cm, h - 1.5 * cm)
    canvas.drawCentredString(w / 2, 1.1 * cm,
                             f"Department of Electronics and Communication Engineering  |  Page {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------- content
story = []

# ---- cover page
big = ParagraphStyle("big", parent=h1, fontSize=22, alignment=TA_CENTER, textColor=colors.black, leading=27)
mid = ParagraphStyle("mid", parent=body, fontName="Times-Bold", fontSize=14, alignment=TA_CENTER, leading=18)
field = ParagraphStyle("field", parent=body, fontSize=12, alignment=0, leading=22, spaceAfter=4)


def line(label, value=""):
    v = value if value else "_" * 34
    return P(f"<b>{label}:</b> {v}", field)


story += [Spacer(1, 1.2 * cm),
          P("INSTITUTE OF ENGINEERING &amp; MANAGEMENT, KOLKATA", big), Spacer(1, 1.0 * cm),
          line("COURSE TITLE", "BACHELOR OF TECHNOLOGY"),
          line("SUBJECT", "PYTHON PROGRAMMING LABORATORY"),
          line("PROJECT TITLE", "SENSOR CALIBRATION COMPARISON")]
names = [n if n else "_" * 14 for n in TEAM["names"]]
story += [P("<b>NAME:</b> " + "&nbsp;&nbsp;".join(f"{i + 1}. {n}" for i, n in enumerate(names[:3])), field),
          P("&nbsp;" * 14 + "&nbsp;&nbsp;".join(f"{i + 4}. {n}" for i, n in enumerate(names[3:5])), field),
          line("ROLL NO", TEAM["roll_no"]), line("ENROLLMENT NO", TEAM["enrollment_no"]),
          line("SECTION", TEAM["section"]), line("SUBMITTED TO", TEAM["submitted_to"]),
          line("DEPARTMENT NAME", "ELECTRONICS AND COMMUNICATION ENGINEERING"),
          line("ACADEMIC SESSION", "2026-2027"),
          line("DATE OF SUBMISSION", TEAM["date_of_submission"]), PageBreak()]

# ---- abstract
s1, s2, s3 = (res[("S1", FULL)]["MAE"], res[("S2", FULL)]["MAE"], res[("S3", FULL)]["MAE"])
story += [P(TITLE, h1), P("Abstract", h2),
          P("This project builds a Python program that calibrates low-cost sensors against a trusted reference "
            "instrument and then checks, honestly, whether the correction really helps. Paired readings are read "
            "from a CSV file, validated, grouped into <i>CalibrationRun</i> objects, and used to estimate each sensor's "
            "offset and scale error with NumPy. Pandas summarises repeated trials, and Matplotlib draws the "
            "before-and-after plots. The key design choice is that every correction is judged on <b>held-out</b> "
            "samples that were not used to fit it."),
          P(f"The dataset is <b>simulated</b>, not measured: three temperature sensors with known offset, scale error "
            f"and noise were generated, and 7 of the {R['input_rows']} rows were damaged on purpose. All 7 were caught by "
            f"validation, leaving {R['valid_rows']} valid pairs in {R['runs_used']} runs. Three methods were compared: raw readings, "
            f"offset-only correction, and offset-plus-scale correction. Offset-plus-scale gave the lowest held-out mean "
            f"absolute error for every sensor ({s1:.2f}, {s2:.2f} and {s3:.2f} deg C for S1, S2 and S3), and for S2 the "
            f"offset-only fix was no better than doing nothing. A straight-line correction could not fully remove the "
            f"curvature built into sensor S3. Because the data are simulated, the results show that the pipeline "
            f"works, not how any real sensor behaves."),
          P("Keywords", h2),
          P("Sensor calibration; offset and scale error; least squares; held-out evaluation; Python; NumPy; Pandas; "
            "Matplotlib; CSV; data validation."),
          P("Table of Contents", h2)]
toc = ["1. Introduction", "2. Problem Statement and Objectives", "3. Software and System Requirements",
       "4. System Design and Methodology", "5. Implementation of Major Modules", "6. Results and Discussion",
       "7. Testing and Validation", "8. Limitations and Future Scope", "9. Conclusion", "10. References",
       "11. Appendix: CSV Format and Execution", "12. Individual Contributions"]
story += [P(t) for t in toc] + [PageBreak()]

# ---- 1 intro
story += [P("1. Introduction", h1),
          P("Every sensor disagrees a little with the truth. A temperature sensor may always read 2 deg C high "
            "(an <i>offset</i> error), or may read 3% low across its range (a <i>scale</i> error), and it also "
            "jitters randomly (<i>noise</i>). Calibration compares the sensor with a trusted reference at several "
            "points and works out how to undo the systematic part of the error. This is an everyday task in "
            "electronics and instrumentation."),
          P("Doing this by hand in a spreadsheet is slow and easy to get wrong, and it is tempting to fit a "
            "correction and then test it on the very same points, which makes the result look better than it is. "
            "This project automates the whole process in Python and builds the honest test into the design: part of "
            "the data is hidden from the fitting step and used only to measure the final error."),
          P("The program reads paired readings from a CSV file, rejects broken rows with a reason, fits two "
            "different corrections, compares them against the uncorrected sensor, draws four labelled plots and "
            "writes a short plain-English analysis. All data in the submitted repository are simulated and are "
            "labelled as such everywhere.")]

# ---- 2 problem + objectives
story += [P("2. Problem Statement and Objectives", h1),
          P("<b>Problem statement:</b> Compare raw sensor measurements against known reference values. Validate paired "
            "readings, store runs in CSV, implement a CalibrationRun class, estimate offset, scale and error with NumPy, "
            "summarise repeated trials with Pandas, and draw raw and corrected scatter plots and error histograms. "
            "Evaluate whether the correction improves error on held-out samples and discuss the limitations."),
          P("The objectives are:")]
story += bullets([
    "Validate each (reference, raw) pair and reject missing, non-numeric or physically impossible values (CO1).",
    "Store and read runs using lists, dictionaries and CSV files (CO2).",
    "Represent one trial with a documented CalibrationRun class that uses special methods (CO3).",
    "Estimate offset, scale and error measures with NumPy arrays (CO4).",
    "Summarise repeated trials with Pandas and export CSV and JSON results (CO5).",
    "Plot raw versus corrected values and error histograms with Matplotlib, and interpret them (CO6).",
    "Evaluate offset-only against offset-plus-scale correction on held-out data, and repeat the test over many random splits.",
])

# ---- 3 requirements
story += [P("3. Software and System Requirements", h1),
          table([["Component", "Purpose"],
                 ["Python 3.9 or newer", "Core program execution"],
                 ["csv, json, math, random, os", "File handling, validation and simulated data generation"],
                 ["NumPy", "Arrays, least-squares line fit (polyfit), error measures, random splits"],
                 ["Pandas", "Tidy results tables, group-by summaries, CSV export"],
                 ["Matplotlib", "Scatter plots, histograms, bar and residual charts"],
                 ["unittest", "35 automated tests (pytest also works)"],
                 ["ReportLab (optional)", "Builds this PDF report from the real results"]],
                [5.5 * cm, 11 * cm]),
          Spacer(1, 6),
          P("The program runs on any ordinary desktop with Python and the three libraries listed in "
            "requirements.txt. It has no graphical window; it saves plots as PNG files.")]

# ---- 4 design
story += [P("4. System Design and Methodology", h1), P("4.1 Input data and schema", h2),
          P("Each CSV row is one paired reading with five columns: <i>run_id</i> (one trial), <i>sensor_id</i>, "
            "<i>sample_id</i>, <i>reference</i> (true temperature from the trusted instrument) and <i>raw</i> (what the "
            "sensor reported). Units are deg C."),
          P("4.2 Simulated data", h2),
          P("The file data/sensor_runs.csv is made by generate_data.py with a fixed random seed (42), so it is identical "
            "every time. Each fake reading follows"),
          P("raw = offset + scale x reference + curvature x (reference - 50)^2 + random noise", code),
          Spacer(1, 4)]
tr = [["Sensor", "True offset (deg C)", "True scale", "Noise std (deg C)", "Curvature"]]
for sid in sensors:
    t = TRUTH[sid]
    tr.append([sid, t["offset"], t["scale"], t["noise"], t["curve"] if t["curve"] else "none"])
story += [table(tr, [2.5 * cm, 3.8 * cm, 3 * cm, 3.8 * cm, 3.3 * cm]), Spacer(1, 4),
          P("Each sensor has 4 runs of 25 reference points from 0 to 100 deg C (300 rows in total). Sensor S3 is noisier "
            "and slightly curved on purpose, so that a straight-line fix cannot be perfect and the failure-case "
            "analysis has something real to explain. Seven rows were then damaged deliberately: missing readings, the text "
            "\"N/A\", the sensor error code -999, an impossible 480 deg C, and \"nan\". These test the validation step."),
          P("4.3 Workflow", h2)]
story += bullets([
    "Read the CSV into a list of dictionaries (csv.DictReader) and check that all required columns exist.",
    "Validate every row. A row is rejected if the reference or raw value is missing, not a finite number, or outside "
    "the allowed range of -40 to 150 deg C. The line number and reason are kept.",
    "Group the valid rows into CalibrationRun objects. A run with fewer than 5 valid pairs would be dropped.",
    "Per sensor, pool all runs and split the samples randomly: 70% to fit the correction, 30% held out.",
    "Fit both corrections on the 70% and apply them to the held-out 30%.",
    "Measure mean absolute error (MAE), root-mean-square error (RMSE) and maximum absolute error.",
    "Repeat the split 200 times with different seeds to check that the answer is not just luck.",
    "Fit each run separately to see how repeatable the offset and scale are from trial to trial.",
    "Save four plots, three tables, a JSON file and a written analysis.",
])
story += [P("4.4 Calibration model and error measures", h2),
          P("A sensor is modelled as <i>raw = offset + scale x reference</i>. Once offset and scale are known, a reading is "
            "corrected with <i>corrected = (raw - offset) / scale</i>. Two ways of estimating the parameters are compared:"),
          ]
story += bullets([
    "<b>Offset only:</b> offset = mean(raw - reference), scale fixed at 1.",
    "<b>Offset + scale:</b> a least-squares straight line through (reference, raw), found with numpy.polyfit. The "
    "reference is used as the x variable because the trusted instrument is the more accurate of the two.",
])
story += [P("With error = value - reference, the measures are MAE = mean(|error|), RMSE = square root of mean(error squared), "
            "and the maximum absolute error. MAE is the headline number because it is in deg C and easy to explain.")]

# ---- 5 modules
story += [P("5. Implementation of Major Modules", h1),
          table([["Module / function", "Functionality"],
                 ["validation.py: to_float(), check_pair(), validate_rows()", "Row-level checks, rejection reasons (CO1)"],
                 ["io_utils.py: load_rows(), save_rows(), save_json()", "CSV and JSON reading and writing (CO2)"],
                 ["run.py: CalibrationRun, build_runs()", "Class for one trial; grouping rows into runs (CO3)"],
                 ["fitting.py: fit_offset_only(), fit_offset_scale(), apply_correction(), mae(), rmse(), split_indices()",
                  "NumPy estimation, correction and error measures (CO4)"],
                 ["analysis.py: evaluate_all(), repeated_split_check(), per_run_fits(), sensor_fit_summary()",
                  "Held-out evaluation and Pandas group-by summaries (CO5)"],
                 ["plots.py: make_all_plots()", "Four Matplotlib figures (CO6)"],
                 ["main.py: run_pipeline()", "Runs everything and writes outputs"],
                 ["generate_data.py", "Creates the simulated dataset"]],
                [8.2 * cm, 8.3 * cm]),
          P("5.1 The CalibrationRun class and its special methods", h2),
          P("CalibrationRun stores the run id, sensor id and the two lists of paired values. The special methods are "
            "used because each one removes real work elsewhere in the program:")]
story += bullets([
    "<b>__init__</b> checks the data when the object is created, so a run with mismatched or empty lists can never exist.",
    "<b>__len__</b> makes len(run) the number of pairs, which build_runs() uses to drop runs that are too short.",
    "<b>__getitem__</b> gives run[i] and slices such as run[:5], returning (reference, raw) pairs.",
    "<b>__iter__</b> allows <i>for ref, raw in run</i>, which keeps the two lists in step without index bookkeeping.",
    "<b>__repr__</b> prints a readable description when debugging.",
])

# ---- 6 results
story += [PageBreak(), P("6. Results and Discussion", h1), P("6.1 Data validation", h2),
          P("All figures below come from the fixed-seed simulated dataset. They will change if a different CSV, split "
            "fraction or seed is used.")]
reasons = R["rejection_reasons"]
story += [table([["Indicator", "Value"],
                 ["Input rows", R["input_rows"]], ["Valid rows", R["valid_rows"]],
                 ["Rejected rows", R["rejected_rows"]], ["Runs used / dropped", f"{R['runs_used']} / {R['runs_dropped']}"],
                 ["Rejected: raw reading missing or not a number", reasons.get("raw reading missing or not a number", 0)],
                 ["Rejected: reference missing or not a number", reasons.get("reference missing or not a number", 0)],
                 ["Rejected: raw reading outside -40 to 150 deg C", reasons.get("raw reading outside allowed range", 0)]],
                [11 * cm, 5.5 * cm]),
          P("Every deliberately damaged row was caught, and no valid row was lost. This matches the tests in Section 7.")]

story += [P("6.2 Repeatability across trials", h2),
          P("Fitting each of the 4 runs of a sensor separately shows how stable the estimates are. The simulated truth is "
            "shown for comparison.")]
rt = [["Sensor", "True offset", "Fitted offset (mean +/- sd)", "True scale", "Fitted scale (mean +/- sd)"]]
for sid in sensors:
    f_ = fits[sid]
    rt.append([sid, TRUTH[sid]["offset"], f"{f_['offset_mean']:.2f} +/- {f_['offset_std']:.2f}",
               TRUTH[sid]["scale"], f"{f_['scale_mean']:.4f} +/- {f_['scale_std']:.4f}"])
story += [table(rt, [2 * cm, 2.6 * cm, 4.6 * cm, 2.6 * cm, 4.7 * cm]), Spacer(1, 4),
          P(f"S1 and S2 are recovered closely and scale is very repeatable (standard deviation below 0.005). S3 is less "
            f"stable: its offset estimate varies more between runs (sd {fits['S3']['offset_std']:.2f}) and its mean fitted "
            f"offset ({fits['S3']['offset_mean']:.2f}) is far from the true 0.5. That is not a bug. The curvature added to S3 "
            f"pushes the straight-line fit away from the true parameters, which is exactly the kind of model mismatch a "
            f"calibration engineer should watch for.")]

story += [P("6.3 Held-out comparison of the three methods", h2),
          P(f"For every sensor, 70% of the pooled samples were used to fit and the remaining {res[('S1', RAW)]['n_test']} "
            f"held-out samples were used to score (seed {R['seed']}).")]
ht = [["Sensor", "Method", "MAE (deg C)", "RMSE (deg C)", "Max error (deg C)"]]
for sid in sensors:
    for m in (RAW, OFF, FULL):
        r = res[(sid, m)]
        ht.append([sid, m, f"{r['MAE']:.3f}", f"{r['RMSE']:.3f}", f"{r['max_abs_error']:.3f}"])
story += [table(ht, [2 * cm, 4.6 * cm, 3 * cm, 3.4 * cm, 3.5 * cm]), Spacer(1, 6)]
story += [figure("03_mae_comparison.png", "Figure 1. Held-out MAE for the three methods and three sensors.", 12.5 * cm),
          figure("01_raw_vs_corrected_scatter.png", "Figure 2. Held-out raw and corrected readings against the reference. "
                 "Points on the dashed line are perfect."),
          figure("02_error_histograms.png", "Figure 3. Distribution of held-out errors before and after correction. "
                 "The corrected errors cluster closer to zero.")]
imp = {sid: pct(res[(sid, RAW)]["MAE"], res[(sid, FULL)]["MAE"]) for sid in sensors}
story += [P(f"Offset-plus-scale correction gave the smallest MAE for every sensor, improving on the raw sensor by "
            f"{imp['S1']:.0f}% (S1), {imp['S2']:.0f}% (S2) and {imp['S3']:.0f}% (S3). Two observations are worth "
            f"highlighting:")]
story += bullets([
    f"<b>S2: offset-only did not help.</b> Its MAE was {res[('S2', OFF)]['MAE']:.2f} deg C against {res[('S2', RAW)]['MAE']:.2f} "
    f"for the raw sensor. S2 reads about 3% too high (scale 1.03), so its error grows with temperature: it is "
    f"negative at the cold end and positive at the hot end. A single constant shift cannot fix an error that changes sign, so the "
    f"fuller model is needed.",
    f"<b>S1: offset-only helped a little, scale helped a lot.</b> The MAE fell from {res[('S1', RAW)]['MAE']:.2f} to "
    f"{res[('S1', OFF)]['MAE']:.2f} with offset only, but to {res[('S1', FULL)]['MAE']:.2f} with scale included.",
])

story += [P("6.4 Is the result just luck? Repeated random splits", h2),
          P("A single random split can be lucky. The held-out experiment was therefore repeated with 200 different splits "
            "per sensor, counting how often offset-plus-scale had a lower MAE.")]
st = [["Sensor", "Beats raw", "Beats offset-only", "Mean MAE (deg C)", "Std of MAE"]]
for sid in sensors:
    s = stab[sid]
    st.append([sid, f"{100 * s['full_beats_raw']:.1f}%", f"{100 * s['full_beats_offset_only']:.1f}%",
               f"{s['mae_full_mean']:.3f}", f"{s['mae_full_std']:.3f}"])
story += [table(st, [2.2 * cm, 3 * cm, 4 * cm, 3.8 * cm, 3.5 * cm]), Spacer(1, 4),
          P("The advantage of offset-plus-scale is not an artefact of one split: it wins in at least 97% of splits against "
            "both alternatives for every sensor. Sensor S3 shows the widest spread in MAE, reflecting its higher noise and "
            "curvature.")]

story += [P("6.5 Failure cases and leftover error", h2),
          figure("04_residuals_after_correction.png", "Figure 4. Error remaining after offset-plus-scale correction. "
                 "A visible curve means the straight-line model is not enough."),
          P("For S1 and S2 the leftover errors are small and roughly centred on zero, with no strong pattern. S3 has the "
            "widest scatter, and its errors are mostly positive near both ends of the range and mostly negative in the middle, "
            "which is the signature of the curvature built into the simulation. The noise (1.2 deg C) partly hides this "
            "pattern, so it is a tendency rather than a clean curve. This is a limit of the model, not of the code: a straight line cannot "
            "remove a bend. A quadratic or piecewise correction would be the natural next step."),
          P("The other failure cases are handled at the input: missing values, text, error codes and impossible readings "
            "are rejected before they can distort the fit. One reading of -999 left in would have dragged the "
            "least-squares line badly, which is why validation comes first.")]

# ---- 7 testing
story += [P("7. Testing and Validation", h1),
          P("The project includes 35 automated tests in the tests folder (run with "
            "<font face='Courier'>python -m unittest discover -s tests -t .</font>). All pass.")]
story += [table([["Test case", "Expected behaviour", "Result"],
                 ["to_float() on '', 'abc', None, 'nan', 'inf'", "Returns None", "Pass"],
                 ["Missing raw / missing reference", "Pair rejected with matching reason", "Pass"],
                 ["Raw = -999 or 480", "Rejected as out of range", "Pass"],
                 ["Values exactly -40 and 150", "Accepted (boundaries inclusive)", "Pass"],
                 ["Mismatched or empty lists in CalibrationRun", "ValueError raised", "Pass"],
                 ["len(), indexing, slicing, iteration of a run", "Behave like a sequence of pairs", "Pass"],
                 ["Run with fewer than 5 pairs", "Dropped by build_runs()", "Pass"],
                 ["Noise-free data, offset 3.0 and scale 0.9", "Fit recovers both to 6 decimals", "Pass"],
                 ["Noisy data (200 points)", "Offset within 0.2, scale within 0.01", "Pass"],
                 ["Flat sensor (constant output)", "ValueError: cannot invert correction", "Pass"],
                 ["Train / test split", "No overlap, full coverage, repeatable with same seed", "Pass"],
                 ["Full pipeline on simulated data", "All 7 broken rows caught, 12 runs kept", "Pass"],
                 ["Held-out MAE, offset+scale vs raw and vs offset-only", "Lower for every sensor", "Pass"],
                 ["Fitted values for S1 vs injected truth", "Close to 2.0 and 0.97", "Pass"],
                 ["CSV missing a required column", "Clear ValueError", "Pass"],
                 ["run_pipeline()", "Creates plots, tables, JSON and analysis files", "Pass"]],
                [6.5 * cm, 7.5 * cm, 2.5 * cm])]

# ---- 8 limitations
story += [P("8. Limitations and Future Scope", h1),
          P("<b>Limitations:</b> (i) the data are simulated, so the results demonstrate the method, not real hardware; "
            "(ii) only a straight-line correction is implemented; (iii) ordinary least squares is sensitive to extreme "
            "points that pass validation; (iv) one sensor type (temperature) and one range (0 to 100 deg C) are modelled; "
            "(v) the held-out samples come from the same runs as the training samples, so drift between days is not tested."),
          P("<b>Possible extensions:</b> polynomial or piecewise correction for curved sensors; robust fitting that down-weights "
            "outliers; holding out whole runs (or whole days) to test drift; temperature-dependent noise; a small command-line "
            "or Tkinter interface; and trying the same pipeline on real measurements with proper consent and documentation.")]

# ---- 9 conclusion
story += [P("9. Conclusion", h1),
          P("The project delivers a complete, reproducible calibration workflow: CSV input, row validation, a "
            "CalibrationRun class, NumPy least-squares fitting, Pandas summaries, Matplotlib plots and a written "
            "interpretation. On the simulated data, offset-plus-scale correction reduced held-out error for every sensor and "
            "beat offset-only correction in at least 97% of 200 random splits. The offset-only fix failed completely for a "
            "sensor whose main fault was scale, and no straight-line fix could remove the curvature in S3. The central "
            "lesson is that a correction should be judged on data it has not seen, and that the shape of the leftover error "
            "is as informative as the average.")]

# ---- 10 references
story += [P("10. References", h1)]
story += [P(t) for t in [
    "Python Software Foundation. Python 3 Documentation. https://docs.python.org/3/",
    "NumPy Developers. NumPy Documentation (numpy.polyfit, numpy.random.default_rng). https://numpy.org/doc/",
    "Pandas Development Team. pandas Documentation. https://pandas.pydata.org/docs/",
    "Matplotlib Development Team. Matplotlib Documentation. https://matplotlib.org/stable/",
    "Python Software Foundation. unittest - Unit testing framework. https://docs.python.org/3/library/unittest.html",
]]

# ---- 11 appendix
story += [P("11. Appendix: CSV Format and Execution", h1),
          P("Required input CSV headers (exact spelling): run_id, sensor_id, sample_id, reference, raw."),
          table([["run_id", "sensor_id", "sample_id", "reference", "raw"],
                 ["S1_R1", "S1", "1", "0.0", "2.13"], ["S1_R1", "S1", "2", "4.2", "6.05"],
                 ["S1_R1", "S1", "3", "8.3", "10.31"]], [3 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm]),
          Spacer(1, 6), P("To run the project:"),
          P("pip install -r requirements.txt<br/>python generate_data.py<br/>python main.py<br/>"
            "python -m unittest discover -s tests -t .", code),
          Spacer(1, 4),
          P("Results appear in the outputs folder. The dataset is simulated and must be described as simulated in any "
            "presentation.")]

# ---- 12 contributions
story += [P("12. Individual Contributions", h1),
          P("The detailed table of who did what is in CONTRIBUTIONS.md in the repository. Every team member is "
            "prepared to explain all modules, tests and results in the individual viva.")]


def build():
    doc = SimpleDocTemplate(PDF_PATH, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2.2 * cm, bottomMargin=2 * cm,
                            title="Sensor Calibration Comparison - Project Report")
    doc.build(story, onFirstPage=cover, onLaterPages=later)
    print("Wrote", PDF_PATH)


if __name__ == "__main__":
    build()
