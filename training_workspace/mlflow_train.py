"""
MLflow-instrumented training script for the Smart Agriculture yield model.
Run:  python mlflow_train.py
Then: mlflow ui  (opens experiment dashboard at http://127.0.0.1:5001)
"""

import os
import sys
import datetime
import pandas as pd
import numpy as np
import pickle
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# ── Config ─────────────────────────────────────────────────────────────────────
DATA_PATH   = os.path.join(os.path.dirname(__file__), 'final_training_data.csv')
MODEL_NAME  = 'agriculture-yield-model'
MLFLOW_URI  = os.environ.get('MLFLOW_TRACKING_URI', 'mlruns')

PARAMS = {
    'n_estimators':  200,
    'learning_rate': 0.1,
    'max_depth':     5,
    'random_state':  42,
}


def train():
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment('agriculture-yield-prediction')

    df = pd.read_csv(DATA_PATH)
    n_samples = len(df)
    print(f"Loaded {n_samples} training records.")

    # ── Encode ─────────────────────────────────────────────────────────────────
    le_district = LabelEncoder()
    le_season   = LabelEncoder()
    le_crop     = LabelEncoder()

    df['District_Encoded'] = le_district.fit_transform(df['District_Name'])
    df['Season_Encoded']   = le_season.fit_transform(df['Season'])
    df['Crop_Encoded']     = le_crop.fit_transform(df['Crop'])

    scaler = StandardScaler()
    df[['Area', 'Rainfall']] = scaler.fit_transform(df[['Area', 'Rainfall']])

    X = df[['District_Encoded', 'Season_Encoded', 'Crop_Encoded', 'Area', 'Rainfall']]
    y = np.log1p(df['Production'])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    with mlflow.start_run() as run:
        # ── Log params ─────────────────────────────────────────────────────────
        mlflow.log_params(PARAMS)
        mlflow.set_tags({
            'training_date': datetime.datetime.now().isoformat(),
            'n_samples':     str(n_samples),
            'model_type':    'GradientBoostingRegressor',
            'target':        'log1p(Production)',
            'region':        'Meghalaya',
        })

        # ── Train ──────────────────────────────────────────────────────────────
        model = GradientBoostingRegressor(**PARAMS)
        model.fit(X_train, y_train)

        # ── Evaluate ───────────────────────────────────────────────────────────
        y_pred_log  = model.predict(X_test)
        y_pred      = np.expm1(y_pred_log)
        y_test_act  = np.expm1(y_test)

        r2   = r2_score(y_test_act, y_pred)
        mae  = mean_absolute_error(y_test_act, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test_act, y_pred))

        mlflow.log_metrics({'r2': round(r2, 4), 'mae': round(mae, 2), 'rmse': round(rmse, 2)})

        print(f"R²: {r2:.4f}  |  MAE: {mae:.2f}  |  RMSE: {rmse:.2f}")

        # ── Log model to MLflow ────────────────────────────────────────────────
        mlflow.sklearn.log_model(
            model,
            artifact_path='model',
            registered_model_name=MODEL_NAME,
        )

        # ── Save .pkl files for Flask backend ──────────────────────────────────
        root = os.path.dirname(__file__)
        with open(os.path.join(root, 'agriculture_model_improved.pkl'), 'wb') as f:
            pickle.dump(model, f)
        with open(os.path.join(root, 'label_encoders_improved.pkl'), 'wb') as f:
            pickle.dump({'district': le_district, 'season': le_season,
                         'crop': le_crop, 'scaler': scaler}, f)

        # ── Save model_info.json for Flask /model-info endpoint ────────────────
        import json
        info = {
            'run_id':        run.info.run_id,
            'model_name':    MODEL_NAME,
            'training_date': datetime.datetime.now().isoformat(),
            'n_samples':     n_samples,
            'r2':            round(r2, 4),
            'mae':           round(mae, 2),
            'rmse':          round(rmse, 2),
            'params':        PARAMS,
        }
        with open(os.path.join(os.path.dirname(root), 'model_info.json'), 'w') as f:
            json.dump(info, f, indent=2)

        print(f"MLflow run ID: {run.info.run_id}")
        print("Saved model_info.json, agriculture_model_improved.pkl, label_encoders_improved.pkl")
        return info


if __name__ == '__main__':
    result = train()
    print("\nDone. Run 'mlflow ui --port 5001' to view the experiment dashboard.")
