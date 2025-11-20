import pandas as pd
import os

# === 1️⃣ Read main CSV ===
input_file = "data-oct.csv"  # change this to your filename
df = pd.read_csv(input_file)

# === 2️⃣ Define patient_info columns (used in all exports) ===
patient_info = [
    "birth_date", "national_id", "gender", "malnutrition_type", "age_months",
    "birth_order", "mother_age_pregnancy", "delivery_type",
    "mother_underweight", "mother_hypertension",
    "week_24_30", "week_31_34", "week_36_37",
    "abortion_history", "gestational_weeks", "gestational_diabetes",
    "diabetes_6_10w", "diabetes_24_30w",
    "dev_issues_2m", "dev_issues_9m", "dev_issues_18m",
    "breastfeeding_issue_3_5d",
    "headcirc_birth_cm", "headcirc_15d_cm", "headcirc_1y_cm",
    "headcirc_eval_15d", "headcirc_eval_1y"
]

# === 3️⃣ Define per-year growth columns ===
groups = {
    "birth": [
        "BMI_birth_zscore", "height_birth_cm", "ht_birth_zscore",
        "weight_birth_g", "wt_birth_zscore"
    ],
    "6m": [
        "BMI_6m_zscore", "BMI_6m_zscore_Imputation", "BMI_DeltaZ = Z12 − Zbirth",
        "height_6m_cm", "ht_6m_zscore", "ht_6m_zscore_Imputation", "ht_DeltaZ = Z12 − Zbirth",
        "weight_6m_g", "wt_6m_zscore", "wt_6m_zscore_Imputation", "wt_DeltaZ = Z12 − Zbirth"
    ],
    "12m": [
        "BMI_12m_zscore", "BMI_12m_zscore_Imputation", "BMI_DeltaZ = Z12 − Z0",
        "BMI_DeltaZ_Category", "BMI_DeltaZ = Z18− Z6",
        "height_12m_cm", "ht_1y_zscore", "ht_12m_zscore_Imputation",
        "ht_DeltaZ = Z12 − Z0", "ht_DeltaZ_Category", "ht_DeltaZ = Z18 − Z6",
        "weight_12m_g", "wt_12m_zscore", "wt_12m_zscore_Imputation",
        "wt_DeltaZ = Z12 − Z0", "wt_DeltaZ_Category", "wt_DeltaZ = Z18 − Z6"
    ],
    "18m": [
        "BMI_18m_zscore", "BMI_18m_zscore_Imputation", "BMI_DeltaZ = Z24− Z12",
        "height_18m_cm", "ht_18m_zscore", "ht_18m_zscore_Imputation",
        "ht_DeltaZ = Z24 − Z12",
        "weight_18m_g", "wt_18m_zscore", "wt_18m_zscore_Imputation",
        "wt_DeltaZ = Z24 − Z12"
    ],
    "24m": [
        "BMI_24m_zscore", "BMIt_24m_zscore_Imputation",
        "BMI_DeltaZ = Z24− Z12", "BMI_DeltaZ_Category", "BMI_DeltaZ = Z36− Z18", "BMI_Category",
        "height_24m_cm", "ht_24m_zscore", "ht_24m_zscore_Imputation",
        "ht_DeltaZ = Z36 − Z18", "ht_Category",
        "weight_24m_g", "wt_24m_zscore", "wt_24m_zscore_Imputation",
        "wt_DeltaZ = Z36 − Z18", "wt_DeltaZ_Category", "wt_Category"
    ],
    "36m": [
        "BMI_36m_zscore", "BMI_36m_zscore_Imputation", "BMI_DeltaZ = Z36− Z24",
        "BMI_DeltaZ_Category", "BMI_DeltaZ = Z48− Z24", "BMI_Category",
        "height_36m_cm", "ht_36m_zscore", "ht_36m_zscore_Imputation",
        "ht_DeltaZ = Z36− Z24", "ht_DeltaZ_Category", "ht_DeltaZ = Z48 − Z24", "ht_Category",
        "weight_36m_g", "wt_3y_zscore", "wt_36m_zscore_Imputation",
        "wt_DeltaZ = Z36 − Z24", "wt_DeltaZ_Category", "wt_DeltaZ = Z48 − Z24", "wt_Category"
    ],
    "48m": [
        "BMI_4y_zscore", "BMI_48m_zscore_Imputation",
        "BMI_DeltaZ = Z48 − Z36", "BMI_DeltaZ_Category", "BMI_Category",
        "height_48m_cm", "ht_48m_zscore", "ht_48m_zscore_Imputation",
        "ht_DeltaZ = Z48 − Z36", "ht_DeltaZ_Category", "ht_Category",
        "weight_48m_g", "wt_4y_zscore", "wt_48m_zscore_Imputation",
        "wt_DeltaZ = Z48 − Z36", "wt_DeltaZ_Category", "wt_Category"
    ]
}

# === 4️⃣ Export grouped CSVs ===
output_folder = "split_data_with_patient_info"
os.makedirs(output_folder, exist_ok=True)

for name, cols in groups.items():
    # combine patient info + group columns, but only those that actually exist in the CSV
    selected_cols = [c for c in (patient_info + cols) if c in df.columns]
    sub_df = df[selected_cols].copy()

    # write to csv
    output_path = os.path.join(output_folder, f"{name}.csv")
    sub_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ Saved {name}.csv with {len(selected_cols)} columns.")

print("🎉 All year-based CSV files exported successfully with patient info included.")
