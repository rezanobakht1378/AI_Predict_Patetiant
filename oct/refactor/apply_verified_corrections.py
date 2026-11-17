# -*- coding: utf-8 -*-
"""Patch a new Table 1 workbook, draw the documented participant flow, and write the change log.

Does not modify raw data, the completed Table 1 workbook, or accepted BMI values.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from openpyxl import load_workbook
from openpyxl.comments import Comment

ROOT = Path(r"D:\Projects\AI_Predict_Patetiant\oct\refactor")
SRC_XLSX = ROOT / "Table1_Study_participants_characteristics_completed.xlsx"
OUT_XLSX = ROOT / "Table1_Study_participants_characteristics_corrected.xlsx"
FIG_DIR = ROOT / "Figures_corrected"
FLOW_PNG = FIG_DIR / "Figure2_participant_flow.png"
FLOW_MMD = ROOT / "Participant_Flow_Diagram.md"


def patch_table1() -> None:
    shutil.copy2(SRC_XLSX, OUT_XLSX)
    wb = load_workbook(OUT_XLSX)
    ws = wb["Table 1"]
    labels = {
        8: "Age (months), mean ± SD",
        12: "Gestational age (weeks), median [IQR]",
        14: "Birth weight (g), mean ± SD",
        15: "Birth length (cm), median [IQR]",
        16: "Birth head circumference (cm), mean ± SD",
        17: "Weight-for-age z-score, median [IQR]",
        18: "Length-for-age z-score, mean ± SD",
        19: "BMI-for-age z-score, mean ± SD",
        21: "Maternal age during pregnancy (years), mean ± SD",
        27: "Previous pregnancy loss (source field unverified), n (%)",
        33: "Moderate low BMI-for-age, n (%)",
        34: "Severe low BMI-for-age, n (%)",
    }
    for row, label in labels.items():
        ws.cell(row, 1).value = label
    for col in range(2, 6):
        ws.cell(27, col).value = "Not analysed"
    profile = {
        33: "93/211 (44.1)",
        34: "16/211 (7.6)",
        35: "114/211 (54.0)",
        36: "15/211 (7.1)",
        37: "82/211 (38.9)",
        38: "14/211 (6.6)",
        39: "110/211 (52.1)",
        40: "79/211 (37.4)",
        41: "22/211 (10.4)",
    }
    for row, value in profile.items():
        ws.cell(row, 4).value = value
    counted = {
        6: ("256/504 (50.8)", "162/293 (55.3)", "94/211 (44.5)"),
        7: ("248/504 (49.2)", "131/293 (44.7)", "117/211 (55.5)"),
        9: ("166/498 (33.3)", "106/291 (36.4)", "60/207 (29.0)"),
        10: ("189/498 (38.0)", "106/291 (36.4)", "83/207 (40.1)"),
        11: ("143/498 (28.7)", "79/291 (27.1)", "64/207 (30.9)"),
        24: ("50/503 (9.9)", "23/293 (7.8)", "27/210 (12.9)"),
        25: ("10/442 (2.3)", "5/250 (2.0)", "5/192 (2.6)"),
        26: ("128/457 (28.0)", "73/257 (28.4)", "55/200 (27.5)"),
    }
    for row, vals in counted.items():
        for col, value in enumerate(vals, start=2):
            ws.cell(row, col).value = value
    ws.cell(43, 1).value = (
        "Continuous variables are mean ± SD or median [IQR], as labeled. Categorical variables are n/N (%), "
        "using the non-missing denominator. P values are unadjusted and describe this two-group file; they are "
        "not a prevalence estimate. Low BMI-for-age is not weight-for-height wasting. The pregnancy-loss field "
        "was not analysed. Malnutrition forms are not mutually exclusive."
    )
    ws.cell(27, 1).comment = Comment(
        "Withdrawn from the primary table. The field سابقه سقط was not verified as miscarriage, "
        "induced abortion, or any pregnancy loss, and the 1/2 coding had been inferred from other items. "
        "Earlier displayed counts are not confirmed findings.",
        "correction",
        width=300,
        height=80,
    )
    ws.cell(21, 1).comment = Comment(
        "Source field: سن مادر در زمان بارداری(سال). Recalculated from data-oct.xlsx Sheet1, "
        "ages 12–55 years, n = 504 / 293 / 211: 30.9 ± 6.0, 30.9 ± 6.2, 30.9 ± 5.6. "
        "The occasion within pregnancy is not documented. Not labeled as age at delivery.",
        "correction",
        width=300,
        height=80,
    )
    ws.cell(12, 1).comment = Comment(
        "The values were already median [IQR]. The previous row label said mean ± SD. "
        "The label was corrected. The numbers were not converted to a mean.",
        "correction",
        width=280,
        height=60,
    )
    old_note = wb["Notes"]["B23"].value
    if isinstance(old_note, str) and "Wasting in this table" in old_note:
        wb["Notes"]["B23"].value = old_note.replace(
            "Wasting in this table follows the BMI codes. It is not a weight-for-height Z-score.",
            "Codes 1 and 2 are low BMI-for-age. They are not a weight-for-height classification.",
        )
    note = wb["Notes"]
    start = note.max_row + 2
    lines = [
        (start, "Corrections applied without changing verified numbers"),
        (start + 1, "Low BMI-for-age", "Rows 33–34 were renamed from Wasting. Counts 93 (44.1) and 16 (7.6) were not changed. No weight-for-height Z-score exists."),
        (start + 2, "Gestational age", "Row 12 label changed from mean ± SD to median [IQR]. Values unchanged."),
        (start + 3, "Maternal age", "Group SDs were already 6.2 and 5.6 in this workbook. The pooled SD is 6.0. An earlier manuscript had assigned 6.0 to both groups. The field name is age during pregnancy, not age at delivery."),
        (start + 4, "Pregnancy loss", "Row 27 counts were removed from the primary table because the meaning and coding of سابقه سقط are unverified."),
        (start + 5, "Sampling", "Row 17 says growth-percentile strata. The draft says simple random sampling. Neither account was verified, so neither was selected."),
        (start + 6, "Scenario 1", "Code 7 remains the operational Healthy class. BMI values were not recalculated."),
        (start + 7, "P values", "Unadjusted comparisons in this two-group file. Not a prevalence estimate for Larestan."),
    ]
    for row, *vals in lines:
        for col, value in enumerate(vals, start=1):
            note.cell(row, col).value = value
    wb.save(OUT_XLSX)


def draw_flow() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.2, 10.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")
    boxes = [
        (1.2, 12.3, "SIB records\nInitial count: Not documented"),
        (5.6, 12.3, "Nutrition Unit records\nInitial count: Not documented"),
        (1.2, 10.0, "Healthy records selected\nCount: Not documented\nSampling method: unresolved"),
        (5.6, 10.0, "Malnourished records selected\nCount: Not documented"),
        (3.4, 7.7, "Duplicates removed: Not documented\nAge exclusions: Not documented\nCongenital-disease exclusions: Not documented"),
        (3.4, 5.2, "Analytic file\n504 rows = 504 unique children\nHealthy (code 7 only): 293\nMalnourished (any code 1–6): 211"),
        (3.4, 2.6, "Not used as flow steps\nDraft or other files cite 399, 380/359,\n282/316, and 598 rows.\nThose counts are not linked by a log."),
    ]
    for x, y, text in boxes:
        patch = FancyBboxPatch(
            (x, y), 3.6 if x != 3.4 else 4.4, 1.7,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            linewidth=0.8,
            edgecolor="#1F4E79",
            facecolor="#F3F6F9",
        )
        ax.add_patch(patch)
        ax.text(x + (1.8 if x != 3.4 else 2.2), y + 0.85, text, ha="center", va="center", fontsize=8)
    for x1, y1, x2, y2 in ((3.0, 12.3, 4.2, 9.4), (7.4, 12.3, 5.8, 9.4), (4.2, 10.0, 5.2, 9.4), (5.6, 7.7, 5.6, 6.9)):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color="#1F4E79", lw=0.8))
    ax.set_title("Participant flow. Only the final 504 children are documented counts.", fontsize=11)
    fig.tight_layout()
    fig.savefig(FLOW_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    FLOW_MMD.write_text(
        """# Participant flow

Only counts that are present in the analytic file are filled. Intermediate counts are not invented.

```mermaid
flowchart TD
    sib["SIB records<br/>Initial count: Not documented"]
    nut["Nutrition Unit records<br/>Initial count: Not documented"]
    hs["Healthy records selected<br/>Count: Not documented<br/>Method: unresolved<br/>Draft says simple random sampling<br/>Table 1 note says growth-percentile strata"]
    ms["Malnourished records selected<br/>Count: Not documented<br/>Draft mentions a 399-child file, not linked by a log"]
    ex["Duplicates removed: Not documented<br/>Age exclusions: Not documented<br/>Congenital-disease exclusions: Not documented"]
    fin["Analytic file<br/>504 rows and 504 unique children<br/>Healthy, code 7 only: 293<br/>Malnourished, any code 1-6: 211"]
    sib --> hs
    nut --> ms
    hs --> ex
    ms --> ex
    ex --> fin
```

Counts that appear in other project files and are not flow steps: 380 and 359 planned, 282 and 316 in an earlier draft, 598 rows in a working file with duplicate identifiers.

The analytic file has one row per national identifier, so the final unit is the child.
""",
        encoding="utf-8",
    )


def main() -> None:
    patch_table1()
    draw_flow()
    print("WROTE", OUT_XLSX)
    print("WROTE", FLOW_PNG)
    print("WROTE", FLOW_MMD)


if __name__ == "__main__":
    main()
