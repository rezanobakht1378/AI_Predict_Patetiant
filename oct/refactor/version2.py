import pandas as pd
import numpy as np
import statsmodels.api as sm
from xgboost import XGBClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE, SMOTENC, RandomOverSampler
from sklearn.preprocessing import StandardScaler, OneHotEncoder, label_binarize
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    balanced_accuracy_score,
    matthews_corrcoef,
    multilabel_confusion_matrix
)
from sklearn.preprocessing import label_binarize
from sklearn.metrics import roc_curve
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
df = df.dropna(subset=['birth_order'])

df = df.replace('#VALUE!', pd.NA)
df = df.replace('UF', pd.NA)

bmi_raw_cols = []

age_mapping = {
    "birth": ("weight_birth_g", "height_birth_cm"),
    "6m": ("weight_6m_g", "height_6m_cm"),
    "12m": ("weight_12m_g", "height_12m_cm"),
    "18m": ("weight_18m_g", "height_18m_cm"),
    "24m": ("weight_24m_g", "height_24m_cm"),
    "36m": ("weight_36m_g", "height_36m_cm"),
    "48m": ("weight_48m_g", "height_48m_cm"),
}

for age, (weight_col, height_col) in age_mapping.items():

    if weight_col in df.columns and height_col in df.columns:

        bmi_col = f"BMI_{age}"

        df[bmi_col] = (
            (df[weight_col] / 1000)
            /
            ((df[height_col] / 100) ** 2)
        )

        df.loc[(df[bmi_col] > 40) | (df[bmi_col] < 5), bmi_col] = np.nan

        bmi_raw_cols.append(bmi_col)

# Baseline features infrastructure definitions
base_cols = ['gender', 'birth_order', 'mother_age_pregnancy', 'delivery_type', 
             'mother_underweight', 'mother_hypertension', 'abortion_history', 
             'gestational_weeks', 'gestational_diabetes', 'headcirc_birth_cm']

raw_metrics = [
    'height_birth_cm', 'weight_birth_g', 
    'height_6m_cm', 'weight_6m_g', 
    'height_12m_cm', 'weight_12m_g',
    'height_18m_cm', 'weight_18m_g',
    'height_24m_cm', 'weight_24m_g',
    'height_36m_cm', 'weight_36m_g',
    'height_48m_cm', 'weight_48m_g',
]

weight_zscore_cols = [
    "wt_birth_zscore",
    "wt_6m_zscore",
    "wt_12m_zscore",
    "wt_18m_zscore",
    "wt_24m_zscore",
    "wt_36m_zscore_Imputation",
    "wt_48m_zscore",
]

height_zscore_cols = [
    "ht_birth_zscore",
    "ht_6m_zscore",
    "ht_1y_zscore",
    "ht_18m_zscore",
    "ht_24m_zscore",
    "ht_36m_zscore",
    "ht_48m_zscore",
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

bmi_cols = [
    'BMI_birth_zscore', 'BMI_6m_zscore', 'BMI_12m_zscore',
    'BMI_18m_zscore', 'BMI_24m_zscore', 'BMI_36m_zscore',
    'BMI_48m_zscore'
]

headcirc_cols = [
    c for c in df.columns
    if "headcirc" in c.lower()
]

# =====================================================================
# 1. CLINICAL CLASSIFICATION LOGIC (UNIFIED 'Normal' LABEL)
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

targets = {}
target_classes = [
    'Normal', 'Severe weight loss', 'Weight loss', 
    'Severe underweight', 'Underweight', 'Severe short stature', 'Short stature'
]

records = []
for label, (zscore_col, classification_func) in all_milestones.items():
    if zscore_col in df.columns:
        classified_series = df[zscore_col].apply(classification_func)
        targets[label] = classified_series
        counts = classified_series.value_counts()
        row = {'Age_Milestone_Metric': label}
        for cls in target_classes:
            row[cls] = counts.get(cls, 0)
        row['Missing_Records'] = classified_series.isna().sum()
        row['Total_Cohort'] = len(classified_series)
        records.append(row)
    else:
        targets[label] = pd.Series(index=df.index, dtype='object')

df_unified = pd.DataFrame(records)
df_unified.to_csv('unified_class_distribution.csv', index=False)

print("\n======================= UPDATED UNIFIED COHORT SHEET =======================")
print(df_unified.to_string(index=False))
print("\n[Data Export] Master counts exported cleanly to: unified_class_distribution.csv")

# =====================================================================
# 1. SCENARIOS DEFINITIONS
# =====================================================================
scenarios = {
    "S1_All_Data": base_cols + raw_metrics + zscore_cols,
    "S2_No_Zscores": base_cols + raw_metrics,
    "S3_No_Base_Data": raw_metrics + zscore_cols,
    "S4_Zscore_Only": zscore_cols,
    "S5_Base_Only": base_cols,
    "S6_Raw_Only": raw_metrics,
    "S7_Anthropometric_Only": raw_metrics + bmi_raw_cols + headcirc_cols,
    "WHO_Growth_Indices": bmi_cols + height_zscore_cols + weight_zscore_cols
}

# =====================================================================
# 2. PREPROCESSING PIPELINE FACTORY
# =====================================================================
def get_processor(feature_list, impute=True, scale=True):
    num_features = [c for c in feature_list if c not in ['gender', 'delivery_type']]
    cat_features = [c for c in feature_list if c in ['gender', 'delivery_type']]
    
    transformers = []
    if num_features:
        steps = []
        if impute:
            steps.append(('imputer', SimpleImputer(strategy='median')))
        if scale:
            steps.append(('scaler', StandardScaler()))
        if steps:
            transformers.append(('num', Pipeline(steps), num_features))
        else:
            transformers.append(('num', 'passthrough', num_features))
    if cat_features:
        cat_steps = []
        if impute:
            cat_steps.append(('imputer', SimpleImputer(strategy='most_frequent')))
        cat_steps.append(('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)))
        transformers.append(('cat', Pipeline(cat_steps), cat_features))
        
    return ColumnTransformer(transformers=transformers)


def compute_multiclass_specificity(conf_mat):
    n_classes = conf_mat.shape[0]
    specificities = []
    for i in range(n_classes):
        tp = conf_mat[i, i]
        fn = conf_mat[i, :].sum() - tp
        fp = conf_mat[:, i].sum() - tp
        tn = conf_mat.sum() - (tp + fp + fn)
        denom = tn + fp
        specificities.append(tn / denom if denom != 0 else 0.0)
    return np.mean(specificities)


def remove_near_zero_variance_features(X, freq_cutoff=0.99):
    if X.shape[1] == 0:
        return X
    low_variance_cols = []
    for col in X.columns:
        top_freq = X[col].value_counts(normalize=True, dropna=False).iloc[0]
        if top_freq >= freq_cutoff:
            low_variance_cols.append(col)
    return X.drop(columns=low_variance_cols)


def get_roc_auc_score(pipeline, X, y_true):
    y_score = None
    if hasattr(pipeline.named_steps['classifier'], 'predict_proba'):
        try:
            y_score = pipeline.predict_proba(X)
        except Exception:
            y_score = None
    if y_score is None and hasattr(pipeline.named_steps['classifier'], 'decision_function'):
        try:
            y_score = pipeline.decision_function(X)
        except Exception:
            y_score = None

    if y_score is None:
        return np.nan

    n_classes = len(np.unique(y_true))
    if n_classes == 2:
        if y_score.ndim > 1 and y_score.shape[1] > 1:
            return roc_auc_score(y_true, y_score[:, 1])
        return roc_auc_score(y_true, y_score)
    return roc_auc_score(y_true, y_score, average='macro', multi_class='ovr')

# =====================================================================
# 3. MULTI-CLASS CLASSIFICATION MODELS DICTIONARY
# =====================================================================
models = {
    'Multinomial_Logistic': LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
    'XGBoost_Classifier': XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.05, eval_metric='mlogloss', random_state=42),
    'Support_Vector_Classifier': SVC(kernel='rbf', C=10.0, probability=True, decision_function_shape='ovr', random_state=42, class_weight='balanced'),
    'Neural_Network_MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42),
    'RandomForestClassifier': RandomForestClassifier(n_estimators=400, random_state=42, n_jobs=-1, class_weight='balanced')
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

history_map = {
    "Birth": ["birth"],

    "6 Months": [
        "birth",
        "6m"
    ],

    "12 Months": [
        "birth",
        "6m",
        "12m"
    ],

    "18 Months": [
        "birth",
        "6m",
        "12m",
        "18m"
    ],

    "24 Months": [
        "birth",
        "6m",
        "12m",
        "18m",
        "24m"
    ],

    "36 Months": [
        "birth",
        "6m",
        "12m",
        "18m",
        "24m",
        "36m"
    ],

    "48 Months": [
        "birth",
        "6m",
        "12m",
        "18m",
        "24m",
        "36m",
        "48m"
    ]
}

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
        y_valid = y_vector.loc[valid_mask].astype('category').cat.codes
        
        for sc_name, feature_space in scenarios.items():
            # current_features = [
            #     f for f in feature_space 
            #     if current_age.split()[0].lower() in f.lower() or ('birth' in current_age.lower() and 'birth' in f.lower())
            # ]

            allowed_ages = history_map[current_age]
            current_features = [
                f
                for f in feature_space
                if any(age in f.lower() for age in allowed_ages) and f in df_valid.columns
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

            imputer = SimpleImputer(strategy="median")

            X_train = pd.DataFrame(
                imputer.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )

            X_test = pd.DataFrame(
                imputer.transform(X_test),
                columns=X_test.columns,
                index=X_test.index
            )

            # apply SMOTE / SMOTENC to the training set to handle class imbalance
            X_train = X_train.copy()
            X_test = X_test.copy()

            if 'weight_birth_g' in X_train.columns:
                X_train['weight_birth_g'] = pd.to_numeric(X_train['weight_birth_g'], errors='coerce')
                X_test['weight_birth_g'] = pd.to_numeric(X_test['weight_birth_g'], errors='coerce')

            numeric_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = [c for c in X_train.columns if c not in numeric_cols]

            if numeric_cols:
                num_imputer = SimpleImputer(strategy='median')
                X_train[numeric_cols] = num_imputer.fit_transform(X_train[numeric_cols])
                X_test[numeric_cols] = num_imputer.transform(X_test[numeric_cols])

            if cat_cols:
                cat_imputer = SimpleImputer(strategy='most_frequent')
                X_train[cat_cols] = cat_imputer.fit_transform(X_train[cat_cols])
                X_test[cat_cols] = cat_imputer.transform(X_test[cat_cols])

            categorical_indices = [
                idx for idx, col in enumerate(X_train.columns)
                if col in ['birth_order', 'gender', 'delivery_type']
            ]

            minority_count = y_train.value_counts().min()
            if minority_count <= 5:
                oversampler = RandomOverSampler(random_state=42)
            else:
                if categorical_indices:
                    oversampler = SMOTENC(categorical_features=categorical_indices, random_state=42)
                else:
                    oversampler = SMOTE(random_state=42)

            try:
                X_train, y_train = oversampler.fit_resample(X_train, y_train)
            except Exception:
                oversampler = RandomOverSampler(random_state=42)
                X_train, y_train = oversampler.fit_resample(X_train, y_train)
            
            os.makedirs("confusion_matrices", exist_ok=True)
            for model_name, model in models.items():
                needs_scaling = model_name in ['Multinomial_Logistic', 'Support_Vector_Classifier', 'Neural_Network_MLP']
                pipeline = Pipeline([
                    ('preprocessor', get_processor(current_features, impute=False, scale=needs_scaling)),
                    ('classifier', model)
                ])
                
                pipeline.fit(X_train, y_train)
                predictions = pipeline.predict(X_test)
                probs = None
                if hasattr(pipeline.named_steps['classifier'], 'predict_proba'):
                    try:
                        probs = pipeline.predict_proba(X_test)
                    except Exception:
                        probs = None

                cm = confusion_matrix(y_test, predictions)
                cm_df = pd.DataFrame(cm)
                cm_df.to_csv(
                    f"confusion_matrices/confusion_{current_age}_{target_key}_{model_name}.csv",
                    index=False
                )

                auc = get_roc_auc_score(pipeline, X_test, y_test)
                acc = accuracy_score(y_test, predictions)
                prec = precision_score(y_test, predictions, average='macro', zero_division=0)
                rec = recall_score(y_test, predictions, average='macro', zero_division=0)
                f1 = f1_score(y_test, predictions, average='macro', zero_division=0)
                balanced_acc = balanced_accuracy_score(y_test,predictions)
                mcc = matthews_corrcoef(y_test,predictions)
                mcm = multilabel_confusion_matrix(y_test,predictions)

                specificities = []

                for mat in mcm:

                    tn = mat[0,0]
                    fp = mat[0,1]

                    if (tn + fp) == 0:
                        specificities.append(0)
                    else:
                        specificities.append(tn / (tn + fp))

                specificity = np.mean(specificities)

                macro_auc = np.nan
                weighted_auc = np.nan
                if probs is not None:
                    try:
                        macro_auc = roc_auc_score(
                            y_test,
                            probs,
                            average="macro",
                            multi_class="ovr"
                        )
                    except Exception:
                        macro_auc = np.nan

                    try:
                        weighted_auc = roc_auc_score(
                            y_test,
                            probs,
                            average="weighted",
                            multi_class="ovr"
                        )
                    except Exception:
                        weighted_auc = np.nan

                results_master.append({

                "Predictor_Age": current_age,
                "Predicted_Target": target_key,
                "Scenario": sc_name,
                "Model": model_name,

                "Features_count": len(current_features),
                "Features": current_features,

                "Accuracy": round(acc,4),

                "Balanced_Accuracy": round(
                    balanced_acc,
                    4
                ),

                "Precision": round(
                    prec,
                    4
                ),

                "Recall": round(
                    rec,
                    4
                ),

                "Specificity": round(
                    specificity,
                    4
                ),

                "F1": round(
                    f1,
                    4
                ),

                "MCC": round(
                    mcc,
                    4
                ),

                "ROC_AUC": round(
                    auc,
                    4
                ),
                "Macro_ROC_AUC": round(macro_auc, 4),
                "Weighted_ROC_AUC": round(weighted_auc, 4),
            })

df_performance = pd.DataFrame(results_master)
df_performance.to_csv('chronological_predictive_performance.csv', index=False)

os.makedirs("roc_plots", exist_ok=True)
os.makedirs("roc_data", exist_ok=True)

# Binarize labels
classes = np.unique(y_test)
y_bin = label_binarize(y_test, classes=classes)

auc_scores = []

for i in range(y_bin.shape[1]):

    # ROC
    fpr, tpr, thresholds = roc_curve(
        y_bin[:, i],
        probs[:, i]
    )

    auc = roc_auc_score(
        y_bin[:, i],
        probs[:, i]
    )

    auc_scores.append({
        "Class": classes[i],
        "AUC": auc
    })

    # ============================
    # Save ROC coordinates
    # ============================

    roc_df = pd.DataFrame({
        "Threshold": thresholds,
        "False Positive Rate": fpr,
        "True Positive Rate": tpr
    })

    roc_df.to_csv(
        f"roc_data/{current_age}_{target_key}_{model_name}_class_{classes[i]}.csv",
        index=False
    )

    # ============================
    # Plot ROC
    # ============================

    plt.figure(figsize=(6,6))

    plt.plot(
        fpr,
        tpr,
        linewidth=2,
        label=f"AUC = {auc:.3f}"
    )

    plt.plot(
        [0,1],
        [0,1],
        "--",
        color="gray"
    )

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")

    plt.title(
        f"{model_name}\n{target_key}\nClass {classes[i]}"
    )

    plt.legend()

    plt.grid(alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        f"roc_plots/{current_age}_{target_key}_{model_name}_class_{classes[i]}.png",
        dpi=300
    )

    plt.close()

# ==========================================
# Save AUC summary for all classes
# ==========================================

pd.DataFrame(auc_scores).to_csv(
    f"roc_data/{current_age}_{target_key}_{model_name}_AUC_summary.csv",
    index=False
)
print("Time-series evaluation complete. Performance matrix generated sequentially.")

# =====================================================================
# 5. DATA PREPARATION UTILITY FOR STATSMODELS (Robust Column Check)
# =====================================================================
def prepare_scenario_matrix(df, feature_list, target):
    valid_features = [c for c in feature_list if c in df.columns]
    X = df[valid_features].copy()
    y = target.copy()

    mask = ~y.isna()
    X = X.loc[mask]
    y = y.loc[mask]

    # Remove near-zero-variance features before feature selection
    X = remove_near_zero_variance_features(X)

    return X, y

# =====================================================================
# 6. MULTINOMIAL FORWARD STEPWISE SELECTOR (Using MNLogit AIC / BIC)
# =====================================================================
def forward_stepwise_selection_mnlogit(X, y, criterion="aic"):
    current_features = ["const"]
    remaining_features = [c for c in X.columns if c != "const"]

    base_model = sm.MNLogit(y, X[current_features]).fit(disp=0)
    best_score = base_model.aic if criterion == "aic" else base_model.bic

    while remaining_features:
        scores = []

        for candidate in remaining_features:
            test_features = current_features + [candidate]

            try:
                model = sm.MNLogit(y, X[test_features]).fit(disp=0)
                score = model.aic if criterion == "aic" else model.bic
                scores.append((score, candidate))
            except Exception:
                continue

        if not scores:
            break

        scores.sort(key=lambda x: x[0])
        candidate_score, candidate = scores[0]

        if candidate_score < best_score:
            current_features.append(candidate)
            remaining_features.remove(candidate)
            best_score = candidate_score
        else:
            break

    return [f for f in current_features if f != "const"]

# =====================================================================
# 7. CHRONOLOGICAL MULTINOMIAL FEATURE SELECTION & CORRELATION PIPELINE
# =====================================================================
print("\n--- Starting Chronological AIC vs BIC Feature Selection & Correlation Pipeline ---")

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
        y_valid = y_vector.loc[valid_mask].astype('category').cat.codes
        
        # We need at least 2 distinct classes to fit an MNLogit model
        if y_valid.nunique() < 2:
            print(f" -> Target {target_key}: Skipped (Less than 2 unique classes present).")
            continue
            
        for sc_name, feature_space in scenarios.items():
            # Filter feature space strictly down to the predictor age context
            # current_features = [
            #     f for f in feature_space 
            #     if current_age.split()[0].lower() in f.lower() or ('birth' in current_age.lower() and 'birth' in f.lower())
            # ]
            
            allowed_ages = history_map[current_age]
            current_features = [
                f
                for f in feature_space
                if any(age in f.lower() for age in allowed_ages)
            ]
            
            # Keep only features present in the raw dataframe index
            valid_features = [f for f in current_features if f in df_valid.columns]
            
            if not valid_features or len(df_valid) < 10:
                continue
                
            # Create cleaner file name strings
            safe_name = f"{current_age.replace(' ', '')}_to_{next_age.replace(' ', '')}_{metric}_{sc_name}"
            
            try:
                # 1. Prepare Feature Space & Handle Imputation/Encoding
                X_processed, y_processed = prepare_scenario_matrix(
                    df_valid,
                    valid_features,
                    y_valid
                )

                X_processed = X_processed.drop(columns=["const"], errors="ignore")

                can_stratify = (
                    y_processed.nunique() > 1 and
                    y_processed.value_counts().min() >= 2
                )

                X_train_fs, X_test_fs, y_train_fs, y_test_fs = train_test_split(
                    X_processed,
                    y_processed,
                    test_size=0.2,
                    random_state=42,
                    stratify=y_processed if can_stratify else None
                )

                # ============================================================
                # Train/test split before preprocessing for feature selection
                # ============================================================
                numeric_cols = X_train_fs.select_dtypes(include=[np.number]).columns.tolist()
                cat_cols = [c for c in X_train_fs.columns if c not in numeric_cols]

                if numeric_cols:
                    num_imputer = SimpleImputer(strategy='median')
                    X_train_fs[numeric_cols] = num_imputer.fit_transform(X_train_fs[numeric_cols])
                    X_test_fs[numeric_cols] = num_imputer.transform(X_test_fs[numeric_cols])

                if cat_cols:
                    cat_imputer = SimpleImputer(strategy='most_frequent')
                    X_train_fs[cat_cols] = cat_imputer.fit_transform(X_train_fs[cat_cols])
                    X_test_fs[cat_cols] = cat_imputer.transform(X_test_fs[cat_cols])

                    X_train_fs = pd.get_dummies(X_train_fs, columns=cat_cols, drop_first=True)
                    X_test_fs = pd.get_dummies(X_test_fs, columns=cat_cols, drop_first=True)
                    X_test_fs = X_test_fs.reindex(columns=X_train_fs.columns, fill_value=0)

                # Remove near-zero variance features using training data only
                if X_train_fs.shape[1] > 0:
                    selector = VarianceThreshold(threshold=0.0)
                    X_train_fs = pd.DataFrame(
                        selector.fit_transform(X_train_fs),
                        columns=[col for col, keep in zip(X_train_fs.columns, selector.get_support()) if keep],
                        index=X_train_fs.index
                    )
                    X_test_fs = pd.DataFrame(
                        selector.transform(X_test_fs),
                        columns=X_train_fs.columns,
                        index=X_test_fs.index
                    )

                # Add constant ONLY for statsmodels
                X_train_sm = sm.add_constant(X_train_fs, has_constant="add")

                # ============================================================
                # FEATURE SELECTION ON TRAIN ONLY
                # ============================================================

                aic_features = forward_stepwise_selection_mnlogit(
                    X_train_sm,
                    y_train_fs,
                    criterion="aic"
                )

                bic_features = forward_stepwise_selection_mnlogit(
                    X_train_sm,
                    y_train_fs,
                    criterion="bic"
                )

                # remove const for sklearn models
                aic_features = [f for f in aic_features if f != "const"]
                bic_features = [f for f in bic_features if f != "const"]

                # ============================================================
                # SAVE OPTIMIZED FEATURE SPACES
                # ============================================================

                optimized_spaces[safe_name] = {
                    "aic_selected": aic_features,
                    "bic_selected": bic_features,
                    "X_train": X_train_fs,
                    "X_test": X_test_fs,
                    "y_train": y_train_fs,
                    "y_test": y_test_fs
                }

                feature_selection_summary.append({
                    "Predictor_Age": current_age,
                    "Target_Age_Metric": target_key,
                    "Scenario": sc_name,
                    "Total_Available_Features": X_train_fs.shape[1],
                    "AIC_Selected_Count": len(aic_features),
                    "BIC_Selected_Count": len(bic_features),
                    "AIC_Features": ", ".join(aic_features),
                    "BIC_Features": ", ".join(bic_features)
                })

                print(f"   -> Available Features: {X_train_fs.shape[1]}")
                print(f"   -> AIC Selected ({len(aic_features)}): {aic_features}")
                print(f"   -> BIC Selected ({len(bic_features)}): {bic_features}")
                
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

    X_train_base = verified_data_pkg["X_train"]
    X_test_base = verified_data_pkg["X_test"]

    y_train_final = verified_data_pkg["y_train"]
    y_test_final = verified_data_pkg["y_test"]
    
    feature_reduction_spaces = {
        "Full_Feature_Space": list(X_train_base.columns),
        "AIC_Optimized_Space": verified_data_pkg["aic_selected"],
        "BIC_Optimized_Space": verified_data_pkg["bic_selected"]
    }


    for space_name, selected_features in feature_reduction_spaces.items():
        if len(selected_features) == 0:
            continue 
            
        X_train_final = X_train_base[selected_features].copy()
        X_test_final = X_test_base[selected_features].copy()
        
        # Ensure we have instances of classes in both validation splits
        if len(np.unique(y_train_final)) < 2 or len(np.unique(y_test_final)) < 2:
            continue

        for model_name, model_instance in models.items():
            try:
                needs_scaling = model_name in ['Multinomial_Logistic', 'Support_Vector_Classifier', 'Neural_Network_MLP']
                final_pipeline = Pipeline([
                    ('preprocessor', get_processor(selected_features, impute=False, scale=needs_scaling)),
                    ('classifier', model_instance)
                ])

                final_pipeline.fit(X_train_final, y_train_final)
                predictions = final_pipeline.predict(X_test_final)
                conf_mat = confusion_matrix(y_test_final, predictions)
                acc = accuracy_score(y_test_final, predictions)
                prec = precision_score(y_test_final, predictions, average='macro', zero_division=0)
                rec = recall_score(y_test_final, predictions, average='macro', zero_division=0)
                f1 = f1_score(y_test_final, predictions, average='macro', zero_division=0)
                balanced_acc = balanced_accuracy_score(y_test_final, predictions)
                specificity = compute_multiclass_specificity(conf_mat)
                mcc = matthews_corrcoef(y_test_final, predictions)

                probs = None
                if hasattr(final_pipeline.named_steps['classifier'], 'predict_proba'):
                    try:
                        probs = final_pipeline.predict_proba(X_test_final)
                    except Exception:
                        probs = None

                auc = get_roc_auc_score(final_pipeline, X_test_final, y_test_final)
                macro_auc = np.nan
                weighted_auc = np.nan
                if probs is not None:
                    try:
                        macro_auc = roc_auc_score(y_test_final, probs, average='macro', multi_class='ovr')
                        weighted_auc = roc_auc_score(y_test_final, probs, average='weighted', multi_class='ovr')
                    except Exception:
                        macro_auc = np.nan
                        weighted_auc = np.nan

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
                    "F1_Score": round(f1, 4),
                    "Sensitivity": round(rec, 4),
                    "Specificity": round(specificity, 4),
                    "Balanced_Accuracy": round(balanced_acc, 4),
                    "Matthews_Correlation": round(mcc, 4),
                    "ROC_AUC": round(auc, 4) if not np.isnan(auc) else None,
                    "Macro_ROC_AUC": round(macro_auc, 4) if not np.isnan(macro_auc) else None,
                    "Weighted_ROC_AUC": round(weighted_auc, 4) if not np.isnan(weighted_auc) else None,
                    "Confusion_Matrix": np.array2string(conf_mat, separator=',')
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
        values=["Accuracy", "F1_Score", "Precision", "Recall", "Sensitivity", "Specificity", "ROC_AUC", "Macro_ROC_AUC", "Weighted_ROC_AUC"]
    )
    
    print("\n======================= FINAL FEATURE REDUCTION EVALUATION REPORT =======================")
    print(performance_pivot.to_string())
    print("\n[Data Export] CSV metric tables generated: 'feature_reduction_performance.csv'")
else:
    print("\n[Execution Warning] No classifiers could be trained. Check target distributions.")