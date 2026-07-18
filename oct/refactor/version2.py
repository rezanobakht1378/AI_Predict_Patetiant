import pandas as pd
import numpy as np
import statsmodels.api as sm
from xgboost import XGBClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Load the file
file_path = 'data-oct.csv'
df = pd.read_csv(file_path)

print(f"Dataset loaded successfully! Total records: {df.shape[0]}, Total columns: {df.shape[1]}")

# Basic data cleaning: handle empty strings or spaces as NaN
df = df.replace(r'^\s*$', np.nan, regex=True)

# Clean birth_order
if 'birth_order' in df.columns:
    df['birth_order'] = df['birth_order'].astype('string').str.strip().replace('', pd.NA)
    df['birth_order'] = pd.to_numeric(df['birth_order'], errors='coerce').astype('Int64')
    df.loc[~df['birth_order'].between(1, 20), 'birth_order'] = pd.NA

df = df.replace('#VALUE!', pd.NA)
df = df.replace('UF', pd.NA)

# =====================================================================
# 0. CLINICAL MULTI-CLASS TARGET CONVERSION (ALL AGES)
# =====================================================================
def assign_clinical_class(zscore):
    if pd.isna(zscore):
        return np.nan
    if float(zscore) < -3:
        return 2  # Severe (Severely underweight / Severely short stature / Severely thin)
    elif -3 <= float(zscore) < -2:
        return 1  # Moderate (Underweight / Short stature / Thin)
    else:
        return 0  # Normal (-2 <= zscore)

# Apply baseline target vectors for all key classification tasks safely across the dataframe
age_suffixes = ['birth', '6m', '12m', '18m', '24m', '36m', '48m']
for age in age_suffixes:
    wt_col = 'wt_birth_zscore' if age == 'birth' else f'wt_{age}_zscore'
    ht_col = 'ht_birth_zscore' if age == 'birth' else ('ht_1y_zscore' if age == '12m' else f'ht_{age}_zscore')
    bmi_col = f'BMI_{age}_zscore'
    
    if wt_col in df.columns:
        df[f'weight_{age}_class'] = df[wt_col].apply(assign_clinical_class)
    if ht_col in df.columns:
        df[f'height_{age}_class'] = df[ht_col].apply(assign_clinical_class)
    if bmi_col in df.columns:
        df[f'bmi_{age}_class'] = df[bmi_col].apply(assign_clinical_class)

# The structured target registry explicitly mapping all rolling window evaluation spaces
targets = {
    # --- BIRTH TARGET MARGINS ---
    'Birth (Weight)':      df['wt_birth_zscore'].apply(assign_clinical_class)  if 'wt_birth_zscore' in df.columns else pd.Series(dtype=float),
    'Birth (Height)':      df['ht_birth_zscore'].apply(assign_clinical_class)  if 'ht_birth_zscore' in df.columns else pd.Series(dtype=float),
    'Birth (BMI)':         df['BMI_birth_zscore'].apply(assign_clinical_class) if 'BMI_birth_zscore' in df.columns else pd.Series(dtype=float),

    # --- 6 MONTHS TARGET MARGINS ---
    '6 Months (Weight)':   df['wt_6m_zscore'].apply(assign_clinical_class)     if 'wt_6m_zscore' in df.columns else pd.Series(dtype=float),
    '6 Months (Height)':   df['ht_6m_zscore'].apply(assign_clinical_class)     if 'ht_6m_zscore' in df.columns else pd.Series(dtype=float),
    '6 Months (BMI)':      df['BMI_6m_zscore'].apply(assign_clinical_class)    if 'BMI_6m_zscore' in df.columns else pd.Series(dtype=float),
    
    # --- 12 MONTHS TARGET MARGINS ---
    '12 Months (Weight)':  df['wt_12m_zscore'].apply(assign_clinical_class)    if 'wt_12m_zscore' in df.columns else pd.Series(dtype=float),
    '12 Months (Height)':  df['ht_1y_zscore'].apply(assign_clinical_class)     if 'ht_1y_zscore' in df.columns else pd.Series(dtype=float),
    '12 Months (BMI)':     df['BMI_12m_zscore'].apply(assign_clinical_class)   if 'BMI_12m_zscore' in df.columns else pd.Series(dtype=float),
    
    # --- 18 MONTHS TARGET MARGINS ---
    '18 Months (Weight)':  df['wt_18m_zscore'].apply(assign_clinical_class)    if 'wt_18m_zscore' in df.columns else pd.Series(dtype=float),
    '18 Months (Height)':  df['ht_18m_zscore'].apply(assign_clinical_class)   if 'ht_18m_zscore' in df.columns else pd.Series(dtype=float),
    '18 Months (BMI)':     df['BMI_18m_zscore'].apply(assign_clinical_class)   if 'BMI_18m_zscore' in df.columns else pd.Series(dtype=float),
    
    # --- 24 MONTHS TARGET MARGINS ---
    '24 Months (Weight)':  df['wt_24m_zscore'].apply(assign_clinical_class)    if 'wt_24m_zscore' in df.columns else pd.Series(dtype=float),
    '24 Months (Height)':  df['ht_24m_zscore'].apply(assign_clinical_class)   if 'ht_24m_zscore' in df.columns else pd.Series(dtype=float),
    '24 Months (BMI)':     df['BMI_24m_zscore'].apply(assign_clinical_class)   if 'BMI_24m_zscore' in df.columns else pd.Series(dtype=float),
    
    # --- 36 MONTHS TARGET MARGINS ---
    '36 Months (Weight)':  df['wt_36m_zscore_Imputation'].apply(assign_clinical_class)    if 'wt_36m_zscore_Imputation' in df.columns else pd.Series(dtype=float),
    '36 Months (Height)':  df['ht_36m_zscore'].apply(assign_clinical_class)   if 'ht_36m_zscore' in df.columns else pd.Series(dtype=float),
    '36 Months (BMI)':     df['BMI_36m_zscore'].apply(assign_clinical_class)   if 'BMI_36m_zscore' in df.columns else pd.Series(dtype=float),
    
    # --- 48 MONTHS TARGET MARGINS ---
    '48 Months (Weight)':  df['wt_48m_zscore'].apply(assign_clinical_class)    if 'wt_48m_zscore' in df.columns else pd.Series(dtype=float),
    '48 Months (Height)':  df['ht_48m_zscore'].apply(assign_clinical_class)   if 'ht_48m_zscore' in df.columns else pd.Series(dtype=float),
    '48 Months (BMI)':     df['BMI_48m_zscore'].apply(assign_clinical_class)   if 'BMI_48m_zscore' in df.columns else pd.Series(dtype=float),
}

# Baseline features infrastructure definitions
base_cols = ['gender', 'birth_order', 'mother_age_pregnancy', 'delivery_type', 
             'mother_underweight', 'mother_hypertension', 'abortion_history', 
             'gestational_weeks', 'gestational_diabetes', 'headcirc_birth_cm']

raw_metrics = [
    'height_birth_cm', 'weight_birth_g', 
    'height_6m_cm', 'weight_6m_g', 
    'height_12m_cm', 'weight_12m_g'
]

zscore_cols = [
    'BMI_birth_zscore', 'ht_birth_zscore', 'wt_birth_zscore', 
    'BMI_6m_zscore', 'ht_6m_zscore', 'wt_6m_zscore', 
    'BMI_12m_zscore', 'ht_1y_zscore', 'wt_12m_zscore',
    'BMI_18m_zscore', 'ht_18m_zscore', 'wt_18m_zscore',
    'BMI_24m_zscore', 'ht_24m_zscore', 'wt_24m_zscore',
    'BMI_36m_zscore', 'ht_36m_zscore', 'wt_36m_zscore_Imputation',
    'BMI_48m_zscore', 'ht_48m_zscore', 'wt_48m_zscore'
]

# =====================================================================
# 0. CLINICAL CLASSIFICATION LOGIC (UNIFIED 'Normal' LABEL)
# =====================================================================
def assign_weight_class(zscore):
    if pd.isna(zscore): return np.nan
    return 'Severe underweight' if float(zscore) <= -3 else 'Underweight' if float(zscore) <= -2 and float(zscore) > -3 else 'Normal'

def assign_height_class(zscore):
    if pd.isna(zscore): return np.nan
    return 'Severe short stature' if float(zscore) <= -3 else 'Short stature' if float(zscore) <= -2 and float(zscore) > -3 else 'Normal'

def assign_bmi_class(zscore):
    if pd.isna(zscore): return np.nan
    return 'Severe weight loss' if float(zscore) <= -3 else 'Weight loss' if float(zscore) <= -2 and float(zscore) > -3 else 'Normal'

all_milestones = {
    'Birth (Weight)': ('wt_birth_zscore', assign_weight_class),
    'Birth (Height)': ('ht_birth_zscore', assign_height_class),
    'Birth (BMI)':    ('BMI_birth_zscore', assign_bmi_class),
    '6 Months (Weight)': ('wt_6m_zscore', assign_weight_class),
    '6 Months (Height)': ('ht_6m_zscore', assign_height_class),
    '6 Months (BMI)':    ('BMI_6m_zscore', assign_bmi_class),
    '12 Months (Weight)': ('wt_12m_zscore', assign_weight_class),
    '12 Months (Height)': ('ht_1y_zscore', assign_height_class),
    '12 Months (BMI)':    ('BMI_12m_zscore', assign_bmi_class),
    '18 Months (Weight)': ('wt_18m_zscore', assign_weight_class),
    '18 Months (Height)': ('ht_18m_zscore', assign_height_class),
    '18 Months (BMI)':    ('BMI_18m_zscore', assign_bmi_class),
    '24 Months (Weight)': ('wt_24m_zscore', assign_weight_class),
    '24 Months (Height)': ('ht_24m_zscore', assign_height_class),
    '24 Months (BMI)':    ('BMI_24m_zscore', assign_bmi_class),
    '36 Months (Weight)': ('wt_36m_zscore_Imputation', assign_weight_class),
    '36 Months (Height)': ('ht_36m_zscore', assign_height_class),
    '36 Months (BMI)':    ('BMI_36m_zscore', assign_bmi_class),
    '48 Months (Weight)': ('wt_48m_zscore', assign_weight_class),
    '48 Months (Height)': ('ht_48m_zscore', assign_height_class),
    '48 Months (BMI)':    ('BMI_48m_zscore', assign_bmi_class)
}

target_classes = [
    'Normal', 'Severe weight loss', 'Weight loss', 
    'Severe underweight', 'Underweight', 'Severe short stature', 'Short stature'
]

records = []
for label, (zscore_col, classification_func) in all_milestones.items():
    if zscore_col in df.columns:
        classified_series = df[zscore_col].apply(classification_func)
        counts = classified_series.value_counts()
        row = {'Age_Milestone_Metric': label}
        for cls in target_classes:
            row[cls] = counts.get(cls, 0)
        row['Missing_Records'] = classified_series.isna().sum()
        row['Total_Cohort'] = len(classified_series)
        records.append(row)

df_unified = pd.DataFrame(records)
df_unified.to_csv('unified_class_distribution.csv', index=False)

print("\n======================= UPDATED UNIFIED COHORT SHEET =======================")
print(df_unified.to_string(index=False))
print("\n[Data Export] Master counts exported cleanly to: unified_class_distribution.csv")

# =====================================================================
# 1. SCENARIOS DEFINITIONS
# =====================================================================
scenarios = {
    "S1_S5_All_Data": base_cols + raw_metrics + zscore_cols,
    "S2_No_Zscores": base_cols + raw_metrics,
    "S3_No_Base_Data": raw_metrics + zscore_cols,
    "S4_S6_Zscore_Only": zscore_cols
}

# =====================================================================
# 2. PREPROCESSING PIPELINE FACTORY
# =====================================================================
def get_processor(feature_list):
    num_features = [c for c in feature_list if c not in ['gender', 'delivery_type']]
    cat_features = [c for c in feature_list if c in ['gender', 'delivery_type']]
    
    transformers = []
    if num_features:
        transformers.append(('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), num_features))
    if cat_features:
        transformers.append(('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ]), cat_features))
        
    return ColumnTransformer(transformers=transformers)

# =====================================================================
# 3. MULTI-CLASS CLASSIFICATION MODELS DICTIONARY
# =====================================================================
models = {
    'Multinomial_Logistic': LogisticRegression(max_iter=1000, random_state=42),
    'XGBoost_Classifier': XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.05, eval_metric='mlogloss', random_state=42),
    'Support_Vector_Classifier': SVC(kernel='rbf', C=10.0, decision_function_shape='ovr', random_state=42),
    'Neural_Network_MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
}

# =====================================================================
# 4. CHRONOLOGICAL ROLLING PREDICTION PIPELINE LOOP
# =====================================================================
age_transitions = [
    {'current_age': 'Birth',     'next_age': '6 Months'},
    {'current_age': '6 Months',  'next_age': '12 Months'},
    {'current_age': '12 Months', 'next_age': '18 Months'},
    {'current_age': '18 Months', 'next_age': '24 Months'},
    {'current_age': '24 Months', 'next_age': '36 Months'},
    {'current_age': '36 Months', 'next_age': '48 Months'}
]

metrics = ['Weight', 'Height', 'BMI']
results_master = []

for transition in age_transitions:
    current_age = transition['current_age']
    next_age = transition['next_age']
    
    for metric in metrics:
        target_key = f"{next_age} ({metric})"
        if target_key not in targets:
            continue
            
        y_vector = targets[target_key]
        valid_mask = y_vector.dropna().index
        
        df_valid = df.loc[valid_mask]
        y_valid = y_vector.loc[valid_mask].astype(int)
        
        for sc_name, feature_space in scenarios.items():
            current_features = [
                f for f in feature_space 
                if current_age.split()[0].lower() in f.lower() or ('birth' in current_age.lower() and 'birth' in f.lower())
            ]
            
            if not current_features:
                continue
                
            X_space = df_valid[current_features]
            if X_space.shape[1] == 0 or len(X_space) < 10:
                continue
            
            # --- ROBUST STRATIFICATION CHECK TO PREVENT CRASHES ---
            # Classes must have at least 2 instances to allow stratification.
            can_stratify = (y_valid.nunique() > 1) and (y_valid.value_counts().min() >= 2)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X_space, y_valid, test_size=0.2, random_state=42, 
                stratify=y_valid if can_stratify else None
            )
            
            for model_name, model in models.items():
                pipeline = Pipeline([
                    ('preprocessor', get_processor(current_features)),
                    ('classifier', model)
                ])
                
                pipeline.fit(X_train, y_train)
                predictions = pipeline.predict(X_test)
                
                acc = accuracy_score(y_test, predictions)
                prec = precision_score(y_test, predictions, average='macro', zero_division=0)
                rec = recall_score(y_test, predictions, average='macro', zero_division=0)
                f1 = f1_score(y_test, predictions, average='macro', zero_division=0)
                
                results_master.append({
                    'Predictor_Age': current_age,
                    'Predicted_Target': target_key,
                    'Scenario': sc_name,
                    'Model': model_name,
                    'Features_Used_Count': len(current_features),
                    'Accuracy': round(acc, 4),
                    'Precision': round(prec, 4),
                    'Recall': round(rec, 4),
                    'F1_Score': round(f1, 4)
                })

df_performance = pd.DataFrame(results_master)
df_performance.to_csv('chronological_predictive_performance.csv', index=False)
print("Time-series evaluation complete. Performance matrix generated sequentially.")

# =====================================================================
# 5. DATA PREPARATION UTILITY FOR STATSMODELS (Robust Column Check)
# =====================================================================
def prepare_scenario_matrix(df, feature_list, target_series):
    # CRITICAL FIX: Dynamically filter out columns that do not exist in the dataframe
    existing_features = [c for c in feature_list if c in df.columns]
    
    if not existing_features:
        raise ValueError("None of the requested features for this scenario exist in the DataFrame columns.")
        
    X_raw = df[existing_features].copy()
    
    cat_cols = [c for c in X_raw.columns if X_raw[c].dtype == 'object' or c in ['gender', 'delivery_type']]
    num_cols = [c for c in X_raw.columns if c not in cat_cols]
    
    if num_cols:
        X_raw[num_cols] = SimpleImputer(strategy='median').fit_transform(X_raw[num_cols])
        X_raw[num_cols] = StandardScaler().fit_transform(X_raw[num_cols])
    if cat_cols:
        X_raw = pd.get_dummies(X_raw, columns=cat_cols, drop_first=True)
        
    valid_idx = target_series.dropna().index
    X_clean = X_raw.loc[valid_idx].astype(float)
    y_clean = target_series.loc[valid_idx].astype(int)
    
    return sm.add_constant(X_clean), y_clean

# =====================================================================
# 6. MULTINOMIAL FORWARD STEPWISE SELECTOR (Using MNLogit AIC / BIC)
# =====================================================================
def forward_stepwise_selection_mnlogit(X, y, criterion='aic'):
    initial_features = ['const'] if 'const' in X.columns else []
    remaining_features = [c for c in X.columns if c != 'const']
    current_features = list(initial_features)
    
    best_score = sm.MNLogit(y, X[current_features]).fit(disp=0).aic if criterion == 'aic' else sm.MNLogit(y, X[current_features]).fit(disp=0).bic
    
    while remaining_features:
        scores_with_candidates = []
        for candidate in remaining_features:
            test_features = current_features + [candidate]
            try:
                model = sm.MNLogit(y, X[test_features]).fit(disp=0)
                score = model.aic if criterion == 'aic' else model.bic
                scores_with_candidates.append((score, candidate))
            except:
                continue 
                
        if not scores_with_candidates:
            break
            
        scores_with_candidates.sort()
        best_candidate_score, best_candidate = scores_with_candidates[0]
        
        if best_candidate_score < best_score:
            current_features.append(best_candidate)
            remaining_features.remove(best_candidate)
            best_score = best_candidate_score
        else:
            break
            
    return [f for f in current_features if f != 'const']

# =====================================================================
# 7. CHRONOLOGICAL MULTINOMIAL FEATURE SELECTION & CORRELATION PIPELINE
# =====================================================================
print("\n--- Starting Chronological AIC vs BIC Feature Selection & Correlation Pipeline ---")

# Define chronological windows matching Section 4
age_transitions = [
    {'current_age': 'Birth',     'next_age': '6 Months'},
    {'current_age': '6 Months',  'next_age': '12 Months'},
    {'current_age': '12 Months', 'next_age': '18 Months'},
    {'current_age': '18 Months', 'next_age': '24 Months'},
    {'current_age': '24 Months', 'next_age': '36 Months'},
    {'current_age': '36 Months', 'next_age': '48 Months'}
]

metrics = ['Weight', 'Height', 'BMI']
feature_selection_summary = []
optimized_spaces = {}

# Make a directory to keep charts organized if desired
os.makedirs('correlation_plots', exist_ok=True)

for transition in age_transitions:
    current_age = transition['current_age']
    next_age = transition['next_age']
    
    print(f"\n=====================================================================")
    print(f"WINDOW: Evaluating {current_age} Features -> Predicting {next_age} Targets")
    print(f"=====================================================================")
    
    for metric in metrics:
        target_key = f"{next_age} ({metric})"
        
        # Verify if target column maps correctly in our registry
        if target_key not in targets or targets[target_key].empty:
            continue
            
        y_vector = targets[target_key]
        valid_mask = y_vector.dropna().index
        
        # Target vectors for statsmodels must match the subset records
        df_valid = df.loc[valid_mask]
        y_valid = y_vector.loc[valid_mask].astype(int)
        
        # We need at least 2 distinct classes to fit an MNLogit model
        if y_valid.nunique() < 2:
            print(f" -> Target {target_key}: Skipped (Less than 2 unique classes present).")
            continue
            
        for sc_name, feature_space in scenarios.items():
            # Filter feature space strictly down to the predictor age context
            current_features = [
                f for f in feature_space 
                if current_age.split()[0].lower() in f.lower() or ('birth' in current_age.lower() and 'birth' in f.lower())
            ]
            
            # Keep only features present in the raw dataframe index
            valid_features = [f for f in current_features if f in df_valid.columns]
            
            if not valid_features or len(df_valid) < 10:
                continue
                
            # Create cleaner file name strings
            safe_name = f"{current_age.replace(' ', '')}_to_{next_age.replace(' ', '')}_{metric}_{sc_name}"
            
            try:
                # 1. Prepare Feature Space & Handle Imputation/Encoding
                X_processed, y_processed = prepare_scenario_matrix(df_valid, valid_features, y_valid)
                X_features_only = X_processed.drop(columns=['const'], errors='ignore')
                
                if X_features_only.shape[1] == 0:
                    continue
                
                # 2. Compute, Save, and Plot Local Feature Correlations
                corr_matrix = X_features_only.corr()
                corr_matrix.to_csv(f"correlation_plots/corr_{safe_name}.csv")
                
                if X_features_only.shape[1] > 1:
                    plt.figure(figsize=(10, 8))
                    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', vmin=-1, vmax=1, linewidths=0.5)
                    plt.title(f"Correlation: {current_age} Features ({sc_name})\nTarget: {target_key}", fontsize=11)
                    plt.tight_layout()
                    plt.savefig(f"correlation_plots/plot_{safe_name}.png", dpi=150)
                    plt.close()
                
                # 3. Perform Forward Stepwise Optimization (AIC vs BIC)
                print(f"\nRunning Selection for Target: {target_key} | Scenario: {sc_name}")
                aic_features = forward_stepwise_selection_mnlogit(X_processed, y_processed, criterion='aic')
                bic_features = forward_stepwise_selection_mnlogit(X_processed, y_processed, criterion='bic')
                
                # CRITICAL FIX: Save the processed matrices along with the selected features!
                optimized_spaces[safe_name] = {
                    'aic_selected': aic_features,
                    'bic_selected': bic_features,
                    'processed_X': X_processed.drop(columns=['const'], errors='ignore'),
                    'processed_y': y_processed
                }
                
                print(f"   -> Available Features: {len(valid_features)}")
                print(f"   -> AIC Selected ({len(aic_features)}): {aic_features}")
                print(f"   -> BIC Selected ({len(bic_features)}): {bic_features}")
                
                feature_selection_summary.append({
                    'Predictor_Age': current_age,
                    'Target_Age_Metric': target_key,
                    'Scenario': sc_name,
                    'Total_Available_Features': len(valid_features),
                    'AIC_Selected_Count': len(aic_features),
                    'BIC_Selected_Count': len(bic_features),
                    'AIC_Features': ", ".join(aic_features),
                    'BIC_Features': ", ".join(bic_features)
                })
                
            except Exception as e:
                print(f"   -> Error processing {safe_name}: {str(e)}")
                continue

# Write final master summary tracking matrix out to disk
df_summary = pd.DataFrame(feature_selection_summary)
df_summary.to_csv('chronological_feature_selection_summary.csv', index=False)

print("\n=====================================================================")
print("Pipeline complete! All localized correlation sheets, visual heatmaps,")
print("and optimization metrics are securely stored in 'correlation_plots/'")
print("Master optimization logs: chronological_feature_selection_summary.csv")
print("=====================================================================")

# =====================================================================
# 8. TRAIN FINAL CLASSIFIERS ON MATHEMATICALLY VERIFIED COLUMNS
# =====================================================================
print("\n--- Training Final Classifiers on Mathematically Verified Columns Only ---")

final_results_report = []

# Iterating over the dynamically constructed chronological spaces
for running_key, verified_data_pkg in optimized_spaces.items():
    # Parse metadata from the key string for downstream reporting
    # Expected format: "Birth_to_6Months_Weight_S1_S5_All_Data"
    parts = running_key.split('_')
    if len(parts) >= 4:
        predictor_age = parts[0]
        target_age = parts[2]
        metric_name = parts[3]
        scenario_name = "_".join(parts[4:]) if len(parts) > 4 else "Base"
    else:
        predictor_age, target_age, metric_name, scenario_name = running_key, "Unknown", "Unknown", "Unknown"

    X_all_processed = verified_data_pkg['processed_X']
    y_final = verified_data_pkg['processed_y']
    
    feature_reduction_spaces = {
        "Full_Feature_Space": list(X_all_processed.columns),
        "AIC_Optimized_Space": verified_data_pkg['aic_selected'],
        "BIC_Optimized_Space": verified_data_pkg['bic_selected']
    }
    
    # Declare fresh model instances inside the loop to avoid cross-contamination
    final_models = {
        'XGBoost_Classifier': XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, eval_metric='mlogloss', random_state=42),
        'Support_Vector_Classifier': SVC(kernel='rbf', C=10.0, decision_function_shape='ovr', random_state=42),
        'Neural_Network_MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
    }

    for space_name, selected_features in feature_reduction_spaces.items():
        if len(selected_features) == 0:
            continue 
            
        X_subset = X_all_processed[selected_features]
        X_train_final, X_test_final, y_train_final, y_test_final = train_test_split(
            X_subset, y_final, test_size=0.2, random_state=42
        )
        
        # Ensure we have instances of classes in both validation splits
        if len(np.unique(y_train_final)) < 2 or len(np.unique(y_test_final)) < 2:
            continue

        for model_name, model_instance in final_models.items():
            try:
                model_instance.fit(X_train_final, y_train_final)
                predictions = model_instance.predict(X_test_final)
                
                acc = accuracy_score(y_test_final, predictions)
                prec = precision_score(y_test_final, predictions, average='macro', zero_division=0)
                rec = recall_score(y_test_final, predictions, average='macro', zero_division=0)
                f1 = f1_score(y_test_final, predictions, average='macro', zero_division=0)
                
                final_results_report.append({
                    "Transition_Key": running_key,
                    "Predictor_Age": predictor_age,
                    "Target_Age": target_age,
                    "Metric": metric_name,
                    "Feature_Space": space_name,
                    "Feature_Count": len(selected_features),
                    "Model": model_name,
                    "Accuracy": round(acc, 4),
                    "Precision": round(prec, 4),
                    "Recall": round(rec, 4),
                    "F1_Score": round(f1, 4)
                })
            except Exception as e:
                print(f" -> Execution error on {model_name} with {space_name} space: {str(e)}")
                continue

# =====================================================================
# 9. FINAL SIDE-BY-SIDE PRESENTATION & EXPORT
# =====================================================================
if final_results_report:
    df_final_comparison = pd.DataFrame(final_results_report)
    
    # Save the complete micro-level tracking data out to disk
    df_final_comparison.to_csv('feature_reduction_performance.csv', index=False)
    
    # Pivot performance tracking macro metrics cleanly
    performance_pivot = df_final_comparison.pivot_table(
        index=["Transition_Key", "Model"], 
        columns="Feature_Space", 
        values=["Accuracy", "F1_Score"]
    )
    
    print("\n======================= FINAL FEATURE REDUCTION EVALUATION REPORT =======================")
    print(performance_pivot.to_string())
    print("\n[Data Export] CSV metric tables generated: 'feature_reduction_performance.csv'")
else:
    print("\n[Execution Warning] No classifiers could be trained. Check target distributions.")