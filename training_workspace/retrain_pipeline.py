"""
Automated retraining pipeline.
- Trains a new model on the current dataset
- Compares R² against the currently deployed model (from model_info.json)
- Upgrades if new model is meaningfully better (delta > UPGRADE_THRESHOLD)
- Copies new .pkl files and updates model_info.json if upgraded

Run:  python retrain_pipeline.py
Returns JSON to stdout: {"status": "upgraded"|"kept", "new_r2": ..., "old_r2": ...}
"""

import os
import sys
import json
import datetime
import shutil
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

ROOT           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE      = os.path.dirname(os.path.abspath(__file__))
DATA_PATH      = os.path.join(WORKSPACE, 'final_training_data.csv')
MODEL_INFO     = os.path.join(ROOT, 'model_info.json')
MODEL_PKL      = os.path.join(WORKSPACE, 'agriculture_model_improved.pkl')
ENCODERS_PKL   = os.path.join(WORKSPACE, 'label_encoders_improved.pkl')
UPGRADE_THRESHOLD = 0.005   # upgrade if R² improves by at least 0.5%


def _get_current_r2():
    if os.path.exists(MODEL_INFO):
        with open(MODEL_INFO) as f:
            info = json.load(f)
        return info.get('r2', 0.0), info
    return 0.0, {}


def _train_and_eval():
    df = pd.read_csv(DATA_PATH)
    n_samples = len(df)

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

    params = {'n_estimators': 200, 'learning_rate': 0.1, 'max_depth': 5, 'random_state': 42}
    model  = GradientBoostingRegressor(**params)
    model.fit(X_train, y_train)

    y_pred    = np.expm1(model.predict(X_test))
    y_test_a  = np.expm1(y_test)

    r2   = round(float(r2_score(y_test_a, y_pred)), 4)
    mae  = round(float(mean_absolute_error(y_test_a, y_pred)), 2)
    rmse = round(float(np.sqrt(mean_squared_error(y_test_a, y_pred))), 2)

    encoders = {'district': le_district, 'season': le_season, 'crop': le_crop, 'scaler': scaler}
    return model, encoders, {'r2': r2, 'mae': mae, 'rmse': rmse, 'n_samples': n_samples, 'params': params}


def run():
    old_r2, old_info = _get_current_r2()
    print(f"Current deployed model R²: {old_r2}")

    model, encoders, metrics = _train_and_eval()
    new_r2 = metrics['r2']
    print(f"New model R²:              {new_r2}")

    delta = new_r2 - old_r2
    upgraded = delta >= UPGRADE_THRESHOLD

    result = {
        'status':    'upgraded' if upgraded else 'kept',
        'new_r2':    new_r2,
        'old_r2':    old_r2,
        'delta_r2':  round(delta, 4),
        'new_mae':   metrics['mae'],
        'new_rmse':  metrics['rmse'],
        'n_samples': metrics['n_samples'],
        'timestamp': datetime.datetime.now().isoformat(),
        'reason':    (
            f"Improved R² by {delta:.4f} — upgrading model."
            if upgraded else
            f"No meaningful improvement (delta={delta:.4f} < threshold={UPGRADE_THRESHOLD})."
        ),
    }

    if upgraded:
        # Backup old model
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        for path in [MODEL_PKL, ENCODERS_PKL]:
            if os.path.exists(path):
                backup = path.replace('.pkl', f'_backup_{ts}.pkl')
                shutil.copy2(path, backup)

        # Save new model
        with open(MODEL_PKL, 'wb') as f:
            pickle.dump(model, f)
        with open(ENCODERS_PKL, 'wb') as f:
            pickle.dump(encoders, f)

        # Update model_info.json
        new_info = {
            'run_id':        f'local_{ts}',
            'model_name':    'agriculture-yield-model',
            'training_date': result['timestamp'],
            'n_samples':     metrics['n_samples'],
            'r2':            new_r2,
            'mae':           metrics['mae'],
            'rmse':          metrics['rmse'],
            'params':        metrics['params'],
            'version':       (old_info.get('version', 1) + 1),
        }
        with open(MODEL_INFO, 'w') as f:
            json.dump(new_info, f, indent=2)

        print("Model upgraded and saved.")
    else:
        print("Keeping current model.")

    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    run()
