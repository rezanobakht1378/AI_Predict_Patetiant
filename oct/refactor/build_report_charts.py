# -*- coding: utf-8 -*-
"""Extra verified charts and a short descriptive report. Does not modify raw data."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

ROOT = Path(r"D:\Projects\AI_Predict_Patetiant\oct\refactor")
FIG = ROOT / "Figures_corrected"
FIG.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "Complete_Descriptive_Report.docx"

AGES = ["Birth", "6", "12", "18", "24", "36", "48"]
HAZ_H = [0.46, 0.11, 0.11, 0.10, 0.04, 0.00, 0.11]
HAZ_M = [-0.08, -0.77, -1.15, -1.48, -0.97, -1.33, -1.18]
WAZ_H = [-0.30, 0.00, 0.05, -0.03, -0.60, -0.34, -0.45]
WAZ_M = [-0.99, -1.48, -1.61, -1.75, -2.72, -2.62, -2.52]
BAZ_H = [-0.96, -0.10, 0.04, -0.10, -0.79, -0.75, -0.68]
BAZ_M = [-1.59, -1.30, -1.43, -1.36, -2.33, -2.69, -2.26]
N_H = [292, 247, 260, 241, 185, 94, 47]
N_M = [204, 181, 181, 184, 158, 97, 60]


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def save(fig, name):
    path = FIG / name
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def charts():
    x = np.arange(2)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    w = 0.36
    ax.bar(x - w / 2, [162, 131], w, label="Healthy", color="#1F4E79")
    ax.bar(x + w / 2, [94, 117], w, label="Malnourished", color="#C45911")
    ax.set_xticks(x)
    ax.set_xticklabels(["Girl", "Boy"])
    ax.set_ylabel("Children")
    ax.set_title("Sex by group")
    ax.legend(frameon=False)
    style_ax(ax)
    sex = save(fig, "Figure3_sex_by_group.png")

    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.bar(["Healthy\nn=292", "Malnourished\nn=208"], [3115, 2751], color=["#1F4E79", "#C45911"])
    ax.errorbar([0, 1], [3115, 2751], yerr=[459, 490], fmt="none", ecolor="black", capsize=4)
    ax.set_ylabel("Birth weight (g)")
    ax.set_title("Mean birth weight ± SD")
    style_ax(ax)
    bw = save(fig, "Figure4_birth_weight.png")

    x = np.arange(len(AGES))
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.bar(x - 0.18, N_H, 0.36, label="Healthy", color="#1F4E79")
    ax.bar(x + 0.18, N_M, 0.36, label="Malnourished", color="#C45911")
    ax.set_xticks(x)
    ax.set_xticklabels(AGES)
    ax.set_xlabel("Measurement age (months)")
    ax.set_ylabel("Children with a valid HAZ")
    ax.set_title("Available height-for-age scores")
    ax.legend(frameon=False)
    style_ax(ax)
    avail = save(fig, "Figure5_available_measurements.png")

    labels = [
        "Moderate underweight",
        "Moderate low BMI-for-age",
        "Moderate stunting",
        "Severe low BMI-for-age",
        "Severe underweight",
        "Severe stunting",
    ]
    counts = [114, 93, 82, 16, 15, 14]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.barh(labels[::-1], counts[::-1], color="#1F4E79")
    ax.set_xlabel("Children among the 211 malnourished")
    ax.set_title("Nutrition-unit codes, overlapping categories")
    style_ax(ax)
    profile = save(fig, "Figure6_nutrition_profile.png")

    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    ax.pie(
        [110, 79, 22],
        labels=["One form\n110", "Two forms\n79", "Three forms\n22"],
        colors=["#1F4E79", "#5B9BD5", "#C45911"],
        startangle=90,
    )
    ax.set_title("Forms recorded in the same child")
    forms = save(fig, "Figure7_concurrent_forms.png")
    return sex, bw, avail, profile, forms


def add_p(doc, text, size=12, bold=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    return p


def report(paths):
    doc = Document()
    add_p(doc, "Descriptive report of the Larestan child-growth file", size=16, bold=True)
    add_p(
        doc,
        "This report summarises the 504-child analytic file. It does not estimate prevalence or incidence, and it does not report the earlier machine-learning runs as forecasts. Healthy means code 7 only (n=293). Malnourished means any code from 1 to 6 (n=211).",
    )
    add_p(doc, "Group composition", bold=True)
    add_p(
        doc,
        "Girls were 162/293 (55.3%) of the healthy group and 94/211 (44.5%) of the malnourished group (unadjusted chi-square P=0.017). Mean birth weight, after the 400–6000 g screen, was 3115 g (SD 459, n=292) in the healthy group and 2751 g (SD 490, n=208) in the malnourished group, a difference of −364 g (95% CI −448 to −279).",
    )
    doc.add_picture(str(paths[0]), width=Inches(5.6))
    doc.add_picture(str(paths[1]), width=Inches(5.6))
    add_p(
        doc,
        "Figure 3. Sex by group. Figure 4. Mean birth weight with the standard deviation as the error bar. The error bar is the SD, not a confidence interval.",
        size=10,
    )
    add_p(doc, "Measurements available at each age", bold=True)
    add_p(
        doc,
        "Valid height-for-age scores fall from nearly the full groups at birth to 47 healthy and 60 malnourished children at 48 months. The later medians describe children who still have a measurement. They are not the path of the original 504.",
    )
    doc.add_picture(str(paths[2]), width=Inches(6.0))
    add_p(doc, "Figure 5. Children with a valid height-for-age Z-score at each age.", size=10)
    add_p(doc, "Nutrition-unit profile", bold=True)
    add_p(
        doc,
        "Among 211 malnourished children, moderate underweight was recorded in 114, moderate low BMI-for-age in 93, and moderate stunting in 82. Severe codes were less common: 16, 15, and 14. A child can carry more than one form. One form was recorded for 110 children, two forms for 79, and three forms for 22. Low BMI-for-age is not weight-for-height wasting.",
    )
    doc.add_picture(str(paths[3]), width=Inches(6.0))
    doc.add_picture(str(paths[4]), width=Inches(4.6))
    add_p(
        doc,
        "Figure 6. Overlapping nutrition-unit codes. Figure 7. Number of forms in the same child. The three slices sum to 211.",
        size=10,
    )
    add_p(doc, "What remains unresolved", bold=True)
    add_p(
        doc,
        "The healthy-group sampling method, the ethics approval, the growth reference for the stored Z-scores, and the pregnancy-loss field are not established. Age-specific median Z-scores are in Figure 1 of the corrected manuscript and in the interactive report. Prediction metrics are omitted because the earlier experiments used later measurements as predictors.",
    )
    doc.save(OUT)


if __name__ == "__main__":
    report(charts())
    print("WROTE", OUT)
