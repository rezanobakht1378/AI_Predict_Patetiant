# Table 1 data-quality and statistical audit

## 1. Verified sample sizes

Source used: `D:\Projects\AI_Predict_Patetiant\data-oct.xlsx`, Sheet1.
`data13.xlsx` was not present. This Sheet1 reproduces the workbook fingerprint exactly:
504 unique `کد ملی` values, 293 records with only code 7, and 5 records mixing code 7 with codes 1–6.

- Healthy: 293
- Malnourished: 211
- Total: 504
- Duplicate national IDs: 0

Group rule: a child is malnourished when the parsed `نوع سوتغذیه` value contains any of codes 1, 2, 3, 4, 5 or 6.
A record whose only code is 7 is healthy. The five mixed records stay in the malnourished group.

Mixed records:

- National ID 2501008839: codes [3, 5, 7]
- National ID 2501034813: codes [4, 7]
- National ID 2501042085: codes [2, 7]
- National ID 2501052374: codes [2, 7]
- National ID 2501053737: codes [6, 7]

Sheet2 of the same workbook labels 162 healthy girls and 131 healthy boys, which matches Sheet1.
Its malnourished counts, 59 boys and 47 girls, total 106 and were not used. Sheet1 is the child-level source.
The proposal counts 380 and 359 were not used.

## 2. Variable-to-column mapping

| Table row | Column | Status |
| --- | --- | --- |
| Sex | جنس | Completed |
| Age (months) | سن کودک(ماه) | Completed |
| Birth order | فرزند چندم | Completed |
| Gestational age | هفته بارداری | Completed |
| Birth weight | وزن تولد(g) | Completed after validity screen |
| Birth length | قد زمان تولد(cm) | Completed after validity screen |
| Birth head circumference | اندازه دور سر در بدو تولد(cm) | Completed after validity screen |
| Weight-for-age Z | wt_birth_zscore | Completed; supplied Z, not recalculated |
| Length-for-age Z | ht_birth_zscore | Completed; supplied Z, not recalculated |
| BMI-for-age Z | BMI_birth_zscore | Completed; supplied Z, not recalculated |
| Maternal age | سن مادر در زمان بارداری(سال) | Completed |
| Mode of delivery | نوع زایمان مادر | Not completed |
| Maternal underweight | آیا مادر سوء تغذیه کم وزنی دارد؟ (شاخص توده بدنی کمتر از 18.5) | Completed with a documented code rule |
| Hypertension | وجود یا عدم وجود فشار خون | Completed with a documented code rule |
| Gestational diabetes | دیابت بارداری | Completed with a documented code rule |
| Abortion | سابقه سقط | Completed with an instrument-level assumption |
| Breastfeeding problems | مشکل تغذیه با شیر مادر در 3-5 روزگی | Not completed |
| Developmental problems | مشکلات تکاملی در2ماهگی; مشکلاتت تکاملی 9ماهگی; مشکلات تکاملی18ماهگی | Not completed |
| Head-circumference assessment | ارزیابی از نظر دور سر(14-15روزگی); رزیابی از نظر دور سر(یک سالگی) | Not completed |
| Malnutrition profile | نوع سوتغذیه | Completed for the malnourished group |

## 3. Coding schemes

- Sex: 1 = girl, 2 = boy. Established from named records in `data final (1).xlsx` (فاطمه and اسرا coded 1; میکاییل, اسماعیل, کیان, بنیامین and سبحان coded 2) and from Sheet2's labeled counts matching Sheet1.
- Malnutrition: 1 = BMI Z ≤ −3, 2 = −3 < BMI Z ≤ −2, 3 = weight-for-age Z ≤ −3, 4 = −3 < weight-for-age Z ≤ −2, 5 = length-for-age Z ≤ −3, 6 = −3 < length-for-age Z ≤ −2, 7 = Z > −2. Established from `BMI_Category`, `wt_Category` and `ht_Category` at 24, 36 and 48 months, where every non-missing category matched these cut-points. Pairs (1, 2), (3, 4) and (5, 6) never occur together.
- Maternal underweight, hypertension and gestational diabetes: 1 = yes, 2 = no, 3 = unresolved and excluded. Evidence: underweight would otherwise be 90% if code 2 meant yes; diabetes code 1 has higher glucose in `هفته6تا10 دیابت` and `هفته24تا30 دیابت`; hypertension code 1 has higher systolic values, while code 3 is usually missing a blood-pressure value.
- Abortion: 1 = yes, 2 = no. This follows the same instrument pattern. There is no biomarker for this item, so it is an explicit assumption.
- Delivery, breastfeeding, development and head-circumference assessment: no code was assigned.

## 4. Derived definitions

- Age is the recorded `سن کودک(ماه)` value. It was not recalculated from dates. One non-numeric entry, `وو`, is missing.
- Birth order uses integer values only. `1`, `2`, and `≥3` are the three table categories. Text such as `چهارقلو` or `2/دوقلو` is missing for this variable.
- Birth BMI was not recalculated, and no Z-score was recalculated. The supplied birth Z columns were used after the validity screen.
- Codes 1 and 2 are moderate and severe low BMI-for-age. The earlier label “wasting” was incorrect for this file, which has no weight-for-height Z-score.
- Concurrent forms count distinct indicator pairs, not raw codes. One pair can contribute only one form.
- Positive binary percentages use children with code 1 or 2 as the denominator. Code 3 is not counted as no.

## 5. Tests and summaries

A continuous variable is summarized as median [IQR] when the absolute skewness of the valid pooled values is at least 1. Otherwise it is mean ± SD. Shapiro–Wilk was not used as the deciding rule because these samples are large.
Approximately symmetric variables use the independent-samples t-test when the Levene test has p ≥ 0.05, and Welch's t-test otherwise. Skewed variables use the Mann–Whitney U test.
Categorical comparisons use one overall test. Pearson's chi-square is used when all expected counts are at least 5; a 2×2 table below that threshold uses Fisher's exact test.

| Variable | Summary | Skewness | Test | P | Valid n (total / healthy / malnourished) |
| --- | --- | --- | --- | --- | --- |
| Age | mean ± SD | 0.21 | Independent-samples t-test | p < 0.001 | 503 / 293 / 210 |
| Gestational age | median [IQR] | -1.62 | Mann–Whitney U | 0.430 | 503 / 293 / 210 |
| Birth weight | mean ± SD | -0.59 | Independent-samples t-test | p < 0.001 | 500 / 292 / 208 |
| Birth length | median [IQR] | -1.72 | Mann–Whitney U | p < 0.001 | 500 / 292 / 208 |
| Birth head circumference | mean ± SD | -1.00 | Independent-samples t-test | p < 0.001 | 498 / 291 / 207 |
| Weight-for-age Z | median [IQR] | -1.07 | Mann–Whitney U | p < 0.001 | 501 / 293 / 208 |
| Length-for-age Z | mean ± SD | -0.89 | Independent-samples t-test | p < 0.001 | 495 / 292 / 203 |
| BMI-for-age Z | mean ± SD | -0.30 | Welch t-test | p < 0.001 | 496 / 292 / 204 |
| Maternal age | mean ± SD | -0.00 | Independent-samples t-test | 0.940 | 504 / 293 / 211 |
| Sex | n (%) | — | Pearson chi-square | 0.017 | 504 / 293 / 211 |
| Birth order | n (%) | — | Pearson chi-square | 0.219 | see missing table |
| Maternal underweight | n (%) | — | Pearson chi-square | 0.064 | known codes 1 and 2 only |
| Hypertension | n (%) | — | Fisher's exact test | 0.753 | known codes 1 and 2 only |
| Gestational diabetes | n (%) | — | Pearson chi-square | 0.831 | known codes 1 and 2 only |
| Abortion | n (%) | — | Pearson chi-square | 0.514 | known codes 1 and 2 only |

## 6. Missing and excluded observations

No value was imputed. Percentages use the valid denominator for that variable and group.

### Invalid measurements removed from the corresponding statistics

#### Birth weight outside 400–6000 g (n = 3)

- 2501017188 | 26000
- 2501024192 | 20500
- 6710114600 | 6500

#### Birth length outside 30–60 cm (n = 4)

- 2501017188.0 | 69.0
- 2501028139.0 | 22.0
- 2501029917.0 | 66.0
- 2501042859.0 | 64.0

#### Birth head circumference outside 25–42 cm (n = 6)

- 2501000544.0 | 48.0
- 2501013905.0 | 50.0
- 2501028139.0 | 43.0
- 2501051262.0 | 50.0
- 2501059001.0 | 54.0
- 6490192391.0 | 45.0

#### Age present but not numeric (n = 1)

- 2501013905 | وو

#### Birth order present but not a pure number (n = 6)

- 2288933151 | چهارقلو
- 2461062285 | 2/دوقلو
- 2501022475 | 4/دوقلو
- 2501022483 | 4/دوقلو
- 2501022513 | 3-3قلو
- 6490204487 | 3 دوقلو

Z-scores were also removed when the absolute value exceeded 8, or when the paired birth measurement was invalid.
A Z-score whose raw measurement was simply missing was retained if its absolute value was 8 or less.

### Missing counts for analyzed variables

| Variable | Missing total | Missing healthy | Missing malnourished |
| --- | --- | --- | --- |
| Age | 1 | 0 | 1 |
| Gestational age | 1 | 0 | 1 |
| Birth weight | 4 | 1 | 3 |
| Birth length | 4 | 1 | 3 |
| Birth head circumference | 6 | 2 | 4 |
| Weight-for-age Z | 3 | 0 | 3 |
| Length-for-age Z | 9 | 1 | 8 |
| BMI-for-age Z | 8 | 1 | 7 |
| Maternal age | 0 | 0 | 0 |

Binary known-code tables are [yes healthy, yes malnourished; no healthy, no malnourished]:

- underweight: [[23, 27], [270, 183]]
- hypertension: [[5, 5], [245, 187]]
- diabetes: [[73, 55], [184, 145]]
- abortion: [[46, 38], [245, 173]]

## 7. Inconsistencies and decisions

- Five records combine healthy code 7 with a malnutrition code. Four have a Z-score at or below −2 on the indicator named by the non-7 code. They remain malnourished, and the extra 7 is treated as a data-entry contradiction.
- Sheet2 undercounts malnourished boys and girls by about half. Individual Sheet1 rows are the analysis population.
- `data final (1).xlsx` has 598 rows, repeated national IDs, and one sex disagreement with Sheet1 (ID 2501034813). It was used only as name evidence for the sex code. Table 1 uses the 504-row Sheet1.
- Birth weight values 6500 g, 20500 g and 26000 g were excluded. Lengths 22, 64, 66 and 69 cm were excluded. Head circumferences above 42 cm were excluded.
- Supplied Z-scores were not replaced by a new reference calculation. The reference standard used to create them is not in the file.

## 8. Not completed, and the clarification needed

- Mode of delivery: which of codes 1 and 2 is vaginal, and which is cesarean?
- Breastfeeding problem at days 3–5: what do codes 1, 2 and 3 mean?
- Developmental assessment at 2, 9 and 18 months: what do codes 1, 2, 3 and 4 mean, and should the table count a problem at any age or at each age?
- Head-circumference assessment at 14–15 days and 12 months: which codes are abnormal, and should either abnormal visit count?
- Code 3 on underweight, hypertension and diabetes: is it unknown, not assessed, or another clinical state? It is currently excluded rather than called no.

## 9. Profile counts among 211 malnourished children

| Row | n | Cell |
| --- | --- | --- |
| Moderate low BMI-for-age (code 2) | 93 | 93/211 (44.1) |
| Severe low BMI-for-age (code 1) | 16 | 16/211 (7.6) |
| Underweight moderate (code 4) | 114 | 114 (54.0) |
| Underweight severe (code 3) | 15 | 15 (7.1) |
| Stunting moderate (code 6) | 82 | 82 (38.9) |
| Stunting severe (code 5) | 14 | 14 (6.6) |
| Exactly 1 form | 110 | 110 (52.1) |
| Exactly 2 forms | 79 | 79 (37.4) |
| Exactly 3 forms | 22 | 22 (10.4) |

The three concurrent-form counts sum to 211. Indicator rows are not mutually exclusive across wasting, underweight and stunting, so those percentages are not expected to sum to 100%.

## 10. Filled Table 1 values

| Row | Total | Healthy | Malnourished | P |
| --- | --- | --- | --- | --- |
| Sample size | 504 | 293 | 211 | — |
| Girl | 256 (50.8) | 162 (55.3) | 94 (44.5) | 0.017 |
| Boy | 248 (49.2) | 131 (44.7) | 117 (55.5) | 0.017 |
| Age | 39.8 ± 11.6 | 37.8 ± 11.4 | 42.7 ± 11.3 | p < 0.001 |
| Birth order 1 | 166 (33.3) | 106 (36.4) | 60 (29.0) | 0.219 |
| Birth order 2 | 189 (38.0) | 106 (36.4) | 83 (40.1) | 0.219 |
| Birth order ≥3 | 143 (28.7) | 79 (27.1) | 64 (30.9) | 0.219 |
| Gestational age | 39.0 [38.0, 39.0] | 39.0 [38.0, 39.0] | 39.0 [38.0, 39.8] | 0.430 |
| Birth weight | 2963 ± 505 | 3115 ± 459 | 2751 ± 490 | p < 0.001 |
| Birth length | 50.0 [48.0, 51.0] | 50.0 [49.0, 52.0] | 49.0 [47.0, 50.0] | p < 0.001 |
| Birth head circumference | 33.9 ± 1.6 | 34.2 ± 1.5 | 33.4 ± 1.6 | p < 0.001 |
| Weight-for-age Z | -0.60 [-1.37, -0.07] | -0.30 [-0.99, 0.20] | -0.99 [-1.73, -0.48] | p < 0.001 |
| Length-for-age Z | 0.14 ± 1.52 | 0.48 ± 1.42 | -0.34 ± 1.54 | p < 0.001 |
| BMI-for-age Z | -1.29 ± 1.47 | -1.02 ± 1.21 | -1.69 ± 1.70 | p < 0.001 |
| Maternal age | 30.9 ± 6.0 | 30.9 ± 6.2 | 30.9 ± 5.6 | 0.940 |
| Maternal underweight | 50 (9.9) | 23 (7.8) | 27 (12.9) | 0.064 |
| Hypertension | 10 (2.3) | 5 (2.0) | 5 (2.6) | 0.753 |
| Gestational diabetes | 128 (28.0) | 73 (28.4) | 55 (27.5) | 0.831 |
| Abortion | 84 (16.7) | 46 (15.8) | 38 (18.0) | 0.514 |
