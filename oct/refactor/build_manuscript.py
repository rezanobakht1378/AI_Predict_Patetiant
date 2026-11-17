# -*- coding: utf-8 -*-
"""Build the verified manuscript, methodology audit, author queries, and Figure 1.

Reads the analytic workbook and the completed Table 1. Does not modify raw data.
Prediction metrics are diagnosed and are not reported as clinical performance.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from scipy import stats

ROOT = Path(r"D:\Projects\AI_Predict_Patetiant\oct\refactor")
DATA = Path(r"D:\Projects\AI_Predict_Patetiant\data-oct.xlsx")
TABLE1 = ROOT / "Table1_Study_participants_characteristics_completed.xlsx"
SUMMARY = Path(
    r"D:\Projects\AI_Predict_Patetiant\oct\senario2_with_previous_years_info"
    r"\results_cleaned\summary_metrics.csv"
)
BMI_VAL = Path(
    r"D:\Projects\AI_Predict_Patetiant\oct\senario2_with_previous_years_info"
    r"\results_cleaned\bmi_accuracy_validated.csv"
)
FIG_DIR = ROOT / "Figures_corrected"
FIG_PATH = FIG_DIR / "Figure1_age_specific_zscores.png"

OUT_MS = ROOT / "Malnutrition_Machine_Learning_Complete_Manuscript.docx"
OUT_AUDIT = ROOT / "Research_Methodology_Audit_updated.docx"
OUT_QUERIES = ROOT / "Author_Queries_updated.docx"

MAL_COL = "نوع سوتغذیه"
Z_LIMIT = 8.0


def parse_codes(value) -> set[int]:
    found = set()
    for part in str(value).replace("،", ",").split(","):
        token = part.strip()
        if token.isdigit():
            found.add(int(token))
    return found

HAZ = [
    ("Birth", "ht_birth_zscore"),
    ("6 months", "ht_6m_zscore"),
    ("12 months", "ht_1y_zscore"),
    ("18 months", "ht_18m_zscore"),
    ("24 months", "ht_24m_zscore"),
    ("36 months", "ht_36m_zscore"),
    ("48 months", "ht_48m_zscore"),
]
WAZ = [
    ("Birth", "wt_birth_zscore"),
    ("6 months", "wt_6m_zscore"),
    ("12 months", "wt_12m_zscore"),
    ("18 months", "wt_18m_zscore"),
    ("24 months", "wt_24m_zscore"),
    ("36 months", "wt_3y_zscore"),
    ("48 months", "wt_4y_zscore"),
]
BAZ = [
    ("Birth", "BMI_birth_zscore"),
    ("6 months", "BMI_6m_zscore"),
    ("12 months", "BMI_12m_zscore"),
    ("18 months", "BMI_18m_zscore"),
    ("24 months", "BMI_24m_zscore"),
    ("36 months", "BMI_36m_zscore"),
    ("48 months", "BMI_4y_zscore"),
]

REFERENCES = [
    "World Health Organization. Malnutrition in children. 2026. Available from: https://www.who.int/data/nutrition/nlis/info/malnutrition-in-children.",
    "Black RE, Victora CG, Walker SP, Bhutta ZA, Christian P, de Onis M, et al. Maternal and child undernutrition and overweight in low-income and middle-income countries. Lancet. 2013;382(9890):427-51.",
    "Domun T, Hone T, Garcia DC, Tadesse H, Palomares-Estrada L, Seferidi P, Laverty AA. Impacts of rising food prices on nutritional outcomes and mortality of children in low and middle-income countries: a systematic review. BMJ Glob Health. 2026;11(4).",
    "Rahman MS, Howlader T, Masud MS, Rahman ML. Association of low birth weight with malnutrition in children under five years in Bangladesh: do mother's education, socio-economic status, and birth interval matter? PLoS One. 2016;11(6):e0157814.",
    "Ijaiya MA, Anjorin S, Uthman OA. Income and education disparities in childhood malnutrition: a multi-country decomposition analysis. BMC Public Health. 2024;24(1):2882.",
    "Aghabozorgi AR, Safari S, Khadivi R. The prevalence rate of malnutrition in children younger than 5 in Iran in 2018. Int J Prev Med. 2021;12:78.",
    "Tadayyon M, Hoseini M, Rahmanian S, Abdollahzadeh P, Zahedi R. The prevalence of malnutrition in children under 6 in Southern Iran from 2018 to 2023: a population-based study. J Health Popul Nutr. 2025;44(1):4.",
    "Azizi-Soleiman F, Sharifi H, Zamanian M. Comparison of the prevalence and trend of malnutrition between 0-6 years and 7-11 years old Iranian children: a systematic review and meta-analysis. Int J Prev Med. 2020;11:182.",
    "Janssen SM, Bouzembrak Y, Tekinerdogan B. Artificial intelligence in malnutrition: a systematic literature review. Adv Nutr. 2024;15(9):100264.",
    "Wang J, He C, Long Z. Establishing a machine learning model for predicting nutritional risk through facial feature recognition. Front Nutr. 2023;10:1219193.",
    "Mahmud T, Wara TU, Joy CD. Risk factor identification and classification of malnutrition among under-five children in Bangladesh: machine learning and statistical approach. arXiv:2412.05813. 2024.",
    "Tadesse GA, Ferguson L, Robinson C, Kuria S, Wanyonyi H, Murage S, et al. Forecasting acute childhood malnutrition in Kenya using machine learning and diverse sets of indicators. PLoS One. 2025;20(5):e0322959.",
    "Rao B, Rashid M, Hasan MG, Thunga G. Machine learning in predicting child malnutrition: a meta-analysis of Demographic and Health Surveys data. Int J Environ Res Public Health. 2025;22(3).",
    "Talukder A, Ahammed B. Machine learning algorithms for predicting malnutrition among under-five children in Bangladesh. Nutrition. 2020;78:110861.",
    "Bitew FH, Sparks CS, Nyarko SH. Machine learning algorithms for predicting undernutrition among under-five children in Ethiopia. Public Health Nutr. 2022;25(2):269-80.",
    "Anku EK, Duah HO. Predicting and identifying factors associated with undernutrition among children under five years in Ghana using machine learning algorithms. PLoS One. 2024;19(2):e0296625.",
    "Hendy A, Ibrahim RK, Abdelaliem SMF, Zaher A, Alkubati SA, El-Kader RGA, Hendy A. Supervised machine learning for classification and prediction of stunting among under-five Egyptian children. BMC Pediatr. 2025;25(1):681.",
    "Islam MM, Kibria N, Kumar S, Roy DC, Karim MR. Prediction of undernutrition and identification of its influencing predictors among under-five children in Bangladesh using explainable machine learning algorithms. PLoS One. 2024;19(12):e0315393.",
]


def p_text(p: float) -> str:
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def fmt_med(series: pd.Series) -> str:
    s = series.dropna()
    if s.empty:
        return "—"
    return f"{s.median():.2f} [{s.quantile(0.25):.2f}, {s.quantile(0.75):.2f}]"


def load_groups() -> pd.DataFrame:
    df = pd.read_excel(DATA, sheet_name="Sheet1")
    codes = df[MAL_COL].map(parse_codes)
    mal = codes.map(lambda found: len(found & {1, 2, 3, 4, 5, 6}) > 0)
    df = df.copy()
    df["group"] = np.where(mal, "Malnourished", "Healthy")
    return df


def valid_z(series: pd.Series) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce")
    return x.where(x.abs() <= Z_LIMIT)


def longitudinal(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for indicator, specs in (("HAZ", HAZ), ("WAZ", WAZ), ("BAZ", BAZ)):
        for age, col in specs:
            z = valid_z(df[col])
            for group in ("Healthy", "Malnourished"):
                mask = df["group"].eq(group)
                raw_n = int(pd.to_numeric(df.loc[mask, col], errors="coerce").notna().sum())
                group_n = int(mask.sum())
                rows.append(
                    {
                        "indicator": indicator,
                        "age": age,
                        "group": group,
                        "row_type": "group",
                        "n_group": group_n,
                        "n_nonmissing_raw": raw_n,
                        "n_missing": group_n - raw_n,
                        "n_valid": int(z[mask].notna().sum()),
                        "n_excluded_extreme": int(
                            (
                                pd.to_numeric(df.loc[mask, col], errors="coerce").notna()
                                & z[mask].isna()
                            ).sum()
                        ),
                        "median": float(z[mask].median()) if z[mask].notna().any() else np.nan,
                        "q1": float(z[mask].quantile(0.25)) if z[mask].notna().any() else np.nan,
                        "q3": float(z[mask].quantile(0.75)) if z[mask].notna().any() else np.nan,
                        "test_statistic": np.nan,
                        "p": np.nan,
                    }
                )
            a = z[df["group"].eq("Healthy")].dropna()
            b = z[df["group"].eq("Malnourished")].dropna()
            if len(a) >= 5 and len(b) >= 5:
                stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            else:
                stat, p = np.nan, np.nan
            rows.append(
                {
                    "indicator": indicator,
                    "age": age,
                    "group": "Comparison",
                    "row_type": "comparison",
                    "n_group": np.nan,
                    "n_nonmissing_raw": np.nan,
                    "n_missing": np.nan,
                    "n_valid": int(len(a) + len(b)),
                    "n_excluded_extreme": np.nan,
                    "median": np.nan,
                    "q1": np.nan,
                    "q3": np.nan,
                    "test_statistic": stat,
                    "p": p,
                }
            )
    return pd.DataFrame(rows)


def cell(long_df: pd.DataFrame, indicator: str, age: str, group: str) -> str:
    r = long_df[(long_df.indicator == indicator) & (long_df.age == age) & (long_df.group == group)].iloc[0]
    return f"{r['median']:.2f} [{r['q1']:.2f}, {r['q3']:.2f}] (n={int(r['n_valid'])})"


def p_of(long_df: pd.DataFrame, indicator: str, age: str) -> str:
    r = long_df[(long_df.indicator == indicator) & (long_df.age == age) & (long_df.group == "Comparison")].iloc[0]
    return p_text(float(r["p"]))


def diagnose_models() -> dict:
    sm = pd.read_csv(SUMMARY)
    lr = sm[sm["model"].eq("LinearRegression")].copy()
    zero = int((lr["mae"] < 1e-6).sum())
    matched_cols = {
        36: {"ht_36m_zscore", "wt_3y_zscore", "BMI_36m_zscore"},
        48: {"ht_48m_zscore", "wt_4y_zscore", "BMI_4y_zscore"},
    }
    matched_parts = []
    for age, cols in matched_cols.items():
        matched_parts.append(lr[lr["target_age"].eq(age) & lr["target_col"].isin(cols)])
    future = pd.concat(matched_parts, ignore_index=True)
    if len(future) != 6 or float(future["mae"].min()) < 0.05:
        raise RuntimeError("Same-age 36/48-month linear-regression rows were not isolated correctly.")
    val = pd.read_csv(BMI_VAL)
    top = val.nlargest(10, "z_correlation")
    return {
        "n_rows": int(len(sm)),
        "n_lr": int(len(lr)),
        "n_lr_zero": zero,
        "future_mae_min": float(future["mae"].min()),
        "future_mae_max": float(future["mae"].max()),
        "future_n_min": int(future["n_samples"].min()),
        "future_n_max": int(future["n_samples"].max()),
        "top_mae_min": float(top["bmi_mae"].min()),
        "top_mae_max": float(top["bmi_mae"].max()),
        "top_acc_min": float(top["class_accuracy"].min()),
        "top_acc_max": float(top["class_accuracy"].max()),
        "top_corr_min": float(top["z_correlation"].min()),
        "top_corr_max": float(top["z_correlation"].max()),
        "top_n_min": int(top["n_samples"].min()),
        "top_n_max": int(top["n_samples"].max()),
    }


def age_summary(df: pd.DataFrame) -> dict:
    age = pd.to_numeric(df["سن کودک(ماه)"], errors="coerce")
    return {
        "n_numeric": int(age.notna().sum()),
        "n_nonnumeric": int(age.isna().sum()),
        "min": float(age.min()),
        "max": float(age.max()),
        "mean": float(age.mean()),
        "sd": float(age.std(ddof=1)),
    }


def set_run_font(run, name="Times New Roman", size=12, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


def shade_cell(cell, hex_color: str) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_cell_border(cell) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "666666")
        tcBorders.append(el)
    tcPr.append(tcBorders)


def add_p(doc, text, *, size=12, bold=False, italic=False, center=False, space_after=8, space_before=0, first_line=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing = 1.15
    if first_line is not None:
        p.paragraph_format.first_line_indent = Cm(first_line)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)
    return p


def add_h(doc, text, level):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        set_run_font(run, size=14 if level == 1 else 12, bold=True, color=(0, 0, 0))
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(6)
    return p


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.autofit = True
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = ""
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(h)
        set_run_font(run, size=9, bold=True)
        shade_cell(cell, "1F4E79")
        run.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_border(cell)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            cell.text = ""
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(str(val))
            set_run_font(run, size=8)
            if i % 2 == 1:
                shade_cell(cell, "F3F6F9")
            set_cell_border(cell)
    doc.add_paragraph()
    return table


def caption(doc, text):
    add_p(doc, text, size=10, italic=True, space_after=8, space_before=2)


def add_fig(doc, filename, width=6.2):
    path = FIG_DIR / filename
    if not path.exists():
        return
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


def make_figure(df: pd.DataFrame, long_df: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ages = [a for a, _ in HAZ]
    x = np.arange(len(ages))
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.8), sharex=True)
    colors = {"Healthy": "#1F4E79", "Malnourished": "#C45911"}
    for ax, indicator, title in zip(axes, ("HAZ", "WAZ", "BAZ"), ("Height-for-age", "Weight-for-age", "BMI-for-age")):
        for group in ("Healthy", "Malnourished"):
            sub = long_df[(long_df.indicator == indicator) & (long_df.group == group)]
            sub = sub.set_index("age").loc[ages]
            ax.plot(x, sub["median"], marker="o", color=colors[group], label=group, linewidth=1.6)
            ax.fill_between(x, sub["q1"], sub["q3"], color=colors[group], alpha=0.12)
        ax.axhline(0, color="#888888", linewidth=0.6)
        ax.axhline(-2, color="#888888", linewidth=0.6, linestyle="--")
        ax.set_title(title, fontsize=11)
        ax.set_ylabel("Z-score" if indicator == "HAZ" else "")
        tick_labels = []
        for age in ages:
            h = long_df[(long_df.indicator == indicator) & (long_df.age == age) & (long_df.group == "Healthy")].iloc[0]
            m = long_df[(long_df.indicator == indicator) & (long_df.age == age) & (long_df.group == "Malnourished")].iloc[0]
            short = "Birth" if age == "Birth" else age.replace(" months", "")
            tick_labels.append(f"{short}\n{int(h['n_valid'])}|{int(m['n_valid'])}")
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, fontsize=7)
        ax.set_ylim(-4.2, 2.2)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle(
        "Age-specific median Z-scores among children with a measurement at that age",
        fontsize=11,
        y=1.04,
    )
    fig.text(0.5, -0.02, "Numbers under each age are valid observations: healthy | malnourished", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)


def table1_rows() -> list[list[str]]:
    """Editable reproduction of the verified Table 1. Grey unpublished cells stay blank."""
    return [
        ["Sex", "", "", "", ""],
        ["Girl, n/N (%)", "256/504 (50.8)", "162/293 (55.3)", "94/211 (44.5)", "0.017"],
        ["Boy, n/N (%)", "248/504 (49.2)", "131/293 (44.7)", "117/211 (55.5)", "0.017"],
        ["Current age, months, mean ± SD", "39.8 ± 11.6", "37.8 ± 11.4", "42.7 ± 11.3", "<0.001"],
        ["Birth order", "", "", "", ""],
        ["1, n/N (%)", "166/498 (33.3)", "106/291 (36.4)", "60/207 (29.0)", "0.219"],
        ["2, n/N (%)", "189/498 (38.0)", "106/291 (36.4)", "83/207 (40.1)", "0.219"],
        ["≥3, n/N (%)", "143/498 (28.7)", "79/291 (27.1)", "64/207 (30.9)", "0.219"],
        ["Gestational age, weeks, median [IQR]", "39.0 [38.0, 39.0]", "39.0 [38.0, 39.0]", "39.0 [38.0, 39.8]", "0.430"],
        ["Birth weight, g, mean ± SD", "2963 ± 505", "3115 ± 459", "2751 ± 490", "<0.001"],
        ["Birth length, cm, median [IQR]", "50.0 [48.0, 51.0]", "50.0 [49.0, 52.0]", "49.0 [47.0, 50.0]", "<0.001"],
        ["Head circumference at birth, cm, mean ± SD", "33.9 ± 1.6", "34.2 ± 1.5", "33.4 ± 1.6", "<0.001"],
        ["Birth WAZ, median [IQR]", "−0.60 [−1.37, −0.07]", "−0.30 [−0.99, 0.20]", "−0.99 [−1.73, −0.48]", "<0.001"],
        ["Birth HAZ, mean ± SD", "0.14 ± 1.52", "0.48 ± 1.42", "−0.34 ± 1.54", "<0.001"],
        ["Birth BAZ, mean ± SD", "−1.29 ± 1.47", "−1.02 ± 1.21", "−1.69 ± 1.70", "<0.001"],
        ["Maternal age during pregnancy, years, mean ± SD", "30.9 ± 6.0", "30.9 ± 6.2", "30.9 ± 5.6", "0.940"],
        ["Maternal underweight, n/N (%)", "50/503 (9.9)", "23/293 (7.8)", "27/210 (12.9)", "0.064"],
        ["Maternal hypertension, n/N (%)", "10/442 (2.3)", "5/250 (2.0)", "5/192 (2.6)", "0.753"],
        ["Gestational diabetes, n/N (%)", "128/457 (28.0)", "73/257 (28.4)", "55/200 (27.5)", "0.831"],
        ["Previous pregnancy loss (source field unverified)", "Not analysed", "Not analysed", "Not analysed", "—"],
        ["Delivery type", "[Author query]", "[Author query]", "[Author query]", "[Author query]"],
        ["Breastfeeding problem, days 3–5", "[Author query]", "[Author query]", "[Author query]", "[Author query]"],
        ["Development at 2, 9 and 18 months", "[Author query]", "[Author query]", "[Author query]", "[Author query]"],
        ["Head-circumference assessment", "[Author query]", "[Author query]", "[Author query]", "[Author query]"],
        ["Nutritional profile of the malnourished group", "", "", "", ""],
        ["Moderate low BMI-for-age (code 2), n/N (%)", "—", "—", "93/211 (44.1)", "—"],
        ["Severe low BMI-for-age (code 1), n/N (%)", "—", "—", "16/211 (7.6)", "—"],
        ["Moderate underweight (code 4), n/N (%)", "—", "—", "114/211 (54.0)", "—"],
        ["Severe underweight (code 3), n/N (%)", "—", "—", "15/211 (7.1)", "—"],
        ["Moderate stunting (code 6), n/N (%)", "—", "—", "82/211 (38.9)", "—"],
        ["Severe stunting (code 5), n/N (%)", "—", "—", "14/211 (6.6)", "—"],
        ["One recorded form, n/N (%)", "—", "—", "110/211 (52.1)", "—"],
        ["Two recorded forms, n/N (%)", "—", "—", "79/211 (37.4)", "—"],
        ["Three recorded forms, n/N (%)", "—", "—", "22/211 (10.4)", "—"],
    ]


def long_table_rows(long_df: pd.DataFrame) -> list[list[str]]:
    rows = []
    ages = [a for a, _ in HAZ]
    for age in ages:
        row = [age]
        for indicator in ("HAZ", "WAZ", "BAZ"):
            for group in ("Healthy", "Malnourished"):
                r = long_df[(long_df.indicator == indicator) & (long_df.age == age) & (long_df.group == group)].iloc[0]
                row.append(f"{r['median']:.2f} [{r['q1']:.2f}, {r['q3']:.2f}]")
                row.append(str(int(r["n_valid"])))
            row.append(p_of(long_df, indicator, age))
        rows.append(row)
    return rows


def build_manuscript(df, long_df, ages, models) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.3)
    section.right_margin = Cm(2.3)
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)

    add_p(
        doc,
        "Anthropometric profiles of healthy and malnourished children younger than 6 years in Larestan, Iran, and an assessment of retrospective machine-learning prediction of growth Z-scores",
        size=16,
        bold=True,
        center=True,
        space_after=6,
    )
    add_p(doc, "[Author names and affiliations: Author query AQ1]", size=11, italic=True, center=True, space_after=2)
    add_p(doc, "[Corresponding author: Author query AQ1]", size=11, italic=True, center=True, space_after=10)

    add_h(doc, "Abstract", 1)
    add_p(doc, "Background", bold=True, space_after=2)
    add_p(
        doc,
        "Childhood stunting, underweight, and low BMI-for-age remain important causes of illness and impaired development. Routine growth records may contain information that could identify children whose later measurements will be low, but only if the prediction is built from information already known at the earlier visit.",
    )
    add_p(doc, "Objective", bold=True, space_after=2)
    add_p(
        doc,
        "To describe the recorded characteristics of healthy and malnourished children attending health centres affiliated with Larestan University of Medical Sciences, to compare their height-for-age, weight-for-age, and BMI-for-age Z-scores from birth to 48 months, and to determine whether the machine-learning experiments already run in this project can be reported as valid predictions of a later measurement.",
    )
    add_p(doc, "Methods", bold=True, space_after=2)
    add_p(
        doc,
        "This was a retrospective analysis of two differently sampled groups drawn from routine records. Healthy children were reported to have been sampled from the Integrated Health System (SIB), and malnourished children were taken from the Nutrition Unit file. The analytic file contains 504 children, each represented once. The healthy group was defined as records whose malnutrition field contained none of codes 1–6 (n=293). The malnourished group was defined as records containing any of codes 1–6 (n=211). Groups were compared with Student or Welch t tests, Mann–Whitney tests, or chi-square tests, according to the distribution and the variable type. Z-scores with an absolute value greater than 8 were excluded from descriptive summaries. Two prediction pipelines had been executed: classification of the next nutritional category, and regression of a later Z-score or of the change in Z-score. Their outputs were audited against the code that produced them. No new predictive performance was calculated for this manuscript.",
    )
    add_p(doc, "Results", bold=True, space_after=2)
    add_p(
        doc,
        f"Of 504 children, 293 (58.1%) were classified as healthy and 211 (41.9%) as malnourished. Current age was recorded for {ages['n_numeric']} children and ranged from {ages['min']:.0f} to {ages['max']:.0f} months. Malnourished children were older (42.7 ± 11.3 vs 37.8 ± 11.4 months), more often boys (55.5% vs 44.7%), and had lower birth weight (2751 ± 490 vs 3115 ± 459 g), birth length, head circumference, birth WAZ, birth HAZ, and birth BAZ (all P<0.001 for these anthropometric comparisons; sex P=0.017). Gestational age, birth order, maternal age, maternal underweight, hypertension, and gestational diabetes did not differ at the unadjusted 0.05 threshold. The source field for previous pregnancy loss was not analysed. Age-specific HAZ, WAZ, and BAZ distributions differed at every measured age, with lower medians in the malnourished group (Table 2, Figure 1). These profiles use the children measured at each age. Previous machine-learning runs were audited and did not establish valid predictive performance.",
    )
    add_p(doc, "Conclusion", bold=True, space_after=2)
    add_p(
        doc,
        "In this two-group sample, malnourished children already differed from healthy children in size at birth, and their Z-score distributions remained lower through 48 months. The prediction experiments do not yet support a claim that malnutrition, or a later Z-score, can be forecast before it is measured. A leakage-free, child-level analysis would be required before any clinical use is considered.",
    )
    add_p(
        doc,
        "Keywords: child malnutrition; growth; anthropometry; body-mass index; machine learning; Iran; retrospective studies",
        italic=True,
    )

    add_h(doc, "Introduction", 1)
    add_h(doc, "Background and public health importance", 2)
    add_p(
        doc,
        "Malnutrition in young children includes several anthropometric conditions that are defined separately. Low height-for-age indicates stunting, low weight-for-age indicates underweight, and low weight-for-height or low BMI-for-age is used, depending on the indicator available, to describe wasting or thinness (1). These conditions contribute to death, infection, and poorer development. Black and colleagues estimated that undernutrition, including fetal growth restriction, suboptimal breastfeeding, stunting, wasting, and vitamin A and zinc deficiency, was an underlying cause of about 45% of deaths among children younger than 5 years (2). Rising food prices have also been linked with poorer nutritional outcomes in low- and middle-income countries (3).",
    )
    add_p(
        doc,
        "The burden is uneven across households and countries. Low birth weight, maternal education, socioeconomic position, and birth interval have been associated with malnutrition in population studies such as the Bangladesh analysis of Rahman and colleagues (4). Multi-country work has likewise separated the contributions of income and education (5). Iranian reports remain relevant to the present setting. A 2018 national report gave prevalences of 8.04% for wasting, 7.63% for underweight, and 8.45% for stunting among children younger than 5 years (6). A population-based study in southern Iran covering 2018–2023 reported wasting in 7.4%, underweight in 4.9%, and stunting in 3.8% of children younger than 6 years (7). A systematic review of Iranian studies through 2017 estimated underweight at 8.4%, stunting at 14.5%, and wasting at 5.6% in children aged 0–6 years, with different figures at school age (8). These estimates come from population surveys and reviews. They are not prevalence estimates for the sample analysed here.",
    )

    add_h(doc, "Traditional growth monitoring", 2)
    add_p(
        doc,
        "Primary care usually monitors growth by weighing and measuring the child and comparing the result with a sex-specific growth reference. A Z-score below −2 is the conventional threshold for a moderate deficit, and a Z-score below −3 for a severe deficit (1). This classification is useful for clinical decisions and for surveillance, but a single threshold has two limitations. A child can move a long way toward the threshold without crossing it, and a child who has crossed it may have done so through different paths. Repeated measurements can show whether height, weight, or BMI-for-age is falling, stable, or recovering. That longitudinal information is distinct from a one-time label of stunting, underweight, or low BMI-for-age.",
    )

    add_h(doc, "Machine learning in nutritional risk assessment", 2)
    add_p(
        doc,
        "Machine-learning methods can combine many recorded variables and can represent nonlinear associations. A systematic review of artificial intelligence in malnutrition found a growing number of models, with wide variation in outcomes, predictors, and validation (9). Examples include nutritional-risk models based on facial features (10), classification of under-five malnutrition in Bangladesh (11,14,18), Ethiopia (15), and Ghana (16), a meta-analysis of Demographic and Health Survey analyses (13), and a forecasting study of acute malnutrition in Kenya that used several indicator sets (12). These studies show that algorithms can be fitted to nutritional data. They do not show that a model fitted in one health system is accurate, calibrated, or useful in another.",
    )

    add_h(doc, "Previous research", 2)
    add_p(
        doc,
        "Most of the machine-learning studies cited above are cross-sectional classification studies. They use a survey record from one visit to classify whether that same record meets a malnutrition definition. Talukder and Ahammed used Bangladesh survey data to classify under-five malnutrition (14). Bitew and colleagues did the analogous classification for undernutrition in Ethiopia (15). Anku and Duah reported classification and associated factors in Ghana (16). Islam and colleagues added explainable-machine-learning summaries to a Bangladesh classification model (18). Mahmud and colleagues reported a Bangladesh classification analysis as a preprint (11). Rao and colleagues synthesised survey-based prediction studies and found heterogeneous performance (13). Hendy and colleagues reported classification and prediction of stunting among Egyptian children younger than 5 years; the reference title concerns stunting, so the draft’s description of that study as a wasting model is not used here (17).",
    )
    add_p(
        doc,
        "These designs answer a different question from forecasting a later measurement. A model that sees the child’s current height and then classifies current stunting is reconstructing a label, not predicting the future. The Kenya study is closer to forecasting because it addresses acute malnutrition over time and uses more than one indicator set, although its population, outcome, and data system differ from a child-level clinic file in southern Iran (12). Janssen and colleagues noted the limited and uneven evidence base for artificial intelligence in malnutrition (9). Wang and colleagues’ facial-feature model is a specialised classification task and is not a growth-trajectory study (10).",
    )

    add_h(doc, "Research gap", 2)
    add_p(
        doc,
        "The cited literature leaves three gaps that this project set out to examine. First, survey classification does not use the sequence of measurements already stored in a child-health record. Second, maternal and perinatal information and later anthropometry are rarely analysed together at the level of the same child across several ages. Third, a change in Z-score between visits is not the same outcome as a cross-sectional label, and the two should not be evaluated with one mixed accuracy number. Whether the present data and code close those gaps is an empirical question, addressed in the Results rather than assumed from the aim.",
    )

    add_h(doc, "Study objectives", 2)
    add_p(
        doc,
        "The project had two analytical objectives. Objective A was to use information available at an earlier age to predict a later height, weight, or BMI-related Z-score, or the nutritional category derived from that Z-score. Objective B was to predict the change in those Z-scores between consecutive measurement ages and to flag changes of at least 0.67 Z-score units in either direction. The 0.67 threshold was a study choice used in the code. It was not treated as a validated clinical standard.",
    )
    add_p(
        doc,
        "The objectives of this manuscript are narrower, because they follow what can be verified. The primary objective is to describe the analytic sample and compare healthy and malnourished children on demographic, maternal, perinatal, and birth anthropometric variables. The secondary objective is to describe HAZ, WAZ, and BAZ from birth to 48 months in the two groups. The third objective is to state, from the implemented code and saved outputs, whether Objective A or Objective B has been evaluated in a way that can be reported as prediction. The study does not estimate incidence, and it does not test a causal effect of any maternal or child factor.",
    )

    add_h(doc, "Methods", 1)
    add_h(doc, "Study design and setting", 2)
    add_p(
        doc,
        "The study is a retrospective analysis of routinely collected child-health records. It is not a prospective cohort, and the sampling does not support an incidence estimate. Healthy and malnourished children were assembled in different ways, so the design is a two-group retrospective comparison with repeated anthropometric measurements, rather than a single random sample of the under-five population.",
    )
    add_p(
        doc,
        "The source records were reported to come from health centres affiliated with Larestan University of Medical Sciences in southern Iran. The Integrated Health System (SIB) is the national electronic system in which health centres record child care, including growth measurements. The authors’ draft states that 20 of 31 urban and rural centres were used and that records were from before 1404 in the Iranian calendar. The centre list, the start date, and the end date are not stored in the analytic file and are marked for confirmation.",
    )

    add_h(doc, "Study population and sampling", 2)
    add_p(
        doc,
        "The target population described by the investigators is children under 6 years of age covered by these health centres. In the analytic file the recorded current age runs from 22 to 61 months, so the sample is concentrated in the preschool years but is not strictly limited to 24–60 months. Historical measurements from birth onward are present for many of these children.",
    )
    add_p(
        doc,
        "Two project documents describe the healthy-group sample differently, and neither description is backed by a sampling frame or a selection log. The earlier manuscript draft says simple random sampling from SIB. A note in the Table 1 workbook says healthy children were sampled by growth-percentile strata and that the P values are therefore descriptive. The strata, their boundaries, and the number selected from each stratum are not recorded. This manuscript does not choose between those accounts. Malnourished children are described in the draft as coming from a Nutrition Unit file of 399 children, later restricted by age. That count is not linked by a log to the 211 children in the analytic file. A proposal figure of 380 healthy and 359 malnourished children, an introductory figure of 282 and 316, and a working file of 598 rows are also present. None of those counts is the analysis file.",
    )
    add_p(
        doc,
        "The file used for all numbers in this manuscript contains 504 unique national identification codes and 504 rows, with no duplicate child identifier. Applying the Scenario 1 rule below gives 293 healthy and 211 malnourished children. No screening log records how many records were identified, how many were removed as duplicates, or how many were excluded for age or congenital disease. Figure 2 therefore shows those steps as not documented. The final groups are the only counts that reconcile.",
    )
    flow = ROOT / "Figures_corrected" / "Figure2_participant_flow.png"
    if flow.exists():
        caption(doc, "Figure 2. Participant flow. Intermediate counts that were not documented are labeled as such. The final file has one row per child.")
        doc.add_picture(str(flow), width=Inches(5.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_h(doc, "Eligibility", 2)
    add_p(
        doc,
        "The draft states that children with a congenital disease affecting growth or nutrition were excluded. The conditions, the number excluded, and a data field recording the exclusion were not found. Children were not removed from the 504 because of missing later measurements. Missing Z-scores were retained as missing and were omitted only from the age-specific summary that required that Z-score. For the descriptive tables, birth weight outside 400–6000 g, birth length outside 30–60 cm, birth head circumference outside 25–42 cm, and Z-scores with absolute value greater than 8 were treated as invalid for that variable only. Three birth weights (6500 g, 20500 g, and 26000 g) and several implausible lengths and head circumferences were excluded on that basis. One current-age value was non-numeric and was omitted from the age summary.",
    )

    add_h(doc, "Data sources", 2)
    add_p(
        doc,
        "The analytic table is a wide file with one row per child. It includes demographic and maternal fields, birth measurements, and height, weight, and BMI Z-scores at later ages, together with the nutrition-unit malnutrition codes. A companion file contains names and was used only to check the sex coding against given names. It was not used as the analysis sample because it contains duplicate identifiers. No personal names or identification numbers are reported.",
    )
    add_p(
        doc,
        "Sex was coded 1 for girl and 2 for boy. This coding was checked against given names in the companion file: names such as Fatemeh and Asra were coded 1, and names such as Mikaeil, Esmaeil, Kian, Benyamin, and Sobhan were coded 2. The healthy group contained 162 girls and 131 boys, and the malnourished group contained 94 girls and 117 boys.",
    )

    add_h(doc, "Group definition", 2)
    add_p(
        doc,
        "The grouping variable is the nutrition-unit malnutrition field, not a Z-score recalculated for this manuscript. Codes were interpreted from the file’s own category columns at 24, 36, and 48 months, which matched the numerical cut-points without exception. Code 1 was BMI-for-age Z-score ≤ −3, code 2 was BMI-for-age Z-score greater than −3 and ≤ −2, code 3 was WAZ ≤ −3, code 4 was WAZ greater than −3 and ≤ −2, code 5 was HAZ ≤ −3, code 6 was HAZ greater than −3 and ≤ −2, and code 7 was a Z-score greater than −2. Codes 1 and 2 never occurred together, nor did 3 with 4, or 5 with 6.",
    )
    add_p(
        doc,
        "A child was classified as healthy when the field contained no code from 1 to 6. All 293 healthy records were code 7 only. Code 7 is the operational Healthy class for Scenario 1. The authors confirmed that definition, and it was not reclassified. Accepted BMI values were not recalculated or deleted. A child was classified as malnourished when any code from 1 to 6 was present (n=211), including five records that also contained code 7. The low-BMI codes are not weight-for-height Z-scores. No weight-for-height column was present. In this paper, codes 1 and 2 are called severe and moderate low BMI-for-age. They are not called wasting unless a weight-for-height classification is supplied. Codes 3 and 4 are severe and moderate underweight. Codes 5 and 6 are severe and moderate stunting.",
    )

    add_h(doc, "Measurements", 2)
    add_p(
        doc,
        "Current age was recorded in months. Birth order was used as an integer. Six children had a non-numeric birth-order entry, including twin and triplet text, and were omitted from the birth-order comparison only. Gestational age was recorded in weeks. Birth weight was recorded in grams, birth length and head circumference in centimetres. Maternal age was recorded in years. Maternal underweight was labelled in the file as BMI below 18.5 kg/m² and was coded 1 for yes (n=50) and 2 for no (n=453); one code 3 was left unresolved and was not counted as no. Gestational diabetes and hypertension used the same 1/2 pattern, supported by higher recorded glucose in diabetes code 1 and higher systolic pressure in hypertension code 1. Code 3 for these fields was not treated as a no. The field for previous pregnancy loss was not analysed: its clinical meaning and yes/no coding are unverified, and the coding was not inferred from the other binary items. Maternal age uses the source field for age during pregnancy; it is not described as age at delivery. The exact occasion within pregnancy is not documented. Delivery type (codes 1 and 2), breastfeeding problems on days 3–5 (codes 1–3), developmental assessments at 2, 9, and 18 months (codes 1–4 and one value of 80), and the head-circumference assessment codes were not given labels that could be checked, so they are not analysed.",
    )
    add_p(
        doc,
        "Height, weight, and BMI-related Z-scores were already present in the file at birth and at 6, 12, 18, 24, 36, and 48 months, with some ages stored under more than one column name. Weight at 36 and 48 months and BMI at 48 months were stored as wt_3y_zscore, wt_4y_zscore, and BMI_4y_zscore. Height at 12 months was stored as ht_1y_zscore. The draft states that Z-scores were calculated from WHO Child Growth Standards and also mentions CDC equations. The calculation script, the reference population, and the software used to create the stored Z-scores were not in the analysis code. A later notebook attempted to use a WHO implementation, but it applied one predicted Z-score to both height and weight through the sample mean and standard deviation. That is not a WHO calculation. This manuscript therefore treats the stored scores as precomputed Z-scores of unknown reference and does not mix WHO and CDC standards.",
    )
    add_p(
        doc,
        "BMI in the classification script was computed as weight in kilograms divided by height in metres squared. Medians of the raw columns were consistent with weight stored in grams and height stored in centimetres. Raw BMI was not used as if it were a BMI-for-age Z-score.",
    )

    add_h(doc, "Missing data and the interpolation described in the draft", 2)
    add_p(
        doc,
        "Missingness increased with age. About 107 of 504 children had a 48-month Z-score. The draft describes two imputations: linear interpolation of a missing intermediate Z-score using the surrounding measurements, and addition of the category-specific mean change from 36 to 48 months when the 48-month score was missing. Both procedures use a later measurement, or a mean estimated from children who had the later measurement, to fill an earlier gap. They are not appropriate for a prediction that is supposed to use only information known at the earlier visit.",
    )
    add_p(
        doc,
        "The file contains parallel columns named as imputations. Where both the original and the imputation column were present they agreed, and the imputation column filled some gaps. The descriptive tables in this manuscript use the original columns, with implausible values removed, and do not use the imputed columns. The Z-score notebook preferentially used a non-imputation column when both existed, but it still trained separate models on imputation columns. The classification script did not fall back to the imputation column when the original column existed. Because the draft method and the executed scripts do not do the same thing, imputation is reported as an unresolved threat to any predictive claim rather than as a completed, leakage-free preprocessing step.",
    )

    add_h(doc, "The two prediction strategies", 2)
    add_p(
        doc,
        "The descriptive comparison above is not a prediction model. The project then ran two separate prediction strategies. They do not share targets, and a result from one is not evidence for the other. Code 7 remains the Healthy label for the group comparison and for Scenario 1 of that comparison. It is not the target class inside the Z-score classifiers.",
    )
    add_p(
        doc,
        "Strategy 1 classifies the nutritional category at the next measurement. The planned windows are birth to 6 months, 6 to 12, 12 to 18, 18 to 24, 24 to 36, and 36 to 48 months. For weight, the classes are severe underweight (Z ≤ −3), underweight (−3 < Z ≤ −2), and a pooled remaining class. For height, the classes are severe short stature, short stature, and the remaining class. For BMI-for-age, the script labels the same cut-points severe low BMI-for-age and moderate low BMI-for-age; the stored output name was “weight loss,” which this report does not use. A Z-score above +2 stays in the remaining class, so overweight is not predicted separately. A missing Z-score stays missing and is dropped. It is not labeled normal.",
    )
    add_p(
        doc,
        "Strategy 1 was fitted under eight feature scenarios. S1 used baseline, raw anthropometry, and Z-scores. S2 dropped Z-scores. S3 dropped baseline fields. S4 used Z-scores only. S5 used baseline fields only. S6 used raw anthropometry only. S7 used raw anthropometry, raw BMI, and head circumference. The eighth list, named WHO growth indices, used the height, weight, and BMI Z-score columns. In the executed code these lists were then filtered by searching for an age token inside the column name. That filter did not do what the scenario names imply. Baseline columns without an age token were dropped, so the baseline-only scenario did not contain sex or the maternal fields. The token for 6 months also occurs inside 36 months, so from the 6-month window onward a later measurement could enter the predictors. The Z-score-only list and the WHO list were the same columns.",
    )
    add_p(
        doc,
        "The Strategy 1 algorithms were multinomial logistic regression, random forest, support-vector machine with a radial-basis kernel, k-nearest neighbours, a multilayer perceptron, and XGBoost classification. Class weights and random oversampling were applied on the training side of one stratified 80/20 split, random state 42. Hyperparameters were fixed in the script. They were not searched. Because each window is one row per child, that split does not place the same child on both sides of a single window. It does not remove a later measurement that the age filter has already allowed in.",
    )
    add_p(
        doc,
        "Strategy 2 predicts the continuous change Delta Z = Z at the next age minus Z at the current age, separately for height-for-age, weight-for-age, and BMI-for-age. The change is missing if either Z-score is missing. It is not imputed. The six intervals are not equal: four are 6 months and the last two, 24 to 36 months and 36 to 48 months, are 12 months. An absolute change of at least 0.67 was stored as a secondary flag for a large move in either direction. That threshold is a study choice. It is not a validated clinical standard, and the same absolute change is not the same velocity on a 6-month gap and a 12-month gap. The regression algorithms were ordinary least squares, random forest, gradient boosting, support-vector regression, a multilayer perceptron, and k-nearest neighbours. Ridge regression, elastic net, and XGBoost regression were not fitted. Forward selection by AIC and BIC was ordinary least squares on the training split only. The saved area under the curve is from a separate logistic regression fitted to the 0.67 flag. It is not the performance of the regression models.",
    )
    add_h(doc, "Objective A: later nutritional category and later Z-score", 2)
    add_p(
        doc,
        "Two implementations of Objective A were present. The first, in the classification script, predicted the next age’s nutritional class for weight, height, and BMI Z-scores. The intended windows were birth to 6 months, 6 to 12, 12 to 18, 18 to 24, 24 to 36, and 36 to 48 months. Classes were severe deficit (Z ≤ −3), moderate deficit (−3 < Z ≤ −2), and a pooled remaining class. Z-scores above +2 were placed in that remaining class, so overweight was not a separate outcome. The algorithms fitted were multinomial logistic regression, random forest, support-vector machine with an RBF kernel, k-nearest neighbours, a multilayer perceptron, and XGBoost classification. Class weights and random oversampling were applied inside the training portion of a single stratified 80/20 split with random state 42. No hyperparameter search was run.",
    )
    add_p(
        doc,
        "The second implementation, in the Z-score notebook, merged earlier age-specific tables onto the child identifier and fitted linear regression, support-vector regression, a multilayer perceptron, and XGBoost regression to predict a Z-score column. The holdout was again a single 80/20 split with random state 42. In the same experiments the notebook also scored a three-class label of the change in Z-score, using loss if the change was ≤ −0.67, gain if it was ≥ 0.67, and stable otherwise. That class accuracy is an Objective B metric and is not a measure of Z-score error.",
    )

    add_h(doc, "Objective B: change in Z-score", 2)
    add_p(
        doc,
        "A second script constructed the change in HAZ, WAZ, and BAZ between consecutive ages and fitted linear regression, random forest regression, gradient boosting, support-vector regression, a multilayer perceptron, and k-nearest-neighbour regression. The binary flag was an absolute change of at least 0.67. The interval length was 6 months for the first four windows and 12 months for 24 to 36 months and 36 to 48 months, but the interval length was not stored as a variable. Ridge regression, elastic net, and XGBoost regression were named in project discussions and were not fitted in this script. AIC and BIC forward selection was run on the training split only, using ordinary least squares. The area under the ROC curve saved for these models came from a separate logistic regression fitted to the binary flag. It was not the discrimination of the regression model’s predicted change.",
    )

    add_h(doc, "Why the predictive outputs are not used as results", 2)
    add_p(
        doc,
        "Three features of the code prevent the saved metrics from being read as forecasts. First, the classification and change-score scripts selected predictors by asking whether an age token occurred anywhere in the column name. The token for 6 months also occurs inside the token for 36 months, so from the 6-month window onward the models could see 36-month height, weight, BMI, and Z-scores. Second, the notebook did not only predict the next age. It fitted models whose target column was an earlier Z-score, a duplicate column, or an imputation column. Linear regression then reproduced that column with error indistinguishable from zero. Third, the table in the draft ranks models by correlation in a post-processing file that rebuilds height and weight from a single Z-score using the sample mean and standard deviation, then computes a BMI from those reconstructed values. That quantity is not a WHO BMI-for-age Z-score.",
    )
    add_p(
        doc,
        "Within any one age window the file has one row per child, so a random row split does not place the same child on both sides of that single window. This does not repair the use of later measurements as predictors. Near-zero-variance filtering was applied before the split in the classification script. Feature-selection candidates were taken from the leaked predictor pool. Apparently perfect fits occurred in windows where a later measurement of the same construct was available to the model. Those fits are not reported as performance.",
    )

    add_h(doc, "Statistical analysis of the descriptive objectives", 2)
    add_p(
        doc,
        "The descriptive analysis was written for this manuscript and uses the original columns only. Continuous variables were summarised as mean and standard deviation when the absolute skewness was below 1, and as median and interquartile range otherwise. Gestational age and birth length were skewed and are reported as medians. Categorical variables are counts and percentages of the non-missing values. The malnutrition profile uses the 211 malnourished children as the denominator. Categories can overlap, so the percentages of low BMI-for-age, underweight, and stunting are not expected to sum to 100%. The number of forms recorded in the same child does sum to 211.",
    )
    add_p(
        doc,
        "Groups were compared with a chi-square test for categorical variables. Fisher’s exact test was available if an expected cell was below 5; it was not required for the reported tests. For continuous variables, a t test was used when skewness was below 1, with Welch’s version when Levene’s test gave P<0.05. Otherwise a Mann–Whitney test was used. The same rule was applied to the age-specific Z-scores, which were compared by Mann–Whitney tests because the distributions were not assumed to be symmetric. The significance threshold was 0.05, two-sided, without adjustment for the number of comparisons. Analyses used Python 3.14 with pandas, NumPy, SciPy, and python-docx. Matplotlib was used for Figures 1 and 3–7.",
    )

    add_h(doc, "Ethics, software, and reporting", 2)
    add_p(
        doc,
        "The ethics committee, approval number, and consent or waiver were not present in the draft or the data files. They are requested from the authors. Identification numbers were used only to confirm that the analytic file contained one row per child and are not displayed. This paper was checked against the STROBE items for the descriptive comparison and against TRIPOD+AI items for the prediction component. It does not claim compliance with either guideline. The prediction component fails items on outcome definition, predictor timing, and validation.",
    )

    add_h(doc, "Results", 1)
    add_h(doc, "Analytic sample", 2)
    add_p(
        doc,
        f"The analytic file contained 504 children and 504 distinct identifiers. The healthy group contained 293 children (58.1%) and the malnourished group 211 (41.9%). Current age was numeric for {ages['n_numeric']} children, from {ages['min']:.0f} to {ages['max']:.0f} months (mean {ages['mean']:.1f}, SD {ages['sd']:.1f}). One age value could not be parsed. No exclusion counts for congenital disease, duplicate records, or incomplete follow-up could be added, because no flow log was stored with the file. Earlier project counts of 282, 316, 380, 359, 399, and 598 refer to other files or to planned samples and are not subgroups of this table.",
    )

    add_h(doc, "Participant characteristics", 2)
    add_p(
        doc,
        "Table 1 shows the verified comparisons. Malnourished children were older by about 5 months and were more often boys (117/211, 55.5%, compared with 131/293, 44.7%; P=0.017). Birth order was similar (P=0.219), as was gestational age (median 39 weeks in both groups; P=0.430). Size at birth differed. Mean birth weight was 2751 g (SD 490) in the malnourished group and 3115 g (SD 459) in the healthy group (P<0.001). Birth length, head circumference, WAZ, HAZ, and BAZ were also lower in the malnourished group (all P<0.001). Maternal age during pregnancy was 30.9 ± 6.0 years overall, 30.9 ± 6.2 in the healthy group, and 30.9 ± 5.6 in the malnourished group (mean difference, malnourished minus healthy, 0.04 years; 95% CI −1.02 to 1.10; P=0.940). Mean birth weight was 364 g lower in the malnourished group (95% CI −448 to −279). Maternal underweight (P=0.064), hypertension (P=0.753), and gestational diabetes (P=0.831) did not differ at the unadjusted threshold. Previous pregnancy loss was not tested. Delivery type, breastfeeding problems, developmental codes, and head-circumference assessment codes are omitted because their labels could not be verified. Figure 3 shows the sex counts. Figure 4 shows the birth-weight means. The error bars in Figure 4 are standard deviations, not confidence intervals.",
    )
    caption(doc, "Figure 3. Number of girls and boys in each group.")
    add_fig(doc, "Figure3_sex_by_group.png", 5.4)
    caption(doc, "Figure 4. Mean birth weight after excluding values outside 400–6000 g. Error bars are standard deviations.")
    add_fig(doc, "Figure4_birth_weight.png", 5.4)
    add_p(
        doc,
        "Among the 211 malnourished children, moderate low BMI-for-age was recorded in 93 (44.1%) and severe low BMI-for-age in 16 (7.6%). Moderate underweight was recorded in 114 (54.0%) and severe underweight in 15 (7.1%). Moderate stunting was recorded in 82 (38.9%) and severe stunting in 14 (6.6%). One form was recorded for 110 children (52.1%), two forms for 79 (37.4%), and three forms for 22 (10.4%). These categories come from the nutrition-unit codes. They are not a new WHO classification of every measurement age, and the low-BMI codes are not weight-for-height wasting. Figure 6 shows the overlapping codes. Figure 7 shows that the three form-counts sum to 211.",
    )
    caption(doc, "Figure 6. Nutrition-unit codes among the 211 malnourished children. A child may contribute to more than one bar.")
    add_fig(doc, "Figure6_nutrition_profile.png", 6.0)
    caption(doc, "Figure 7. Number of recorded forms in the same malnourished child. The slices sum to 211.")
    add_fig(doc, "Figure7_concurrent_forms.png", 4.4)
    caption(doc, "Table 1. Characteristics of the 504 children in the analytic file.")
    add_table(
        doc,
        ["Characteristic", "All (n=504)", "Healthy (n=293)", "Malnourished (n=211)", "P"],
        table1_rows(),
    )
    add_p(
        doc,
        "Categorical values are n/N (%), with N equal to the non-missing denominator for that variable and group. Continuous values are mean ± SD or median [IQR], as labeled. P values are unadjusted. The same P value is repeated on each row of a multi-row variable. Birth-weight denominators after the validity screen were 500, 292, and 208. Current-age denominators were 503, 293, and 210. Maternal-age denominators were 504, 293, and 211. The previous-pregnancy-loss field was not analysed. Low BMI-for-age codes are not weight-for-height wasting. Profile percentages use the 211 malnourished children as the denominator and are not mutually exclusive across indicator types. The 211/504 split is the sample composition, not the prevalence of malnutrition in Larestan.",
        size=10,
        space_after=8,
    )

    add_h(doc, "Longitudinal Z-scores", 2)
    add_p(
        doc,
        "Table 2 and Figure 1 summarise the original Z-score columns after removal of scores with absolute value greater than 8. The sample medians were lower in the malnourished group for HAZ, WAZ, and BAZ at each age from birth through 48 months. Mann–Whitney U tests of the two distributions, unadjusted for multiple comparisons or for the older age of the malnourished group, all had P<0.001. These tests are not described as tests of the medians. Figure 5 shows how many of those children contribute a height-for-age score at each age. The plotted values are age-specific profiles of children who had a measurement at that age. They are not the growth trajectories of one fixed cohort, and they are not an incidence analysis.",
    )
    add_p(
        doc,
        f"At birth, median HAZ was {cell(long_df, 'HAZ', 'Birth', 'Healthy')} in healthy children and {cell(long_df, 'HAZ', 'Birth', 'Malnourished')} in malnourished children. Median birth WAZ was {cell(long_df, 'WAZ', 'Birth', 'Healthy')} and {cell(long_df, 'WAZ', 'Birth', 'Malnourished')}. Median birth BAZ was {cell(long_df, 'BAZ', 'Birth', 'Healthy')} and {cell(long_df, 'BAZ', 'Birth', 'Malnourished')}. At 24 months, median HAZ was {cell(long_df, 'HAZ', '24 months', 'Healthy')} and {cell(long_df, 'HAZ', '24 months', 'Malnourished')}; median WAZ was {cell(long_df, 'WAZ', '24 months', 'Healthy')} and {cell(long_df, 'WAZ', '24 months', 'Malnourished')}; median BAZ was {cell(long_df, 'BAZ', '24 months', 'Healthy')} and {cell(long_df, 'BAZ', '24 months', 'Malnourished')}. By 48 months the available samples were much smaller: HAZ {cell(long_df, 'HAZ', '48 months', 'Healthy')} versus {cell(long_df, 'HAZ', '48 months', 'Malnourished')}. The lower medians in the malnourished group were already present at birth, so the later differences cannot be read as new events detected by a model.",
    )
    caption(
        doc,
        "Table 2. Median [IQR] Z-scores by group and measurement age. n is the number of valid scores. Scores with absolute value greater than 8 were excluded. P values are Mann–Whitney tests.",
    )
    # Wide table split by indicator so it remains readable.
    for indicator, label in (
        ("HAZ", "Height-for-age Z-score"),
        ("WAZ", "Weight-for-age Z-score"),
        ("BAZ", "BMI-for-age Z-score"),
    ):
        add_p(doc, label, bold=True, space_after=2)
        rows = []
        for age in [a for a, _ in HAZ]:
            h = long_df[(long_df.indicator == indicator) & (long_df.age == age) & (long_df.group == "Healthy")].iloc[0]
            m = long_df[(long_df.indicator == indicator) & (long_df.age == age) & (long_df.group == "Malnourished")].iloc[0]
            rows.append(
                [
                    age,
                    f"{h['median']:.2f} [{h['q1']:.2f}, {h['q3']:.2f}]",
                    str(int(h["n_valid"])),
                    str(int(h["n_excluded_extreme"])),
                    f"{m['median']:.2f} [{m['q1']:.2f}, {m['q3']:.2f}]",
                    str(int(m["n_valid"])),
                    str(int(m["n_excluded_extreme"])),
                    p_of(long_df, indicator, age),
                ]
            )
        add_table(
            doc,
            ["Age", "Healthy, median [IQR]", "n", "Excluded", "Malnourished, median [IQR]", "n", "Excluded", "P"],
            rows,
        )
    caption(
        doc,
        "Figure 1. Age-specific median height-for-age, weight-for-age, and BMI-for-age Z-scores. Shaded bands are interquartile ranges. The dashed line marks Z = −2. Numbers under each age are the valid observations in the healthy group and the malnourished group. The lines connect available observations at each age. They are not trajectories of the same children.",
    )
    doc.add_picture(str(FIG_PATH), width=Inches(6.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(
        doc,
        "Figure 5. Children with a valid height-for-age Z-score at each age. Weight-for-age and BMI-for-age counts differ from these bars by only a few children. The later ages are the children who still have a measurement.",
    )
    add_fig(doc, "Figure5_available_measurements.png", 6.0)

    add_h(doc, "Audit of previous machine-learning experiments", 2)
    add_p(
        doc,
        "The previous predictive experiments are reported here as an audit, not as a prediction result. No accuracy, area under the curve, R², error, or feature-importance number from those runs is given, because the runs are not valid forecasts. The classification and change-score scripts selected predictors by searching for an age token inside the column name. The token for 6 months also occurs inside the token for 36 months, so later measurements entered earlier windows. Some notebook targets were historical or duplicate columns, including imputation copies, and were therefore recoverable from the predictors. Near-zero-variance filtering was applied before the train/test split. The area under the curve stored for the change-score regression models came from a separate logistic regression fitted to a binary flag. It is not the discrimination of those regression models. The draft ranking of important features was taken from a post-processing step that rebuilt height and weight from one Z-score using the sample mean and standard deviation. That ranking is withdrawn.",
    )
    add_p(
        doc,
        "The experiments were not rerun. A valid rerun would need an explicit predictor allowlist for each milestone, exclusion of the target and of every later measurement, preprocessing fitted only inside training folds, and a child-level split. The growth reference used for the stored Z-scores is still undocumented, and the healthy-group sampling method is unresolved. Those gaps are enough to stop a new model from being presented as validated. Scenario 1 keeps the author-confirmed rule that code 7 is the Healthy class. Accepted BMI values were not recalculated or removed.",
    )

    add_h(doc, "Objective A and Objective B, kept separate", 2)
    add_p(
        doc,
        "Objective A was the attempt to predict the nutritional class at the next milestone from information available up to the index age. In Scenario 1, code 7 is the operational Healthy class and was not reclassified. Objective B was the attempt to predict the continuous change Delta Z = Z(t+1) − Z(t) for height-for-age, weight-for-age, and BMI-for-age. A flag for an absolute change of at least 0.67 was a study-specific rule, not a validated clinical threshold, and the gaps between milestones are 6 or 12 months, so the same absolute change is not the same velocity. Classification metrics were not used as the result of the regression models. Neither objective has a valid performance estimate. Counts of children with both measurements of a pair describe missingness only. They are not model performance.",
    )

    add_h(doc, "Discussion", 1)
    add_h(doc, "Principal findings", 2)
    add_p(
        doc,
        "The verifiable findings are descriptive. In a file of 504 children from Larestan health centres, the 211 children carrying a nutrition-unit malnutrition code were older, more often boys, and smaller at birth than the 293 children coded as healthy. Their median HAZ, WAZ, and BAZ remained lower at each later age, while the number of children with a measurement fell sharply after 24 months. Maternal age and the recorded maternal conditions did not separate the groups. The machine-learning pipelines were extensive, but their published-looking metrics either reproduce columns already in the model or depend on later measurements and on a post-processing step that is not a growth standard. The appropriate scientific conclusion is that the prediction objective has not been established.",
    )

    add_h(doc, "Comparison with previous studies", 2)
    add_p(
        doc,
        "The Iranian prevalence reports provide context and a reminder that moderate deficits are more common than severe ones in population data (6–8). They cannot be compared numerically with this sample, because healthy children were sampled from SIB and malnourished children were taken from a nutrition-unit list. The 41.9% malnourished share is a feature of that design, not a prevalence.",
    )
    add_p(
        doc,
        "The survey-based machine-learning studies classify a child’s current status from a cross-sectional record (11,13–16,18). Their accuracy, if valid within those surveys, answers whether the algorithm can reconstruct a label from the same interview. The present file is longitudinal in structure, which is an advantage those surveys do not have, but only if earlier visits alone are allowed to predict a later visit. That condition was not met by the executed scripts. The Kenya forecasting study is the closest in intent among the cited papers (12). Differences in setting, indicators, and validation make a side-by-side accuracy comparison uninformative, and this paper has no valid accuracy to place beside it. The Egyptian stunting study is a supervised classification of stunting, not a demonstration that wasting can be anticipated a year ahead (17).",
    )

    add_h(doc, "What the group differences can and cannot mean", 2)
    add_p(
        doc,
        "Lower birth weight, birth length, head circumference, and birth Z-scores in the malnourished group are consistent with a large literature linking small size at birth with later undernutrition (4). In this sample the differences are associations under two sampling schemes. Mothers of malnourished children were not older, and the recorded rates of underweight, hypertension, and diabetes were similar. Previous pregnancy loss was not interpreted. Those analysed maternal variables do not explain the anthropometric gap in these data. Delivery type and the developmental items could not be examined. None of the differences should be written as an effect of a maternal exposure.",
    )
    add_p(
        doc,
        "A draft table ranked birth size by its correlation with model output. That table is withdrawn with the other invalidated prediction output. Birth size is reported here only through the between-group comparisons.",
    )

    add_h(doc, "Longitudinal measurements", 2)
    add_p(
        doc,
        "The repeated Z-scores show that the group difference is not confined to a single age. They also show that much of the separation is already visible at birth. A model that uses birth size to classify children who were already identified by the nutrition unit will look successful without having predicted a future event. Claiming detection one year before clinical onset would require a cohort in which the outcome had not occurred, predictors frozen at the index visit, and evaluation in children not used to build the model. The present design does not provide that sequence.",
    )
    add_p(
        doc,
        "The 0.67 Z-score rule makes the same point in a different way. It marks a change of that size as loss, gain, or stability. Because the windows are not all the same length, a change of 0.67 over 6 months is not the same growth velocity as a change of 0.67 over 12 months. The rule was not checked against a clinical outcome such as later admission or a new diagnosis.",
    )

    add_h(doc, "Implications for services", 2)
    add_p(
        doc,
        "SIB already stores the measurements that growth monitoring requires. The descriptive results support continued attention to children who are small at birth and to children who carry a nutrition-unit code, which is existing clinical practice rather than a new algorithm. A validated model could, in principle, help clinics order follow-up when staff capacity is limited. This study does not provide that model. External validation, a prespecified time origin, calibration, and a decision analysis would be required before anyone used a score to change a visit schedule. Until then, the growth chart remains the tool that the data can support.",
    )

    add_h(doc, "Strengths", 2)
    add_p(
        doc,
        "The records are child-level and cover birth through 48 months, with maternal and perinatal fields alongside anthropometry. The malnutrition codes could be checked against the file’s own category labels and the usual −2 and −3 cut-points. Sex coding was checked against names. The analysis keeps classification, Z-score regression, and change-in-Z-score prediction apart. The sample size of 504, and the split into 293 and 211, was taken from the file rather than forced to match an earlier draft.",
    )

    add_h(doc, "Limitations", 2)
    add_p(
        doc,
        "The sampling limitation is serious. Healthy children and malnourished children did not enter through the same procedure, and the share of each group is fixed by that choice. Results do not estimate prevalence or incidence in Larestan, and they may not extend to other districts. The region is a single university catchment. Centre identifiers and study dates were not available for checking.",
    )
    add_p(
        doc,
        "The outcome definition is only partly standard. Underweight and stunting codes match WAZ and HAZ. The codes used for the thinness component match BMI-for-age, not weight-for-height. Severe and moderate labels follow −3 and −2, but the growth reference that generated the stored Z-scores was not documented. Extreme scores, including a birth WAZ above +30, a birth HAZ below −14, a birth BAZ above +55, and a 12-month BMI Z-score above 700, show that some source values are wrong. Excluding absolute values above 8 reduces their effect on the medians and does not repair the source.",
    )
    add_p(
        doc,
        "Missingness at 36 and 48 months is large. Children who remain under observation may differ from those without a later measurement. The interpolation described in the draft would fill gaps with future information. Congenital diagnoses were not listed. Several categorical fields remain uncoded. The pregnancy-loss field was left out of the primary analysis because its meaning and coding were not verified. The malnourished children were older, and the Z-score comparisons were not adjusted for age or sex. Multiple comparisons were not corrected, so isolated P values near 0.05 would have been weak evidence; the anthropometric P values were far below that level.",
    )
    add_p(
        doc,
        "The prediction limitation is decisive for any claim about early identification. Later measurements entered earlier models through the age-token filter. Duplicate and historical columns were used as targets and produced near-zero error. The draft performance table comes from an invalid reconstruction of BMI and from a selected set of rows. There was no external test set, no calibration plot, and no decision-curve analysis. A single random split does not estimate uncertainty. These problems are reasons to withhold the metrics, not footnotes to a successful model.",
    )

    add_h(doc, "Future work", 2)
    add_p(
        doc,
        "A useful next analysis would start from a documented cohort extract: every child eligible in a defined period, the date of each visit, and the Z-scores calculated with one named standard. Predictors at each index age would be restricted to columns whose measurement date is on or before that age, using an explicit allow-list rather than a text search. Missing values would be imputed inside training folds only, or left missing if the algorithm accepts missingness. Children, not rows, would define the split. Objective A and Objective B would be prespecified, with separate reports of calibration and error in Z-score units. External data from another district would be held out until the protocol was fixed. None of that work is claimed here.",
    )

    add_h(doc, "Conclusion", 1)
    add_p(
        doc,
        "This study compared 293 healthy and 211 malnourished children in routine records from health centres affiliated with Larestan University of Medical Sciences and examined whether existing machine-learning experiments could predict a later growth measurement. Malnourished children were smaller at birth and had lower height-for-age, weight-for-age, and BMI-for-age Z-scores at later recorded ages. Maternal age and the maternal conditions that could be coded did not differ between the groups. The prediction experiments were not valid forecasts: many fits reproduced information already in the predictors, and others could see a later measurement. The work documents the growth differences in this two-group sample and sets a clear requirement for any future model. It does not identify children one year before malnutrition appears, and it does not provide a tool for clinical deployment.",
    )

    add_h(doc, "Declarations", 1)
    add_h(doc, "Ethics approval and consent to participate", 2)
    add_p(
        doc,
        "[Author query AQ2. Insert the ethics committee name, the approval number, and whether consent was obtained or waived. This information was not in the manuscript draft or the analysis files. The records contain health information and national identification numbers and were analysed locally for this reconstruction.]",
    )
    add_h(doc, "Data availability", 2)
    add_p(
        doc,
        "The analytic file contains protected health information, including national identification numbers. It is not publicly available. Requests would have to be considered by the investigators and by Larestan University of Medical Sciences or the relevant health authority. [Author query AQ3 for the exact access statement they are permitted to make.]",
    )
    add_h(doc, "Funding", 2)
    add_p(doc, "[Author query AQ4. No funding statement was present in the draft.]")
    add_h(doc, "Conflict of interest", 2)
    add_p(doc, "[Author query AQ5. The authors should confirm whether any competing interests exist.]")
    add_h(doc, "Author contributions", 2)
    add_p(
        doc,
        "[Author query AQ1. CRediT roles should be completed by the authors. They were not inferred.]",
    )
    add_h(doc, "Acknowledgments", 2)
    add_p(
        doc,
        "[Author query AQ6. The draft refers to health centres affiliated with Larestan University of Medical Sciences and to the Nutrition Unit and SIB records. Named centres, data managers, and other contributors should be added only by the authors.]",
    )

    add_h(doc, "References", 1)
    for i, ref in enumerate(REFERENCES, start=1):
        add_p(doc, f"{i}. {ref}", size=11, space_after=4)

    add_h(doc, "Figure legend", 1)
    add_p(
        doc,
        "Figure 1. Median Z-scores and interquartile ranges for height-for-age, weight-for-age, and BMI-for-age from birth to 48 months, by nutrition-unit group. The dashed reference line is Z = −2. Values with absolute Z-score greater than 8 were excluded. The figure is descriptive and is not a predictive model. Figure 2. Participant flow; undocumented steps are labeled as such. Figure 3. Sex by group. Figure 4. Mean birth weight with standard-deviation bars. Figure 5. Valid height-for-age scores by age. Figure 6. Overlapping nutrition-unit codes among 211 malnourished children. Figure 7. Number of forms recorded in the same child.",
        size=11,
    )
    doc.save(OUT_MS)


def add_audit_item(doc, status, title, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(status + ". ")
    set_run_font(r, size=12, bold=True)
    r2 = p.add_run(title)
    set_run_font(r2, size=12, bold=True)
    add_p(doc, text, size=12)


def build_audit(df, ages, models) -> None:
    doc = Document()
    add_p(doc, "Research and methodology audit", size=16, bold=True, center=True)
    add_p(
        doc,
        "This audit records what the files and scripts support. It does not replace the manuscript. Classifications are Confirmed, Requires correction, Requires author clarification, or Not verifiable from available materials.",
        size=11,
        italic=True,
    )

    add_h(doc, "Research design", 1)
    add_audit_item(
        doc,
        "Confirmed",
        "The analytic object is a retrospective two-group file with repeated measurements.",
        "data-oct.xlsx, Sheet1, has 504 rows and 504 unique national identifiers. Healthy children are those whose malnutrition field has none of codes 1–6 (n=293, all code 7). Malnourished children are those with any code 1–6 (n=211). The draft’s title and conclusion describe one-year incidence prediction and detection before clinical onset. The sampling design cannot estimate incidence.",
    )
    add_audit_item(
        doc,
        "Requires correction",
        "The title, the incidence wording, and the claim of identification one year before onset.",
        "These were replaced in the manuscript with a descriptive comparison plus an explicit statement that prediction was not validly evaluated.",
    )
    add_audit_item(
        doc,
        "Requires author clarification",
        "Centre selection, study dates, and the SIB sampling fraction.",
        "The draft says 20 of 31 centres and records before 1404. Neither the centre list nor the calendar window is in the spreadsheet.",
    )
    add_audit_item(
        doc,
        "Not verifiable from available materials",
        "That the healthy sample is a simple random sample of all eligible SIB children.",
        "No sampling frame, random-number log, or inclusion file was found.",
    )

    add_h(doc, "Sample-size reconciliation", 1)
    add_audit_item(
        doc,
        "Confirmed",
        "The analysis sample is 293 healthy and 211 malnourished children, total 504.",
        "This count is the Sheet1 file. Sheet2’s malnourished sex counts are about half of Sheet1 and were not used. A proposal count of 380 and 359 was not used. data final (1).xlsx has 598 rows, duplicate identifiers, and 282 code-7 records. It is a different file.",
    )
    add_audit_item(
        doc,
        "Requires correction",
        "The introductory 282 healthy and 316 malnourished counts, and any text that treats 399 as the analysed malnourished group.",
        "399 is the draft’s description of the Nutrition Unit source file before age restriction. It is not the 211 in the analytic file. The path from 399 to 211, and from 282 to 293, is not documented.",
    )
    add_audit_item(
        doc,
        "Not verifiable from available materials",
        "A participant-flow diagram with reasons for exclusion.",
        "No exclusion dataset was found. Congenital-disease exclusions cannot be counted.",
    )

    add_h(doc, "Data source", 1)
    add_audit_item(
        doc,
        "Confirmed",
        "data13.xlsx was not in the project. data-oct.xlsx Sheet1 is the 504-child source used for Table 1 and for this manuscript.",
        "oct/data-oct.xlsx is a duplicate of that workbook. The classification script and the Z-score notebook read this wide structure. Names in the companion file were used only to check sex coding.",
    )
    add_audit_item(
        doc,
        "Confirmed",
        "Sex coding is 1 = girl and 2 = boy.",
        "Checked against given names. Healthy: 162 girls and 131 boys. Malnourished: 94 girls and 117 boys. Chi-square P = 0.017.",
    )

    add_h(doc, "Outcome definitions", 1)
    add_audit_item(
        doc,
        "Confirmed",
        "Codes 1–6 match BMI-for-age, WAZ, and HAZ cut-points at −3 and −2, using the file’s own category columns.",
        "Pairs (1,2), (3,4), and (5,6) do not co-occur. Code 7 is Z greater than −2. There is no weight-for-height column. Calling codes 1 and 2 wasting is not supported.",
    )
    add_audit_item(
        doc,
        "Requires correction",
        "Draft language that equates the group label with a fresh WHO classification of every child, and language that says weight loss for wasting.",
        "The group label is the stored nutrition-unit field. Low BMI-for-age is the term used in the manuscript.",
    )
    add_audit_item(
        doc,
        "Not verifiable from available materials",
        "Whether stored Z-scores were calculated with WHO standards, CDC references, or a mixture.",
        "Both are mentioned in the draft. The analysis code does not compute the stored scores. The notebook’s pygrowup block applies one Z-score to height and weight using the sample mean and SD. That block is invalid.",
    )

    add_h(doc, "Missing data", 1)
    add_audit_item(
        doc,
        "Confirmed",
        "Descriptive tables use original columns and drop only invalid values for that variable.",
        "Birth-weight screen 400–6000 g removed 6500, 20500, and 26000 g. Length and head-circumference screens were applied as in the Table 1 script. Z-scores with absolute value above 8 were excluded from Table 2 and Figure 1. Six non-numeric birth-order values were excluded from that row only.",
    )
    add_audit_item(
        doc,
        "Requires correction",
        "Using linear interpolation through the next measurement, or a category-specific 36-to-48-month mean change, as if it were valid preprocessing for prediction.",
        "Both use future information. Imputation columns exist and agree with originals where both are filled. They were not used for Table 1 or Table 2. The notebook still fitted models to imputation targets.",
    )
    add_audit_item(
        doc,
        "Confirmed",
        "Extreme stored Z-scores exist.",
        "Examples include birth WAZ above +30, birth HAZ below −14, birth BAZ above +55, and a 12-month BMI Z-score above 700. These indicate upstream data errors.",
    )

    add_h(doc, "Prediction framework", 1)
    add_audit_item(
        doc,
        "Confirmed",
        "Objective A and Objective B were both coded, and their metrics were saved.",
        "Objective A classification: logistic regression, random forest, SVM, k-nearest neighbours, multilayer perceptron, and XGBoost, on three-level next-age classes, eight feature scenarios, one stratified split. Objective A regression in the notebook: linear regression, SVR, MLP, and XGBoost, with a separate three-class change accuracy. Objective B: change in Z-score with threshold 0.67, fitted with linear regression, random forest, gradient boosting, SVR, MLP, and k-nearest neighbours. Ridge, elastic net, and XGBoost regression were not in that second script.",
    )
    add_audit_item(
        doc,
        "Requires correction",
        "Any table that ranks these models as successful prediction, including the draft top-ten table and the feature-correlation table.",
        "The saved metric files are invalidated preliminary output, not performance. Linear fits recovered earlier and duplicate columns. The classification script’s age filter treats the 6-month token as present inside 36 months, so later measurements enter earlier models. A draft top-ten table came from an invalid BMI reconstruction and is withdrawn. Numeric error, accuracy, and correlation from those files are retained only in this audit sentence as evidence of leakage, and they are not repeated in the manuscript Results.",
    )
    add_audit_item(
        doc,
        "Requires correction",
        "Reporting the change-model ROC-AUC as if each regressor had been evaluated on the binary flag.",
        "The saved AUC is from a separate logistic regression. All regressors in a group share one AUC. MAPE is not interpretable for Z-score changes that cross zero. The 0.67 threshold was not clinically validated in these data.",
    )

    add_h(doc, "Data leakage", 1)
    add_audit_item(
        doc,
        "Confirmed",
        "Leakage is present in the executed prediction code.",
        "Age-token substring matching admits 36-month predictors into windows from 6 months onward. Apparently perfect fits occur in those windows, including raw-measurement scenarios that contain the 36-month height or weight. Those fits are invalidated outputs, not performance estimates. The notebook’s perfect linear fits recover historical and imputation columns. AIC/BIC selection in the classification script draws from the same leaked candidate pool. Near-zero-variance filtering occurs before the train/test split.",
    )
    add_audit_item(
        doc,
        "Confirmed",
        "A row split does not duplicate a child inside one window of the current wide file.",
        "There is one row per child. This does not make the evaluation leakage-free. Grouped cross-validation was not used and would not remove the future-column problem.",
    )

    add_h(doc, "Statistical methods", 1)
    add_audit_item(
        doc,
        "Confirmed",
        "Table 1 tests match the completed workbook and an independent recomputation.",
        "Examples: sex chi-square P=0.017; age t-test P<0.001; birth weight means 2963, 3115, and 2751 g; gestational age Mann–Whitney P=0.430; birth order P=0.219. Profile counts 93, 16, 114, 15, 82, 14 and form counts 110, 79, 22 sum correctly for the overlapping and non-overlapping presentations respectively.",
    )
    add_audit_item(
        doc,
        "Requires author clarification",
        "Delivery, breastfeeding, development, and head-circumference assessment codes.",
        "Left blank. Code 3 on several maternal items was not treated as ‘no’.",
    )

    add_h(doc, "Reporting checklist", 1)
    add_p(
        doc,
        "STROBE applies to the descriptive comparison. Items that are met include setting, sample size actually analysed, variables, and statistical tests. Items that are not met include dates, eligibility flow, efforts to address bias, and adjustment for age. TRIPOD+AI applies to the prediction aim. Items that fail include predictor timing, outcome definition for the BMI post-processing, missing-data handling, internal validation, and presentation of performance. The manuscript does not claim compliance.",
    )
    add_h(doc, "Unresolved issues", 1)
    add_p(
        doc,
        "Ethics identifiers, study dates, centre list, congenital-disease exclusions, the route from the source files to 504, the growth reference, the meaning of the pregnancy-loss field, healthy-group sampling, and author roles remain open. They are listed in Author_Queries_updated.docx. Maternal-age group standard deviations were recalculated as 6.2 and 5.6. Gestational age is labeled median [IQR]. Low BMI-for-age replaces wasting in the study table. Previous predictive metrics were not carried forward. No raw data file was edited, and the models were not rerun.",
    )
    doc.save(OUT_AUDIT)


def build_queries() -> None:
    doc = Document()
    add_p(doc, "Author queries", size=16, bold=True, center=True)
    add_p(
        doc,
        "Each item is information the manuscript needs before journal submission. Please answer in the right-hand column or in a reply. Do not invent values in the manuscript until the answer is documented.",
        size=11,
        italic=True,
    )
    queries = [
        (
            "AQ1. Authors and contributions",
            "The draft file name contains a personal token, but author names, affiliations, corresponding-author details, and CRediT roles were not supplied as metadata.",
            "Needed for the title page and the contribution statement. Roles must not be guessed.",
        ),
        (
            "AQ2. Ethics approval and consent",
            "No committee name, approval number, consent statement, or waiver was found in the draft or the data files.",
            "Journals require this before review. The records are identifiable health data.",
        ),
        (
            "AQ3. Data-access wording",
            "The manuscript currently says the file is not public because it contains national identifiers and clinical data.",
            "Confirm the wording the university and health authority will allow.",
        ),
        (
            "AQ4. Funding",
            "No grant or ‘no funding’ statement was in the draft.",
            "Required by most journals.",
        ),
        (
            "AQ5. Competing interests",
            "No declaration was in the draft.",
            "Required even when the declaration is that none exist.",
        ),
        (
            "AQ6. Acknowledgments",
            "Centres, the Nutrition Unit, and SIB are mentioned in general terms.",
            "Add named centres or people only if the authors want them acknowledged.",
        ),
        (
            "AQ7. Study dates",
            "The draft says records before 1404. No start or end date is in the file.",
            "Needed for STROBE and for interpreting which growth charts and care protocols applied.",
        ),
        (
            "AQ8. Health centres",
            "The draft says 20 of 31 urban and rural centres affiliated with Larestan University of Medical Sciences.",
            "The file has no centre identifier that was used to confirm this fraction. Please supply the list and the sampling of centres.",
        ),
        (
            "AQ9. How the two groups were sampled",
            "The draft says simple random sampling from SIB for healthy children and a Nutrition Unit extract for malnourished children.",
            "The different routes change the meaning of every comparison and forbid an incidence or prevalence claim. Please confirm both protocols and whether any child could appear in both sources.",
        ),
        (
            "AQ10. Sample-size path",
            "Counts in circulation are 282 and 316, 293 and 211, a 399-child nutrition file, a proposal of 380 and 359, and a 598-row working file. The analytic file is 504 (293 and 211).",
            "Please provide the flow: initial records, exclusions, reasons, and the final groups. The manuscript will not force these counts to agree.",
        ),
        (
            "AQ11. Congenital-disease exclusions",
            "The draft says children with congenital disease affecting growth were excluded. No diagnosis list or count is in the data.",
            "Without this, the eligibility section cannot name the conditions or the number removed.",
        ),
        (
            "AQ12. Age restriction",
            "The draft says ages under 2 years were omitted because data were insufficient. Recorded current age in the analytic file runs from 22 to 61 months, while birth and infancy measurements are still present as history.",
            "Please confirm whether the restriction was on current age, and what ‘insufficient data’ meant operationally.",
        ),
        (
            "AQ13. Growth reference",
            "The draft mentions WHO standards and CDC equations. The stored Z-scores are precomputed. The notebook’s later WHO code does not implement a WHO standard correctly.",
            "Please state, for each indicator and age, the standard, the software, and whether length or height was used. If this cannot be reconstructed, the limitation stands.",
        ),
        (
            "AQ14. Wasting versus BMI-for-age",
            "Codes 1 and 2 match BMI-for-age cut-points. No weight-for-height Z-score was found.",
            "Confirm that the nutrition-unit ‘wasting’ label, if that is the local term, was assigned from BMI-for-age. The manuscript does not call these codes wasting.",
        ),
        (
            "AQ15. Delivery-type codes",
            "Codes 1 (n=206) and 2 (n=298) have no verified map to vaginal birth or caesarean section.",
            "Table 1 leaves this row blank until a codebook is supplied.",
        ),
        (
            "AQ16. Breastfeeding codes",
            "The 3–5-day breastfeeding field has codes 1, 2, and 3 (66, 285, and 152).",
            "The meanings were not established. They were not analysed.",
        ),
        (
            "AQ17. Developmental codes",
            "Assessments at 2, 9, and 18 months use codes 1–4 and one value of 80.",
            "Please provide the instrument and the meaning of each code, including whether any code denotes delay.",
        ),
        (
            "AQ18. Head-circumference assessment codes",
            "The assessment codes do not separate a clean abnormal group. Code 3 has smaller circumferences, and code 4 overlaps the normal range.",
            "Please provide the coding manual before any abnormal-head-circumference row is filled.",
        ),
        (
            "AQ19. Code 3 on maternal yes/no items",
            "Underweight, hypertension, and gestational diabetes include a code 3. Code 3 was not counted as ‘no’. For hypertension, code 3 was mostly missing blood pressure.",
            "Please define code 3. If it means ‘unknown’, the present denominators can stand.",
        ),
        (
            "AQ20. Pregnancy-loss coding",
            "The corrected manuscript does not analyse سابقه سقط. An earlier table had treated code 1 as yes and code 2 as no by analogy, and had called the field miscarriage or abortion.",
            "The row stays out of the primary analysis until the clinical meaning and the codes are confirmed from a codebook.",
        ),
        (
            "AQ21. Interpolation",
            "The draft describes linear interpolation using neighbouring measurements and a category-specific mean change from 36 to 48 months.",
            "Please confirm whether these filled values were ever used as predictors or outcomes in a result the authors still wish to report. The reconstructed manuscript does not report them as valid prediction methods.",
        ),
        (
            "AQ22. Which model, if any, the authors still wish to claim",
            "Saved metrics include perfect linear fits on historical columns, leaked 36-month predictors, and a BMI reconstruction that is not a WHO Z-score. The draft top-ten table is that reconstruction, sorted by correlation.",
            "If the authors have a different, documented, leakage-free run, please provide the script and the output. Otherwise the prediction section should remain a negative finding, as written.",
        ),
        (
            "AQ23. Feature-importance table",
            "The draft table of mean correlations, with birth length at 0.52 and a maximum of 0.995, correlates features with model predictions.",
            "It was not carried into the Results. Confirm that this is acceptable, or supply permutation importance or SHAP values from a model that cannot see the future.",
        ),
        (
            "AQ24. References that need a physical check",
            "References were kept as listed in the draft, in Vancouver style, without adding DOIs that were not already printed. Years include 2025 and 2026. The Hendy paper’s title is about stunting, whereas the draft text called it a wasting study. Aghabozorgi’s title refers to Iran in 2018; the draft text placed the same percentages in Isfahan.",
            "Please check each PDF. Do not add a DOI unless it was read from the paper. Correct the Hendy and Aghabozorgi sentences if the full texts disagree with the titles.",
        ),
        (
            "AQ25. Target journal",
            "No journal was specified. The reference list is Vancouver.",
            "If a journal is chosen, the heading levels and reference style can be adjusted. Compliance with STROBE or TRIPOD+AI is not claimed.",
        ),
    ]
    queries.extend(
        [
            (
                "AQ26. Healthy-group sampling strata",
                "The Table 1 note says healthy children were sampled by growth-percentile strata and that P values are descriptive. The draft says simple random sampling. No stratum variable, cut-points, or stratum counts were found.",
                "The sampling method changes whether the P values can be read as population comparisons.",
                "Methods, sampling; interpretation of every P value.",
                "Both accounts stay unresolved, and P values remain unadjusted descriptions of this sample.",
                "Limits interpretation. It blocks any prevalence or population-inference claim. It does not block the description of the 504-child file.",
            ),
            (
                "AQ27. Participant-flow counts",
                "Figure 2 shows initial SIB records, initial Nutrition Unit records, exclusions, and duplicate removals as not documented. Only 293, 211, and 504 are verified.",
                "A journal flow diagram cannot use guessed intermediate counts.",
                "Methods and Figure 2.",
                "The flow diagram stays incomplete.",
                "Limits reporting. It blocks a claim that the sample represents a fully enumerated cohort.",
            ),
            (
                "AQ28. Maternal-age occasion",
                "The source column is سن مادر در زمان بارداری(سال). Recalculated values are 30.9 ± 6.0 overall, 30.9 ± 6.2 healthy, and 30.9 ± 5.6 malnourished (n = 504, 293, and 211). The earlier manuscript used 6.0 for both groups and called the variable age at delivery.",
                "Age at booking and age at delivery are different variables.",
                "Table 1 and Methods.",
                "The label stays ‘during pregnancy’, following the field name, without a more precise occasion.",
                "Limits interpretation of the maternal-age comparison only.",
            ),
            (
                "AQ29. Pregnancy-loss field",
                "سابقه سقط was removed from the primary table. The earlier analysis had treated code 1 as yes and code 2 as no by analogy with other items, and had called the field miscarriage.",
                "Miscarriage and induced abortion are not interchangeable, and the coding was not verified.",
                "Table 1.",
                "The variable stays out of the primary results.",
                "Limits interpretation of that variable. It does not block the anthropometric results.",
            ),
            (
                "AQ30. Whether a leakage-free model may be rerun",
                "The stored experiments were not rerun. A valid rerun still needs a named growth reference, an explicit predictor allowlist, and a decision about the healthy-group sample.",
                "Rerunning the current scripts would repeat the leakage.",
                "Methods and Results, prediction audit.",
                "No predictive performance will be added.",
                "Blocks any claim of validated prediction. It does not block the descriptive manuscript.",
            ),
        ]
    )
    for item in queries:
        title, detail, why = item[0], item[1], item[2]
        section = item[3] if len(item) > 3 else "See the query title."
        consequence = item[4] if len(item) > 4 else "The related statement remains unresolved and is not presented as a confirmed finding."
        blocks = item[5] if len(item) > 5 else "Limits interpretation. It does not by itself block description of the 504-child file."
        add_h(doc, title, 2)
        add_p(doc, detail)
        add_p(doc, "Why it is needed: " + why, italic=True)
        add_p(doc, "Affected section: " + section, italic=True)
        add_p(doc, "If unanswered: " + consequence, italic=True)
        add_p(doc, "Status: " + blocks, italic=True)
    doc.save(OUT_QUERIES)


def main() -> None:
    df = load_groups()
    assert (df["group"] == "Healthy").sum() == 293
    assert (df["group"] == "Malnourished").sum() == 211
    long_df = longitudinal(df)
    ages = age_summary(df)
    models = diagnose_models()
    make_figure(df, long_df)
    corrected_csv = ROOT / "Table2_longitudinal_zscores_corrected.csv"
    long_df.to_csv(corrected_csv, index=False)
    print("WROTE", corrected_csv)
    build_manuscript(df, long_df, ages, models)
    build_audit(df, ages, models)
    build_queries()
    desktop = Path(r"C:\Users\CLICK\Downloads\Telegram Desktop")
    if desktop.exists():
        for src in (OUT_MS, OUT_AUDIT, OUT_QUERIES):
            shutil.copy2(src, desktop / src.name)
    print("AGE", ages)
    print("MODELS", models)
    draft = ROOT / "ML and malnutrition.v1_amanatN - Copy.docx"
    shutil.copy2(OUT_MS, draft)
    table_src = ROOT / "Table1_Study_participants_characteristics_corrected.xlsx"
    table_dst = Path(r"C:\Users\CLICK\Downloads\Telegram Desktop\Table1_Study_participants_characteristics.xlsx")
    if table_src.exists() and table_dst.parent.exists():
        shutil.copy2(table_src, table_dst)
        shutil.copy2(OUT_MS, table_dst.parent / draft.name)
        print("WROTE", table_dst)
    print("WROTE", draft)
    print("WROTE", OUT_MS)
    print("WROTE", OUT_AUDIT)
    print("WROTE", OUT_QUERIES)
    print("FIGURE", FIG_PATH)


if __name__ == "__main__":
    main()
