# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import ClassifierChain
from xgboost import XGBClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import MultiLabelBinarizer
import re

def load_and_preprocess(filepath):
    df = pd.read_csv(filepath, encoding="utf-8")
    df.columns = [col.strip() for col in df.columns]
    df = df.drop(columns=["Birthdate", "ID"])
    df["Malnutrition Type"] = df["Malnutrition Type"].apply(
        lambda x: [s.strip() for s in re.split('[,و]', str(x))] if pd.notna(x) else []
    )
    return df

def filter_rare_classes(y, min_samples=2):
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
    
    # Filter classes with <2 samples
    y, valid_cols = filter_rare_classes(y)
    if y.shape[1] == 0:
        raise ValueError("No classes with sufficient samples after filtering.")
    class_names = mlb.classes_[valid_cols]
    
    # Remove samples with no remaining labels
    has_labels = y.sum(axis=1) > 0
    X = X[has_labels]
    y = y[has_labels]
    
    # Train-test split without stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Build pipeline
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, X.select_dtypes(include=np.number).columns)
        ])
    
    # Use a single XGBClassifier as the base_estimator
    base_estimator = XGBClassifier(
        eval_metric='logloss',
        use_label_encoder=False
    )
    
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', ClassifierChain(base_estimator=base_estimator))
    ])
    
    # Train model
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(X_test)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names))
    
if __name__ == "__main__":
    main()