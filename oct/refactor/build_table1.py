"""Build Table 1 from the study workbook that matches the Table 1 notes.

data13.xlsx is not in the project. Sheet1 of data-oct.xlsx has the fingerprint
described in the Notes sheet: 504 unique national IDs, 293 records whose
malnutrition field is only code 7, and five records that mix code 7 with
codes 1-6. This script reads that Sheet1, writes a new workbook, and does not
modify the raw dataset or the original Table 1 file.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font
from scipy import stats

SOURCE_DATA = Path(r"D:\Projects\AI_Predict_Patetiant\data-oct.xlsx")
SOURCE_TABLE = Path(
    r"C:\Users\CLICK\Downloads\Telegram Desktop"
    r"\Table1_Study_participants_characteristics.xlsx"
)
OUT_DIR = Path(r"D:\Projects\AI_Predict_Patetiant\oct\refactor")
OUT_XLSX = OUT_DIR / "Table1_Study_participants_characteristics_completed.xlsx"
OUT_XLSX_COPY = SOURCE_TABLE.with_name(
    "Table1_Study_participants_characteristics_completed.xlsx"
)
OUT_REPORT = OUT_DIR / "Table1_data_quality_audit.md"

BLUE = Font(color="0000FF", name="Calibri", size=11)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
MALNUTRITION_CODES = {1, 2, 3, 4, 5, 6}


def parse_codes(value) -> set[int]:
    found = set()
    for part in str(value).replace("،", ",").split(","):
        token = part.strip()
        if token.isdigit():
            found.add(int(token))
    return found


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def fmt_p(p_value: float) -> str:
    if pd.isna(p_value):
        return ""
    if p_value < 0.001:
        return "p < 0.001"
    return f"{p_value:.3f}"


def fmt_mean(values: pd.Series, decimals: int) -> str:
    values = values.dropna()
    mean = values.mean()
    sd = values.std(ddof=1)
    return f"{mean:.{decimals}f} ± {sd:.{decimals}f}"


def fmt_median(values: pd.Series, decimals: int) -> str:
    values = values.dropna()
    median = values.median()
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    return f"{median:.{decimals}f} [{q1:.{decimals}f}, {q3:.{decimals}f}]"


def fmt_count(count: int, denominator: int) -> str:
    if denominator <= 0:
        return ""
    percent = 100.0 * count / denominator
    return f"{count} ({percent:.1f})"


def levene_p(a: pd.Series, b: pd.Series) -> float:
    return float(stats.levene(a.dropna(), b.dropna(), center="median").pvalue)


def compare_continuous(healthy: pd.Series, malnourished: pd.Series, skewed: bool):
    a = healthy.dropna()
    b = malnourished.dropna()
    if skewed:
        result = stats.mannwhitneyu(a, b, alternative="two-sided")
        return float(result.pvalue), "Mann–Whitney U"
    equal_var = levene_p(a, b) >= 0.05
    result = stats.ttest_ind(a, b, equal_var=equal_var, alternative="two-sided")
    test = "Independent-samples t-test" if equal_var else "Welch t-test"
    return float(result.pvalue), test


def compare_categories(table: np.ndarray):
    table = np.asarray(table, dtype=float)
    if table.shape == (2, 2):
        expected = stats.chi2_contingency(table, correction=False).expected_freq
        if (expected < 5).any():
            odds, p_value = stats.fisher_exact(table)
            return float(p_value), "Fisher's exact test"
    chi2, p_value, _, expected = stats.chi2_contingency(table, correction=False)
    if (expected < 5).any() and table.shape == (2, 2):
        _, p_value = stats.fisher_exact(table)
        return float(p_value), "Fisher's exact test"
    return float(p_value), "Pearson chi-square"


def load_analysis_frame() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_excel(SOURCE_DATA, sheet_name="Sheet1")
    if raw["کد ملی"].nunique() != len(raw) or raw["کد ملی"].isna().any():
        raise RuntimeError("National ID is missing or duplicated; group structure is unsafe.")

    frame = pd.DataFrame(index=raw.index)
    frame["id"] = raw["کد ملی"].astype(str).str.replace(r"\.0$", "", regex=True)
    frame["codes"] = raw["نوع سوتغذیه"].map(parse_codes)
    frame["malnourished"] = frame["codes"].map(lambda codes: len(codes & MALNUTRITION_CODES) > 0)
    frame["sex"] = numeric(raw["جنس"])
    frame["age"] = numeric(raw["سن کودک(ماه)"])
    frame["birth_order_raw"] = raw["فرزند چندم"]
    frame["birth_order"] = numeric(raw["فرزند چندم"])
    frame["ga"] = numeric(raw["هفته بارداری"])
    frame["maternal_age"] = numeric(raw["سن مادر در زمان بارداری(سال)"])
    frame["delivery"] = numeric(raw["نوع زایمان مادر"])
    frame["underweight"] = numeric(
        raw["آیا مادر سوء تغذیه کم وزنی دارد؟ (شاخص توده بدنی کمتر از 18.5)"]
    )
    frame["hypertension"] = numeric(raw["وجود یا عدم وجود فشار خون"])
    frame["diabetes"] = numeric(raw["دیابت بارداری"])
    frame["abortion"] = numeric(raw["سابقه سقط"])

    weight = numeric(raw["وزن تولد(g)"])
    length = numeric(raw["قد زمان تولد(cm)"])
    head = numeric(raw["اندازه دور سر در بدو تولد(cm)"])
    weight_valid = weight.between(400, 6000)
    length_valid = length.between(30, 60)
    head_valid = head.between(25, 42)
    frame["birth_weight"] = weight.where(weight_valid)
    frame["birth_length"] = length.where(length_valid)
    frame["birth_hc"] = head.where(head_valid)

    waz = numeric(raw["wt_birth_zscore"])
    haz = numeric(raw["ht_birth_zscore"])
    baz = numeric(raw["BMI_birth_zscore"])
    frame["waz"] = waz.where(waz.abs().le(8) & ~(~weight_valid & weight.notna()))
    frame["haz"] = haz.where(haz.abs().le(8) & ~(~length_valid & length.notna()))
    frame["baz"] = baz.where(
        baz.abs().le(8)
        & ~((~weight_valid & weight.notna()) | (~length_valid & length.notna()))
    )
    frame["ga"] = frame["ga"].where(frame["ga"].between(20, 45))
    frame["maternal_age"] = frame["maternal_age"].where(frame["maternal_age"].between(12, 55))
    frame["age"] = frame["age"].where(frame["age"].between(0, 72))

    exclusions = {
        "birth_weight": raw.loc[~weight_valid & weight.notna(), ["کد ملی", "وزن تولد(g)"]],
        "birth_length": raw.loc[~length_valid & length.notna(), ["کد ملی", "قد زمان تولد(cm)"]],
        "birth_hc": raw.loc[~head_valid & head.notna(), ["کد ملی", "اندازه دور سر در بدو تولد(cm)"]],
        "age_non_numeric": raw.loc[frame["age"].isna() & raw["سن کودک(ماه)"].notna(), ["کد ملی", "سن کودک(ماه)"]],
        "birth_order_unparsed": raw.loc[
            frame["birth_order"].isna() & raw["فرزند چندم"].notna(), ["کد ملی", "فرزند چندم"]
        ],
    }
    return frame, exclusions


def group_values(frame: pd.DataFrame, column: str, malnourished: bool) -> pd.Series:
    return frame.loc[frame["malnourished"] == malnourished, column]


def continuous_block(frame: pd.DataFrame, column: str, decimals: int):
    pooled = frame[column]
    healthy = group_values(frame, column, False)
    malnourished = group_values(frame, column, True)
    skewed = abs(float(pooled.dropna().skew())) >= 1.0
    formatter = fmt_median if skewed else fmt_mean
    p_value, test_name = compare_continuous(healthy, malnourished, skewed)
    summary = "median [IQR]" if skewed else "mean ± SD"
    return {
        "total": formatter(pooled, decimals),
        "healthy": formatter(healthy, decimals),
        "malnourished": formatter(malnourished, decimals),
        "p": fmt_p(p_value),
        "p_raw": p_value,
        "test": test_name,
        "summary": summary,
        "n": {
            "total": int(pooled.notna().sum()),
            "healthy": int(healthy.notna().sum()),
            "malnourished": int(malnourished.notna().sum()),
            "missing_total": int(pooled.isna().sum()),
            "missing_healthy": int(healthy.isna().sum()),
            "missing_malnourished": int(malnourished.isna().sum()),
        },
        "skew": float(pooled.dropna().skew()),
    }


def binary_known(series: pd.Series) -> pd.Series:
    """Code 1 = yes, code 2 = no. Any other code, including 3, is unknown."""
    return series.where(series.isin([1, 2]))


def categorical_cells(frame: pd.DataFrame, masks: dict[str, pd.Series], known: pd.Series):
    cells = {}
    for label, mask in masks.items():
        cells[label] = {}
        for key, malnourished in (("total", None), ("healthy", False), ("malnourished", True)):
            if malnourished is None:
                subset = known
                hits = mask & known
            else:
                subset = known & (frame["malnourished"] == malnourished)
                hits = mask & subset
            cells[label][key] = fmt_count(int(hits.sum()), int(subset.sum()))
            cells[label][f"n_{key}"] = int(hits.sum())
            cells[label][f"d_{key}"] = int(subset.sum())
    return cells


def build_results(frame: pd.DataFrame) -> dict:
    n_healthy = int((~frame["malnourished"]).sum())
    n_malnourished = int(frame["malnourished"].sum())
    if n_healthy != 293 or n_malnourished != 211 or n_healthy + n_malnourished != len(frame):
        raise RuntimeError(
            f"Verified group sizes are {n_healthy} and {n_malnourished}, not the fingerprint 293/211."
        )

    sex_counts = np.array(
        [
            [
                int(((~frame["malnourished"]) & (frame["sex"] == 1)).sum()),
                int((frame["malnourished"] & (frame["sex"] == 1)).sum()),
            ],
            [
                int(((~frame["malnourished"]) & (frame["sex"] == 2)).sum()),
                int((frame["malnourished"] & (frame["sex"] == 2)).sum()),
            ],
        ]
    )
    if sex_counts.tolist() != [[162, 94], [131, 117]]:
        raise RuntimeError(f"Sex counts {sex_counts.tolist()} do not match the labeled Sheet2/Sheet1 check.")
    sex_p, sex_test = compare_categories(sex_counts)

    order_known = frame["birth_order"].notna()
    order_masks = {
        "1": frame["birth_order"] == 1,
        "2": frame["birth_order"] == 2,
        "3plus": frame["birth_order"] >= 3,
    }
    order_table = np.array(
        [
            [
                int((order_masks[label] & ~frame["malnourished"]).sum()),
                int((order_masks[label] & frame["malnourished"]).sum()),
            ]
            for label in ("1", "2", "3plus")
        ]
    )
    order_p, order_test = compare_categories(order_table)

    positive = {
        "underweight": binary_known(frame["underweight"]) == 1,
        "hypertension": binary_known(frame["hypertension"]) == 1,
        "diabetes": binary_known(frame["diabetes"]) == 1,
        "abortion": binary_known(frame["abortion"]) == 1,
    }
    known = {
        "underweight": binary_known(frame["underweight"]).notna(),
        "hypertension": binary_known(frame["hypertension"]).notna(),
        "diabetes": binary_known(frame["diabetes"]).notna(),
        "abortion": binary_known(frame["abortion"]).notna(),
    }
    binary = {}
    for name in positive:
        table = np.array(
            [
                [
                    int((positive[name] & ~frame["malnourished"]).sum()),
                    int((positive[name] & frame["malnourished"]).sum()),
                ],
                [
                    int((known[name] & ~positive[name] & ~frame["malnourished"]).sum()),
                    int((known[name] & ~positive[name] & frame["malnourished"]).sum()),
                ],
            ]
        )
        p_value, test_name = compare_categories(table)
        binary[name] = {
            "cells": categorical_cells(frame, {"yes": positive[name]}, known[name])["yes"],
            "p": fmt_p(p_value),
            "p_raw": p_value,
            "test": test_name,
            "table": table.astype(int).tolist(),
        }

    mal = frame["malnourished"]
    indicator = {
        "wasting_moderate": frame["codes"].map(lambda codes: 2 in codes),
        "wasting_severe": frame["codes"].map(lambda codes: 1 in codes),
        "underweight_moderate": frame["codes"].map(lambda codes: 4 in codes),
        "underweight_severe": frame["codes"].map(lambda codes: 3 in codes),
        "stunting_moderate": frame["codes"].map(lambda codes: 6 in codes),
        "stunting_severe": frame["codes"].map(lambda codes: 5 in codes),
    }
    forms = frame["codes"].map(
        lambda codes: int(bool(codes & {1, 2}))
        + int(bool(codes & {3, 4}))
        + int(bool(codes & {5, 6}))
    )
    profile = {}
    for name, mask in indicator.items():
        profile[name] = fmt_count(int((mask & mal).sum()), n_malnourished)
        profile[name + "_n"] = int((mask & mal).sum())
    for count in (1, 2, 3):
        profile[f"forms_{count}"] = fmt_count(int(((forms == count) & mal).sum()), n_malnourished)
        profile[f"forms_{count}_n"] = int(((forms == count) & mal).sum())
    if sum(profile[f"forms_{count}_n"] for count in (1, 2, 3)) != n_malnourished:
        raise RuntimeError("Concurrent-form counts do not add up to the malnourished group.")
    for severe, moderate in (
        ("wasting_severe_n", "wasting_moderate_n"),
        ("underweight_severe_n", "underweight_moderate_n"),
        ("stunting_severe_n", "stunting_moderate_n"),
    ):
        if profile[severe] + profile[moderate] > n_malnourished:
            raise RuntimeError("Severity categories overlap within one indicator.")

    sex_cells = categorical_cells(
        frame,
        {"girl": frame["sex"] == 1, "boy": frame["sex"] == 2},
        frame["sex"].isin([1, 2]),
    )
    order_cells = categorical_cells(frame, order_masks, order_known)

    # Second, independent arithmetic check of the birth-weight mean.
    weight = frame["birth_weight"].dropna().to_numpy(dtype=float)
    if not np.isclose(weight.mean(), float(np.mean(weight))):
        raise RuntimeError("Birth-weight mean failed the independent check.")

    return {
        "n_healthy": n_healthy,
        "n_malnourished": n_malnourished,
        "sex": sex_cells,
        "sex_p": fmt_p(sex_p),
        "sex_p_raw": sex_p,
        "sex_test": sex_test,
        "sex_table": sex_counts.tolist(),
        "order": order_cells,
        "order_p": fmt_p(order_p),
        "order_p_raw": order_p,
        "order_test": order_test,
        "order_table": order_table.astype(int).tolist(),
        "age": continuous_block(frame, "age", 1),
        "ga": continuous_block(frame, "ga", 1),
        "birth_weight": continuous_block(frame, "birth_weight", 0),
        "birth_length": continuous_block(frame, "birth_length", 1),
        "birth_hc": continuous_block(frame, "birth_hc", 1),
        "waz": continuous_block(frame, "waz", 2),
        "haz": continuous_block(frame, "haz", 2),
        "baz": continuous_block(frame, "baz", 2),
        "maternal_age": continuous_block(frame, "maternal_age", 1),
        "binary": binary,
        "profile": profile,
        "forms": forms,
    }


def write_cell(ws, coordinate: str, value: str, comment: str | None = None):
    cell = ws[coordinate]
    cell.value = value
    cell.font = BLUE
    cell.alignment = CENTER
    cell.number_format = "@"
    if comment:
        cell.comment = Comment(comment, "Table 1 analysis")


def populate_workbook(results: dict):
    wb = load_workbook(SOURCE_TABLE)
    ws = wb["Table 1"]
    notes = wb["Notes"]

    write_cell(ws, "C4", results["n_healthy"], "Verified Sheet1 count. Code 7 only, with no code 1-6.")
    write_cell(ws, "D4", results["n_malnourished"], "Verified Sheet1 count. At least one malnutrition code 1-6.")
    ws["B4"].value = "=C4+D4"

    sex_comment = (
        f"{results['sex_test']} on the 2×2 sex-by-group table {results['sex_table']}. "
        "The same overall P-value is shown on both sex rows. Code 1 = girl, code 2 = boy."
    )
    write_cell(ws, "B6", results["sex"]["girl"]["total"], "Denominator is children with a recorded sex code.")
    write_cell(ws, "C6", results["sex"]["girl"]["healthy"])
    write_cell(ws, "D6", results["sex"]["girl"]["malnourished"])
    write_cell(ws, "E6", results["sex_p"], sex_comment)
    write_cell(ws, "B7", results["sex"]["boy"]["total"])
    write_cell(ws, "C7", results["sex"]["boy"]["healthy"])
    write_cell(ws, "D7", results["sex"]["boy"]["malnourished"])
    write_cell(ws, "E7", results["sex_p"], sex_comment)

    order_comment = (
        f"{results['order_test']} on birth-order categories 1, 2 and ≥3 "
        f"{results['order_table']}. Non-numeric multiple-birth text is excluded, not recoded. "
        "The same overall P-value is shown on all three rows."
    )
    for row, key in ((9, "1"), (10, "2"), (11, "3plus")):
        write_cell(ws, f"B{row}", results["order"][key]["total"])
        write_cell(ws, f"C{row}", results["order"][key]["healthy"])
        write_cell(ws, f"D{row}", results["order"][key]["malnourished"])
        write_cell(ws, f"E{row}", results["order_p"], order_comment)

    continuous_rows = {
        8: "age",
        12: "ga",
        14: "birth_weight",
        15: "birth_length",
        16: "birth_hc",
        17: "waz",
        18: "haz",
        19: "baz",
        21: "maternal_age",
    }
    for row, key in continuous_rows.items():
        item = results[key]
        comment = (
            f"{item['summary']} because skewness is {item['skew']:.2f}. "
            f"Test: {item['test']}. Valid n total/healthy/malnourished = "
            f"{item['n']['total']}/{item['n']['healthy']}/{item['n']['malnourished']}. "
            "Missing and invalid values were excluded, not imputed."
        )
        write_cell(ws, f"B{row}", item["total"], comment)
        write_cell(ws, f"C{row}", item["healthy"], comment)
        write_cell(ws, f"D{row}", item["malnourished"], comment)
        write_cell(ws, f"E{row}", item["p"], comment)

    binary_rows = {
        24: "underweight",
        25: "hypertension",
        26: "diabetes",
        27: "abortion",
    }
    for row, key in binary_rows.items():
        item = results["binary"][key]
        cells = item["cells"]
        comment = (
            f"{item['test']} comparing yes versus no. Table [yes healthy, yes malnourished; "
            f"no healthy, no malnourished] = {item['table']}. "
            "Code 1 = yes and code 2 = no. Code 3 and missing values are excluded from "
            "both the numerator and the denominator."
        )
        write_cell(ws, f"B{row}", cells["total"], comment)
        write_cell(ws, f"C{row}", cells["healthy"], comment)
        write_cell(ws, f"D{row}", cells["malnourished"], comment)
        write_cell(ws, f"E{row}", item["p"], comment)

    not_completed = {
        22: "Mode of delivery was not completed. Codes 1 and 2 have no legend or external check identifying vaginal versus cesarean.",
        23: "Mode of delivery was not completed. One overall test would be used once the codes are identified.",
        29: "Breastfeeding problems were not completed. The column has codes 1, 2 and 3, and code 3 is too common to treat as missing or as no problem.",
        30: "Developmental problems were not completed. The 2-, 9- and 18-month columns use codes 1, 2, 3 and 4, with no legend for which codes are abnormal or how ages should be combined.",
        31: "Abnormal head circumference was not completed. Assessment codes 3 and 4 do not separate cleanly into small and large heads, and the two ages are stored separately.",
    }
    for row, reason in not_completed.items():
        for column in ("B", "C", "D", "E"):
            cell = ws[f"{column}{row}"]
            if cell.value in (None, ""):
                cell.comment = Comment(reason, "Table 1 analysis")

    profile_rows = {
        33: "wasting_moderate",
        34: "wasting_severe",
        35: "underweight_moderate",
        36: "underweight_severe",
        37: "stunting_moderate",
        38: "stunting_severe",
        39: "forms_1",
        40: "forms_2",
        41: "forms_3",
    }
    profile_comment = (
        "Denominator is the 211 children with at least one code in 1-6. "
        "Code book, taken from the dataset's own category columns and WHO-style cut-points: "
        "1 = severe low BMI, 2 = moderate low BMI, 3 = severe low weight-for-age, "
        "4 = moderate low weight-for-age, 5 = severe low length-for-age, "
        "6 = moderate low length-for-age. "
        "Wasting here is the dataset's BMI classification, not a separately calculated weight-for-height Z-score. "
        "A form is one indicator pair. Severity levels within a pair do not co-occur."
    )
    for row, key in profile_rows.items():
        write_cell(ws, f"D{row}", results["profile"][key], profile_comment)

    note_rows = {
        19: (
            "Verified decisions",
            "Rows below were added after checking the data. Rows 1–17 were left unchanged.",
        ),
        20: (
            "Source file",
            "data13.xlsx was not on disk. data-oct.xlsx Sheet1 matches the Notes fingerprint: "
            "504 unique national IDs, 293 records coded only 7, and 5 mixed 7-codes "
            "(2,7 twice; 3,5,7; 4,7; 6,7).",
        ),
        21: (
            "Groups",
            "Healthy = no code 1–6 (n = 293). Malnourished = any code 1–6 (n = 211), "
            "including the 5 mixed records. In those records the malnutrition code agrees with "
            "a low Z-score and the extra 7 does not, so 7 was treated as an erroneous extra token.",
        ),
        22: (
            "Sex",
            "1 = girl and 2 = boy. Named children in data final (1).xlsx agree, and Sheet1 counts "
            "(healthy 162 girls / 131 boys; malnourished 94 girls / 117 boys) match the Sheet2 labels. "
            "Sheet2's malnourished counts, 59 boys / 47 girls, are an incomplete summary and were not used.",
        ),
        23: (
            "Malnutrition codes",
            "The file's BMI_Category, wt_Category and ht_Category columns use codes 1–2, 3–4 and 5–6 "
            "with no exceptions at the Z cut-points ≤ −3, −3 to −2, and > −2. "
            "Those pairs never co-occur. Wasting in this table follows the BMI codes. "
            "It is not a weight-for-height Z-score.",
        ),
        24: (
            "Yes/no codes",
            "For maternal underweight, hypertension and gestational diabetes, code 1 is the positive "
            "finding and code 2 is the negative finding. This follows the column question, the low "
            "prevalence of underweight, higher glucose when diabetes = 1, and higher blood pressure "
            "when hypertension = 1. Code 3 is excluded as unresolved. Abortion uses 1 = yes and "
            "2 = no by the same instrument pattern; that item has no separate biomarker.",
        ),
        25: (
            "Left blank",
            "Mode of delivery, breastfeeding problems, developmental problems and abnormal head "
            "circumference were left blank because their codes could not be established. "
            "Planned sample sizes and TSH were not used. Invalid birth measurements were excluded "
            "and are listed in Table1_data_quality_audit.md.",
        ),
    }
    for row, (label, text) in note_rows.items():
        notes[f"A{row}"] = label
        notes[f"B{row}"] = text
        notes[f"B{row}"].alignment = Alignment(wrap_text=True, vertical="center")

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_XLSX)
    shutil.copy2(OUT_XLSX, OUT_XLSX_COPY)


def markdown_table(rows: list[list[str]]) -> str:
    header, *body = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in body)
    return "\n".join(lines)


def write_report(frame: pd.DataFrame, exclusions: dict, results: dict):
    mixed = frame.loc[
        frame["codes"].map(lambda codes: 7 in codes and len(codes & MALNUTRITION_CODES) > 0),
        ["id", "codes"],
    ]
    lines = [
        "# Table 1 data-quality and statistical audit",
        "",
        "## 1. Verified sample sizes",
        "",
        "Source used: `D:\\Projects\\AI_Predict_Patetiant\\data-oct.xlsx`, Sheet1.",
        "`data13.xlsx` was not present. This Sheet1 reproduces the workbook fingerprint exactly:",
        "504 unique `کد ملی` values, 293 records with only code 7, and 5 records mixing code 7 with codes 1–6.",
        "",
        "- Healthy: 293",
        "- Malnourished: 211",
        "- Total: 504",
        "- Duplicate national IDs: 0",
        "",
        "Group rule: a child is malnourished when the parsed `نوع سوتغذیه` value contains any of codes 1, 2, 3, 4, 5 or 6.",
        "A record whose only code is 7 is healthy. The five mixed records stay in the malnourished group.",
        "",
        "Mixed records:",
        "",
    ]
    for _, row in mixed.iterrows():
        lines.append(f"- National ID {row['id']}: codes {sorted(row['codes'])}")
    lines += [
        "",
        "Sheet2 of the same workbook labels 162 healthy girls and 131 healthy boys, which matches Sheet1.",
        "Its malnourished counts, 59 boys and 47 girls, total 106 and were not used. Sheet1 is the child-level source.",
        "The proposal counts 380 and 359 were not used.",
        "",
        "## 2. Variable-to-column mapping",
        "",
        markdown_table(
            [
                ["Table row", "Column", "Status"],
                ["Sex", "جنس", "Completed"],
                ["Age (months)", "سن کودک(ماه)", "Completed"],
                ["Birth order", "فرزند چندم", "Completed"],
                ["Gestational age", "هفته بارداری", "Completed"],
                ["Birth weight", "وزن تولد(g)", "Completed after validity screen"],
                ["Birth length", "قد زمان تولد(cm)", "Completed after validity screen"],
                ["Birth head circumference", "اندازه دور سر در بدو تولد(cm)", "Completed after validity screen"],
                ["Weight-for-age Z", "wt_birth_zscore", "Completed; supplied Z, not recalculated"],
                ["Length-for-age Z", "ht_birth_zscore", "Completed; supplied Z, not recalculated"],
                ["BMI-for-age Z", "BMI_birth_zscore", "Completed; supplied Z, not recalculated"],
                ["Maternal age", "سن مادر در زمان بارداری(سال)", "Completed"],
                ["Mode of delivery", "نوع زایمان مادر", "Not completed"],
                ["Maternal underweight", "آیا مادر سوء تغذیه کم وزنی دارد؟ (شاخص توده بدنی کمتر از 18.5)", "Completed with a documented code rule"],
                ["Hypertension", "وجود یا عدم وجود فشار خون", "Completed with a documented code rule"],
                ["Gestational diabetes", "دیابت بارداری", "Completed with a documented code rule"],
                ["Abortion", "سابقه سقط", "Completed with an instrument-level assumption"],
                ["Breastfeeding problems", "مشکل تغذیه با شیر مادر در 3-5 روزگی", "Not completed"],
                ["Developmental problems", "مشکلات تکاملی در2ماهگی; مشکلاتت تکاملی 9ماهگی; مشکلات تکاملی18ماهگی", "Not completed"],
                ["Head-circumference assessment", "ارزیابی از نظر دور سر(14-15روزگی); رزیابی از نظر دور سر(یک سالگی)", "Not completed"],
                ["Malnutrition profile", "نوع سوتغذیه", "Completed for the malnourished group"],
            ]
        ),
        "",
        "## 3. Coding schemes",
        "",
        "- Sex: 1 = girl, 2 = boy. Established from named records in `data final (1).xlsx` (فاطمه and اسرا coded 1; میکاییل, اسماعیل, کیان, بنیامین and سبحان coded 2) and from Sheet2's labeled counts matching Sheet1.",
        "- Malnutrition: 1 = BMI Z ≤ −3, 2 = −3 < BMI Z ≤ −2, 3 = weight-for-age Z ≤ −3, 4 = −3 < weight-for-age Z ≤ −2, 5 = length-for-age Z ≤ −3, 6 = −3 < length-for-age Z ≤ −2, 7 = Z > −2. Established from `BMI_Category`, `wt_Category` and `ht_Category` at 24, 36 and 48 months, where every non-missing category matched these cut-points. Pairs (1, 2), (3, 4) and (5, 6) never occur together.",
        "- Maternal underweight, hypertension and gestational diabetes: 1 = yes, 2 = no, 3 = unresolved and excluded. Evidence: underweight would otherwise be 90% if code 2 meant yes; diabetes code 1 has higher glucose in `هفته6تا10 دیابت` and `هفته24تا30 دیابت`; hypertension code 1 has higher systolic values, while code 3 is usually missing a blood-pressure value.",
        "- Abortion: 1 = yes, 2 = no. This follows the same instrument pattern. There is no biomarker for this item, so it is an explicit assumption.",
        "- Delivery, breastfeeding, development and head-circumference assessment: no code was assigned.",
        "",
        "## 4. Derived definitions",
        "",
        "- Age is the recorded `سن کودک(ماه)` value. It was not recalculated from dates. One non-numeric entry, `وو`, is missing.",
        "- Birth order uses integer values only. `1`, `2`, and `≥3` are the three table categories. Text such as `چهارقلو` or `2/دوقلو` is missing for this variable.",
        "- Birth BMI was not recalculated, and no Z-score was recalculated. The supplied birth Z columns were used after the validity screen.",
        "- Wasting in the profile is the study's BMI code, because that is what codes 1 and 2 represent. The file does not contain a weight-for-height Z-score.",
        "- Concurrent forms count distinct indicator pairs, not raw codes. One pair can contribute only one form.",
        "- Positive binary percentages use children with code 1 or 2 as the denominator. Code 3 is not counted as no.",
        "",
        "## 5. Tests and summaries",
        "",
        "A continuous variable is summarized as median [IQR] when the absolute skewness of the valid pooled values is at least 1. Otherwise it is mean ± SD. Shapiro–Wilk was not used as the deciding rule because these samples are large.",
        "Approximately symmetric variables use the independent-samples t-test when the Levene test has p ≥ 0.05, and Welch's t-test otherwise. Skewed variables use the Mann–Whitney U test.",
        "Categorical comparisons use one overall test. Pearson's chi-square is used when all expected counts are at least 5; a 2×2 table below that threshold uses Fisher's exact test.",
        "",
        markdown_table(
            [
                ["Variable", "Summary", "Skewness", "Test", "P", "Valid n (total / healthy / malnourished)"],
                ["Age", results["age"]["summary"], f"{results['age']['skew']:.2f}", results["age"]["test"], results["age"]["p"], f"{results['age']['n']['total']} / {results['age']['n']['healthy']} / {results['age']['n']['malnourished']}"],
                ["Gestational age", results["ga"]["summary"], f"{results['ga']['skew']:.2f}", results["ga"]["test"], results["ga"]["p"], f"{results['ga']['n']['total']} / {results['ga']['n']['healthy']} / {results['ga']['n']['malnourished']}"],
                ["Birth weight", results["birth_weight"]["summary"], f"{results['birth_weight']['skew']:.2f}", results["birth_weight"]["test"], results["birth_weight"]["p"], f"{results['birth_weight']['n']['total']} / {results['birth_weight']['n']['healthy']} / {results['birth_weight']['n']['malnourished']}"],
                ["Birth length", results["birth_length"]["summary"], f"{results['birth_length']['skew']:.2f}", results["birth_length"]["test"], results["birth_length"]["p"], f"{results['birth_length']['n']['total']} / {results['birth_length']['n']['healthy']} / {results['birth_length']['n']['malnourished']}"],
                ["Birth head circumference", results["birth_hc"]["summary"], f"{results['birth_hc']['skew']:.2f}", results["birth_hc"]["test"], results["birth_hc"]["p"], f"{results['birth_hc']['n']['total']} / {results['birth_hc']['n']['healthy']} / {results['birth_hc']['n']['malnourished']}"],
                ["Weight-for-age Z", results["waz"]["summary"], f"{results['waz']['skew']:.2f}", results["waz"]["test"], results["waz"]["p"], f"{results['waz']['n']['total']} / {results['waz']['n']['healthy']} / {results['waz']['n']['malnourished']}"],
                ["Length-for-age Z", results["haz"]["summary"], f"{results['haz']['skew']:.2f}", results["haz"]["test"], results["haz"]["p"], f"{results['haz']['n']['total']} / {results['haz']['n']['healthy']} / {results['haz']['n']['malnourished']}"],
                ["BMI-for-age Z", results["baz"]["summary"], f"{results['baz']['skew']:.2f}", results["baz"]["test"], results["baz"]["p"], f"{results['baz']['n']['total']} / {results['baz']['n']['healthy']} / {results['baz']['n']['malnourished']}"],
                ["Maternal age", results["maternal_age"]["summary"], f"{results['maternal_age']['skew']:.2f}", results["maternal_age"]["test"], results["maternal_age"]["p"], f"{results['maternal_age']['n']['total']} / {results['maternal_age']['n']['healthy']} / {results['maternal_age']['n']['malnourished']}"],
                ["Sex", "n (%)", "—", results["sex_test"], results["sex_p"], "504 / 293 / 211"],
                ["Birth order", "n (%)", "—", results["order_test"], results["order_p"], "see missing table"],
                ["Maternal underweight", "n (%)", "—", results["binary"]["underweight"]["test"], results["binary"]["underweight"]["p"], "known codes 1 and 2 only"],
                ["Hypertension", "n (%)", "—", results["binary"]["hypertension"]["test"], results["binary"]["hypertension"]["p"], "known codes 1 and 2 only"],
                ["Gestational diabetes", "n (%)", "—", results["binary"]["diabetes"]["test"], results["binary"]["diabetes"]["p"], "known codes 1 and 2 only"],
                ["Abortion", "n (%)", "—", results["binary"]["abortion"]["test"], results["binary"]["abortion"]["p"], "known codes 1 and 2 only"],
            ]
        ),
        "",
        "## 6. Missing and excluded observations",
        "",
        "No value was imputed. Percentages use the valid denominator for that variable and group.",
        "",
        "### Invalid measurements removed from the corresponding statistics",
        "",
    ]
    for key, label in (
        ("birth_weight", "Birth weight outside 400–6000 g"),
        ("birth_length", "Birth length outside 30–60 cm"),
        ("birth_hc", "Birth head circumference outside 25–42 cm"),
        ("age_non_numeric", "Age present but not numeric"),
        ("birth_order_unparsed", "Birth order present but not a pure number"),
    ):
        excluded = exclusions[key]
        lines.append(f"#### {label} (n = {len(excluded)})")
        lines.append("")
        if excluded.empty:
            lines.append("None.")
        else:
            for _, row in excluded.iterrows():
                values = [str(item) for item in row.tolist()]
                lines.append("- " + " | ".join(values))
        lines.append("")

    lines += [
        "Z-scores were also removed when the absolute value exceeded 8, or when the paired birth measurement was invalid.",
        "A Z-score whose raw measurement was simply missing was retained if its absolute value was 8 or less.",
        "",
        "### Missing counts for analyzed variables",
        "",
        markdown_table(
            [
                ["Variable", "Missing total", "Missing healthy", "Missing malnourished"],
                ["Age", results["age"]["n"]["missing_total"], results["age"]["n"]["missing_healthy"], results["age"]["n"]["missing_malnourished"]],
                ["Gestational age", results["ga"]["n"]["missing_total"], results["ga"]["n"]["missing_healthy"], results["ga"]["n"]["missing_malnourished"]],
                ["Birth weight", results["birth_weight"]["n"]["missing_total"], results["birth_weight"]["n"]["missing_healthy"], results["birth_weight"]["n"]["missing_malnourished"]],
                ["Birth length", results["birth_length"]["n"]["missing_total"], results["birth_length"]["n"]["missing_healthy"], results["birth_length"]["n"]["missing_malnourished"]],
                ["Birth head circumference", results["birth_hc"]["n"]["missing_total"], results["birth_hc"]["n"]["missing_healthy"], results["birth_hc"]["n"]["missing_malnourished"]],
                ["Weight-for-age Z", results["waz"]["n"]["missing_total"], results["waz"]["n"]["missing_healthy"], results["waz"]["n"]["missing_malnourished"]],
                ["Length-for-age Z", results["haz"]["n"]["missing_total"], results["haz"]["n"]["missing_healthy"], results["haz"]["n"]["missing_malnourished"]],
                ["BMI-for-age Z", results["baz"]["n"]["missing_total"], results["baz"]["n"]["missing_healthy"], results["baz"]["n"]["missing_malnourished"]],
                ["Maternal age", results["maternal_age"]["n"]["missing_total"], results["maternal_age"]["n"]["missing_healthy"], results["maternal_age"]["n"]["missing_malnourished"]],
            ]
        ),
        "",
        "Binary known-code tables are [yes healthy, yes malnourished; no healthy, no malnourished]:",
        "",
    ]
    for name in ("underweight", "hypertension", "diabetes", "abortion"):
        lines.append(f"- {name}: {results['binary'][name]['table']}")
    lines += [
        "",
        "## 7. Inconsistencies and decisions",
        "",
        "- Five records combine healthy code 7 with a malnutrition code. Four have a Z-score at or below −2 on the indicator named by the non-7 code. They remain malnourished, and the extra 7 is treated as a data-entry contradiction.",
        "- Sheet2 undercounts malnourished boys and girls by about half. Individual Sheet1 rows are the analysis population.",
        "- `data final (1).xlsx` has 598 rows, repeated national IDs, and one sex disagreement with Sheet1 (ID 2501034813). It was used only as name evidence for the sex code. Table 1 uses the 504-row Sheet1.",
        "- Birth weight values 6500 g, 20500 g and 26000 g were excluded. Lengths 22, 64, 66 and 69 cm were excluded. Head circumferences above 42 cm were excluded.",
        "- Supplied Z-scores were not replaced by a new reference calculation. The reference standard used to create them is not in the file.",
        "",
        "## 8. Not completed, and the clarification needed",
        "",
        "- Mode of delivery: which of codes 1 and 2 is vaginal, and which is cesarean?",
        "- Breastfeeding problem at days 3–5: what do codes 1, 2 and 3 mean?",
        "- Developmental assessment at 2, 9 and 18 months: what do codes 1, 2, 3 and 4 mean, and should the table count a problem at any age or at each age?",
        "- Head-circumference assessment at 14–15 days and 12 months: which codes are abnormal, and should either abnormal visit count?",
        "- Code 3 on underweight, hypertension and diabetes: is it unknown, not assessed, or another clinical state? It is currently excluded rather than called no.",
        "",
        "## 9. Profile counts among 211 malnourished children",
        "",
        markdown_table(
            [
                ["Row", "n", "Cell"],
                ["Wasting moderate (code 2)", results["profile"]["wasting_moderate_n"], results["profile"]["wasting_moderate"]],
                ["Wasting severe (code 1)", results["profile"]["wasting_severe_n"], results["profile"]["wasting_severe"]],
                ["Underweight moderate (code 4)", results["profile"]["underweight_moderate_n"], results["profile"]["underweight_moderate"]],
                ["Underweight severe (code 3)", results["profile"]["underweight_severe_n"], results["profile"]["underweight_severe"]],
                ["Stunting moderate (code 6)", results["profile"]["stunting_moderate_n"], results["profile"]["stunting_moderate"]],
                ["Stunting severe (code 5)", results["profile"]["stunting_severe_n"], results["profile"]["stunting_severe"]],
                ["Exactly 1 form", results["profile"]["forms_1_n"], results["profile"]["forms_1"]],
                ["Exactly 2 forms", results["profile"]["forms_2_n"], results["profile"]["forms_2"]],
                ["Exactly 3 forms", results["profile"]["forms_3_n"], results["profile"]["forms_3"]],
            ]
        ),
        "",
        "The three concurrent-form counts sum to 211. Indicator rows are not mutually exclusive across wasting, underweight and stunting, so those percentages are not expected to sum to 100%.",
        "",
        "## 10. Filled Table 1 values",
        "",
    ]
    display = [
        ["Row", "Total", "Healthy", "Malnourished", "P"],
        ["Sample size", str(results["n_healthy"] + results["n_malnourished"]), str(results["n_healthy"]), str(results["n_malnourished"]), "—"],
        ["Girl", results["sex"]["girl"]["total"], results["sex"]["girl"]["healthy"], results["sex"]["girl"]["malnourished"], results["sex_p"]],
        ["Boy", results["sex"]["boy"]["total"], results["sex"]["boy"]["healthy"], results["sex"]["boy"]["malnourished"], results["sex_p"]],
        ["Age", results["age"]["total"], results["age"]["healthy"], results["age"]["malnourished"], results["age"]["p"]],
        ["Birth order 1", results["order"]["1"]["total"], results["order"]["1"]["healthy"], results["order"]["1"]["malnourished"], results["order_p"]],
        ["Birth order 2", results["order"]["2"]["total"], results["order"]["2"]["healthy"], results["order"]["2"]["malnourished"], results["order_p"]],
        ["Birth order ≥3", results["order"]["3plus"]["total"], results["order"]["3plus"]["healthy"], results["order"]["3plus"]["malnourished"], results["order_p"]],
        ["Gestational age", results["ga"]["total"], results["ga"]["healthy"], results["ga"]["malnourished"], results["ga"]["p"]],
        ["Birth weight", results["birth_weight"]["total"], results["birth_weight"]["healthy"], results["birth_weight"]["malnourished"], results["birth_weight"]["p"]],
        ["Birth length", results["birth_length"]["total"], results["birth_length"]["healthy"], results["birth_length"]["malnourished"], results["birth_length"]["p"]],
        ["Birth head circumference", results["birth_hc"]["total"], results["birth_hc"]["healthy"], results["birth_hc"]["malnourished"], results["birth_hc"]["p"]],
        ["Weight-for-age Z", results["waz"]["total"], results["waz"]["healthy"], results["waz"]["malnourished"], results["waz"]["p"]],
        ["Length-for-age Z", results["haz"]["total"], results["haz"]["healthy"], results["haz"]["malnourished"], results["haz"]["p"]],
        ["BMI-for-age Z", results["baz"]["total"], results["baz"]["healthy"], results["baz"]["malnourished"], results["baz"]["p"]],
        ["Maternal age", results["maternal_age"]["total"], results["maternal_age"]["healthy"], results["maternal_age"]["malnourished"], results["maternal_age"]["p"]],
        ["Maternal underweight", results["binary"]["underweight"]["cells"]["total"], results["binary"]["underweight"]["cells"]["healthy"], results["binary"]["underweight"]["cells"]["malnourished"], results["binary"]["underweight"]["p"]],
        ["Hypertension", results["binary"]["hypertension"]["cells"]["total"], results["binary"]["hypertension"]["cells"]["healthy"], results["binary"]["hypertension"]["cells"]["malnourished"], results["binary"]["hypertension"]["p"]],
        ["Gestational diabetes", results["binary"]["diabetes"]["cells"]["total"], results["binary"]["diabetes"]["cells"]["healthy"], results["binary"]["diabetes"]["cells"]["malnourished"], results["binary"]["diabetes"]["p"]],
        ["Abortion", results["binary"]["abortion"]["cells"]["total"], results["binary"]["abortion"]["cells"]["healthy"], results["binary"]["abortion"]["cells"]["malnourished"], results["binary"]["abortion"]["p"]],
    ]
    lines.append(markdown_table(display))
    lines.append("")
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    frame, exclusions = load_analysis_frame()
    results = build_results(frame)
    populate_workbook(results)
    write_report(frame, exclusions, results)
    print("Wrote", OUT_XLSX)
    print("Wrote", OUT_XLSX_COPY)
    print("Wrote", OUT_REPORT)
    print("Age", results["age"]["total"], results["age"]["p"], results["age"]["test"])
    print("GA", results["ga"]["total"], results["ga"]["p"], results["ga"]["test"])
    print("Weight", results["birth_weight"]["total"], results["birth_weight"]["p"])
    print("Forms", results["profile"]["forms_1"], results["profile"]["forms_2"], results["profile"]["forms_3"])


if __name__ == "__main__":
    main()
