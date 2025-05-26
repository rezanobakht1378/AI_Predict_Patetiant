# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import ClassifierChain
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, multilabel_confusion_matrix
from sklearn.preprocessing import MultiLabelBinarizer
#from imblearn.over_sampling import RandomOverSampler

def load_and_preprocess(filepath):
    df = pd.read_csv(filepath, encoding="utf-8", low_memory=False)
    df.columns = [col.strip() for col in df.columns]
    df = df.drop(columns=["Birthdate", "ID"])
    df["Malnutrition Type"] = df["Malnutrition Type"].apply(
        lambda x: [s.strip() for s in re.split('[,و]', str(x))] if pd.notna(x) else []
    )
    return df

def filter_rare_classes(y, min_samples=5):
    column_sums = y.sum(axis=0)
    valid_columns = column_sums >= min_samples
    return y[:, valid_columns], valid_columns

def main():
    # Load and preprocess data
    df = load_and_preprocess('patient.csv')

    # Handle multi-label target
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(df["Malnutrition Type"])
    X = df.drop(columns=["Malnutrition Type"])

    # Filter rare classes
    y, valid_cols = filter_rare_classes(y, min_samples=2)
    if y.shape[1] == 0:
        raise ValueError("No classes with sufficient samples after filtering.")
    class_names = mlb.classes_[valid_cols]

    # Remove samples with no remaining labels
    has_labels = y.sum(axis=1) > 0
    X = X[has_labels].reset_index(drop=True)
    y = y[has_labels]

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Oversample minority classes (multi-label aware)
    #ros = RandomOverSampler(random_state=42)
    #X_train_resampled, y_train_resampled = ros.fit_resample(X_train, y_train)
    X_train_resampled, y_train_resampled = X_train, y_train
    # Build numeric transformer
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, X.select_dtypes(include=np.number).columns)
        ])

    # XGBoost with balanced weight
    base_estimator = XGBClassifier(
        eval_metric='logloss',
        use_label_encoder=False,
        scale_pos_weight=1  # Let RandomOverSampler handle class balance
    )

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', ClassifierChain(base_estimator=base_estimator))
    ])

    # Train model
    pipeline.fit(X_train_resampled, y_train_resampled)

    # Predict
    y_pred = pipeline.predict(X_test)

    # Evaluate
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names))

    # Confusion Matrix per class
    print("\n📉 Confusion Matrix for each class:")
    cm = multilabel_confusion_matrix(y_test, y_pred)
    for i, matrix in enumerate(cm):
        print(f"\nClass: {class_names[i]}")
        print(matrix)

if __name__ == "__main__":
    main()
