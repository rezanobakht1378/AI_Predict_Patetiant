# Final validation report

Status labels: PASS, PARTIAL, BLOCKED, NOT APPLICABLE.

## Checklist

| Issue | Status | Result |
| --- | --- | --- |
| Code 7 remains Healthy in Scenario 1 | PASS | Stated in the corrected manuscript and in the warning at the top of `version2.py`. No child was reclassified. Healthy n = 293, all code 7 only. |
| Accepted BMI values unchanged | PASS | BMI was not recalculated, deleted, or reclassified. |
| Wasting labels for this study’s BMI codes | PASS | Corrected workbook rows 33–34 and the manuscript table use low BMI-for-age. Counts unchanged: 93/211 and 16/211. |
| Maternal age matches across workbook and manuscript | PASS | Overall 30.9 ± 6.0, healthy 30.9 ± 6.2, malnourished 30.9 ± 5.6. Recalculated from `سن مادر در زمان بارداری(سال)`, n = 504 / 293 / 211. |
| Gestational age label matches the statistic | PASS | Label is median [IQR]. Values remain 39.0 [38.0, 39.0], 39.0 [38.0, 39.0], and 39.0 [38.0, 39.8]. |
| Maternal-age timing | PARTIAL | The label follows the source field, age during pregnancy. It is not called age at delivery. The visit within pregnancy is unresolved (AQ28). |
| Pregnancy-loss terminology | PARTIAL | Removed from the primary table and results. The clinical meaning and the 1/2 coding remain unverified (AQ20, AQ29). |
| Invalid model results not presented as performance | PASS | Results contain no accuracy, AUC, R², MAE, RMSE, or feature-importance number from the leaked runs. The section is an audit. |
| Models rerun under leakage controls | BLOCKED | Not rerun. The current scripts leak, the growth reference is undocumented, and the healthy-group sample is unresolved. A new run of the current code would not be a validation. |
| Sampling method | BLOCKED | The draft says simple random sampling. The Table 1 note says growth-percentile strata. No frame, stratum definition, or stratum count was found. Neither account was chosen (AQ26). |
| 211/504 described as prevalence | PASS | The manuscript states that this is the sample composition, not the prevalence in Larestan. |
| Participant flow reconciles to 504 | PARTIAL | Final file: 504 unique children, 293 healthy, 211 malnourished. Every earlier count is marked Not documented or listed as a count that is not a flow step. |
| Table 2 schema | PASS | Group rows hold the median. Comparison rows hold the Mann–Whitney U in `test_statistic` and the P value in `p`. The median field is empty on comparison rows. |
| Figure sample sizes and wording | PASS | Figure 1 prints valid n as healthy \| malnourished and is captioned as age-specific available observations. |
| No fabricated intermediate counts, ethics numbers, or code maps | PASS | Missing items are queries or “Not documented”. |
| P values | PASS | Unadjusted. Mann–Whitney results are described as tests of the distributions, not of the medians. Birth-weight difference −364 g (95% CI −448 to −279). Maternal-age difference 0.04 years (95% CI −1.02 to 1.10). |

## Remaining uses of “wasting”, “WHZ”, “WLZ”, and “weight-for-height”

Searched the corrected workbook, the corrected manuscript, and the project scripts.

Appropriate remaining uses:

- The introduction uses “wasting” for the general WHO concept and for published Iranian prevalence estimates (references 1, 2, 6, 7, and 8). Those sentences are about other reports, not this file’s codes.
- The manuscript says this study’s codes 1 and 2 are not called wasting and are not weight-for-height.
- `Author_Queries_updated.docx` keeps a query titled “Wasting versus BMI-for-age”, asking the authors to confirm the local nutrition-unit term.
- The corrected Notes sheet records that the rows were renamed from the old wasting label.
- No WHZ or WLZ variable was found. “Weight-for-height” appears only to say that the indicator is absent or to define the standard concept.

Not changed, and not used as results:

- The original completed workbook and the earlier manuscript still contain the old labels. They were preserved on purpose.
- Invalidated model-output files use the script label “weight loss” for low BMI Z-score classes. Those files were not relabeled and are not cited as findings.

## What was recalculated

- Maternal age mean and SD, by group, from `data-oct.xlsx` Sheet1, restricted to ages 12–55 years. Levene P = 0.19, so the equal-variance t interval was used.
- Birth-weight mean difference and 95% CI on the same validity screen as Table 1 (400–6000 g).
- Table 2 medians, quartiles, missing counts, and Mann–Whitney statistics were written to a new schema. The numeric medians were not replaced.

## Machine-learning status

Invalidated, not rerun. Objective A remains future nutritional class, with code 7 as Healthy. Objective B remains Delta Z = Z(t+1) − Z(t). The 0.67 absolute-change flag is described as a study-specific rule. Unequal 6-month and 12-month gaps are stated. No logistic AUC is attributed to a regression model.

## Blockers before journal submission

1. Ethics approval and consent or waiver (AQ2).
2. Healthy-group sampling method and, if stratified, the strata (AQ26).
3. Participant-flow counts (AQ27).
4. Growth reference used to create the stored Z-scores (AQ13).
5. A leakage-free prediction analysis, if prediction is still claimed (AQ30). Without it, the paper can proceed only as a descriptive comparison plus an audit of the failed experiments.
