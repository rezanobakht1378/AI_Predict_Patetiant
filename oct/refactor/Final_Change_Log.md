# Final change log

Original files were not overwritten. Raw data, accepted BMI values, and the Scenario 1 rule that code 7 is Healthy were not changed. The previous machine-learning scripts were not rerun.

| ID | Issue | Affected files | Correction | Automatic | Author confirmation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | Table labels called BMI-for-age codes wasting | Corrected Table 1 workbook, manuscript, Table 1 audit note, `build_table1.py` labels | Renamed to moderate and severe low BMI-for-age. Counts unchanged | Yes | No | Done |
| C02 | Maternal-age SD differed between workbook and manuscript | `data-oct.xlsx` recalculation; manuscript; workbook already had the group SDs | Healthy 30.9 ± 6.2, malnourished 30.9 ± 5.6, overall 30.9 ± 6.0. n = 293, 211, and 504. Mean difference 0.04 years, 95% CI −1.02 to 1.10 | Yes | Occasion within pregnancy remains open | Done for the numbers |
| C03 | Gestational age labeled mean ± SD while the values are a median and IQR | Corrected workbook row 12; manuscript | Label changed to median [IQR]. Numbers not converted | Yes | How gestational age was measured remains open | Done |
| C04 | Maternal age called “at delivery” in the manuscript and “at pregnancy” in the workbook | Manuscript and corrected workbook | Both now follow the source field, age during pregnancy. Not called age at delivery | Yes | Exact visit remains open | Done for the label that the field supports |
| C05 | Pregnancy-loss field analysed as miscarriage with an inferred 1/2 code | Manuscript primary table and text; corrected workbook row 27 | Removed from the primary analysis. Cells set to Not analysed | Yes | Meaning and coding remain open | Done |
| C06 | Sampling described as simple random sampling and, in the workbook note, as growth-percentile strata | Manuscript Methods; Figure 2 | Neither account was selected. The conflict is stated and queried | No | Yes | Unresolved by design |
| C07 | 211/504 could be read as prevalence | Manuscript | Stated as sample composition, not prevalence in Larestan | Yes | No | Done |
| C08 | Participant flow required counts that are not in a log | Figure 2 and `Participant_Flow_Diagram.md` | Final 504, 293, and 211 shown. Intermediate counts marked Not documented. Other file counts listed as not used | Yes | Yes, if a log exists | Done without invented counts |
| C09 | Table 2 stored the Mann–Whitney U statistic in the median field | `Table2_longitudinal_zscores_corrected.csv` | Median kept for group rows. U stored in `test_statistic`. P stored separately. Original CSV kept | Yes | No | Done |
| C10 | Figure 1 had no sample size and could be read as one cohort’s trajectory | `Figures_corrected/Figure1_age_specific_zscores.png` | Valid n for each group printed under each age. Caption says age-specific available observations | Yes | No | Done |
| C11 | Previous model metrics could be quoted as performance | `Manuscript_corrected.docx` Results | Metrics removed from Results. Runs described as an invalidated audit. Models not rerun | Yes | A leakage-free rerun would need a new decision | Done |
| C12 | Objective A and Objective B were at risk of being merged | Manuscript Methods and Results | Separate definitions kept. Code 7 stated as the Scenario 1 Healthy class. Delta Z defined as Z(t+1) − Z(t). Logistic AUC not reported as a regression result | Yes | No | Done |
| C13 | Categorical cells did not show the denominator | Manuscript Table 1 and corrected workbook | Format changed to n/N (%) using the same numerators | Yes | No | Done |
| C14 | Mann–Whitney tests were easy to read as tests of medians | Manuscript Results | Described as tests of the distributions. P values called unadjusted | Yes | No | Done |
| C15 | Birth-weight contrast had no interval | Manuscript Results | Malnourished minus healthy −364 g, 95% CI −448 to −279 | Yes | No | Done |

Files created:

- `Table1_Study_participants_characteristics_corrected.xlsx`
- `Table2_longitudinal_zscores_corrected.csv`
- `Manuscript_corrected.docx`
- `Author_Queries_updated.docx`
- `Research_Methodology_Audit_updated.docx`
- `Participant_Flow_Diagram.md`
- `Figures_corrected/Figure1_age_specific_zscores.png`
- `Figures_corrected/Figure2_participant_flow.png`
- `apply_verified_corrections.py`
- `Final_Change_Log.md`
- `Final_Validation_Report.md`

`build_manuscript.py` now writes the corrected manuscript, audit, queries, figure, and Table 2. `version2.py` received a warning comment only. Its calculations were not changed and it was not executed.
