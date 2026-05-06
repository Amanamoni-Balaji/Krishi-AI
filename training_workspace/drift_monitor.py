"""
Data drift monitor using Evidently AI.
Compares recent prediction inputs against the training distribution.

Run standalone:  python drift_monitor.py
Or imported by Flask app via run_drift_check()
"""

import os
import json
import datetime
import pandas as pd

TRAINING_DATA = os.path.join(os.path.dirname(__file__), 'final_training_data.csv')
PRED_LOG      = os.path.join(os.path.dirname(__file__), '..', 'prediction_log.jsonl')
DRIFT_CACHE   = os.path.join(os.path.dirname(__file__), '..', 'drift_report.json')

FEATURES = ['Area', 'Rainfall']  # numerical features to check drift on


def _load_prediction_log(n=200):
    """Load last n entries from prediction_log.jsonl."""
    path = os.path.abspath(PRED_LOG)
    if not os.path.exists(path):
        return pd.DataFrame()
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows[-n:])


def run_drift_check():
    """
    Run drift detection and return a JSON-serialisable report dict.
    Uses Evidently if available, falls back to a statistical summary.
    """
    ref_df     = pd.read_csv(TRAINING_DATA)
    current_df = _load_prediction_log()

    n_current = len(current_df)
    timestamp = datetime.datetime.now().isoformat()

    if n_current < 10:
        report = {
            'timestamp':    timestamp,
            'status':       'insufficient_data',
            'message':      f'Only {n_current} prediction(s) logged. Need ≥10 to detect drift.',
            'n_current':    n_current,
            'features':     {},
        }
        _cache(report)
        return report

    # ── Try Evidently ──────────────────────────────────────────────────────────
    try:
        from evidently.report import Report
        from evidently.metric_preset import DataDriftPreset

        ref_subset     = ref_df[FEATURES].copy()
        current_subset = current_df[FEATURES].copy()

        drift_report = Report(metrics=[DataDriftPreset()])
        drift_report.run(reference_data=ref_subset, current_data=current_subset)

        result_dict = drift_report.as_dict()
        metrics     = result_dict['metrics']

        # Parse per-feature drift results
        feature_results = {}
        dataset_drift   = False

        for metric in metrics:
            if metric.get('metric') == 'DatasetDriftMetric':
                dataset_drift = metric['result'].get('dataset_drift', False)

            if metric.get('metric') == 'ColumnDriftMetric':
                col    = metric['result']['column_name']
                drifted = metric['result']['drift_detected']
                score  = round(metric['result'].get('stattest_threshold', 0.05), 4)
                pval   = round(metric['result'].get('p_value', 1.0), 4)
                feature_results[col] = {
                    'drifted':  drifted,
                    'p_value':  pval,
                    'status':   'red' if drifted else ('amber' if pval < 0.15 else 'green'),
                }

        report = {
            'timestamp':      timestamp,
            'status':         'drift_detected' if dataset_drift else 'ok',
            'dataset_drifted': dataset_drift,
            'n_reference':    len(ref_subset),
            'n_current':      n_current,
            'features':       feature_results,
            'engine':         'evidently',
        }

    except ImportError:
        # ── Fallback: KS-test via scipy ────────────────────────────────────────
        from scipy import stats

        feature_results = {}
        any_drift = False

        for col in FEATURES:
            if col not in current_df.columns or col not in ref_df.columns:
                continue
            ref_vals = ref_df[col].dropna().values
            cur_vals = current_df[col].dropna().values
            if len(cur_vals) == 0:
                continue

            ks_stat, p_val = stats.ks_2samp(ref_vals, cur_vals)
            drifted = p_val < 0.05
            any_drift = any_drift or drifted

            feature_results[col] = {
                'drifted':  bool(drifted),
                'p_value':  round(float(p_val), 4),
                'ks_stat':  round(float(ks_stat), 4),
                'status':   'red' if drifted else ('amber' if p_val < 0.15 else 'green'),
            }

        report = {
            'timestamp':       timestamp,
            'status':          'drift_detected' if any_drift else 'ok',
            'dataset_drifted': any_drift,
            'n_reference':     len(ref_df),
            'n_current':       n_current,
            'features':        feature_results,
            'engine':          'scipy_ks',
        }

    _cache(report)
    return report


def _cache(report):
    with open(os.path.abspath(DRIFT_CACHE), 'w') as f:
        json.dump(report, f, indent=2)


def load_cached():
    path = os.path.abspath(DRIFT_CACHE)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


if __name__ == '__main__':
    print("Running drift check...")
    result = run_drift_check()
    print(json.dumps(result, indent=2))
