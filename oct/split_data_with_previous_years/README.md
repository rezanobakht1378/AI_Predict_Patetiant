Pipeline to train and evaluate models predicting next-age z-scores

Files added:
- train_and_evaluate.py : main script to run the pipeline
- requirements.txt : Python dependencies

How to run (Windows PowerShell):
1. Create / activate a virtual environment (optional):
   python -m venv .venv; .\.venv\Scripts\Activate.ps1
2. Install dependencies:
   pip install -r requirements.txt
3. Run the pipeline from the project folder:
   python train_and_evaluate.py

Outputs:
- pipeline_outputs/metrics_summary_<_transition_>.csv : per-transition metrics (one CSV per transition)
- pipeline_outputs/predictions_<transition>_<measure>_<model>.csv : per-sample predictions
- pipeline_outputs/best_models_<transition>.csv : selected best model per measure for that transition
- pipeline_outputs/metrics_summary_all_transitions.csv : combined metrics across transitions

Notes and caveats:
- The script looks for z-score columns (BMI, height, weight) in the CSVs. If those z-score columns are missing, that target will be skipped.
- Data cleaning is minimal; some columns may contain non-numeric tokens (#VALUE!, commas, etc.) that are coerced to numeric where possible.
- If XGBoost is not installed or fails to import, the script will continue without XGBoost models.

Next steps:
- Run the script and inspect pipeline_outputs. If many measures were skipped, inspect CSV headers and adapt the column-finding heuristics in `train_and_evaluate.py`.
- Optionally add stricter preprocessing, feature engineering, hyperparameter tuning, or cross-validation.
