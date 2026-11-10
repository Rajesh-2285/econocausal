"""
EconoCausal - Automated Data & Behavioral Drift Detector
Infotact Solutions - Week 4 Specification Requirement
Monitors incoming customer feature distributions against baseline observational data
using Kolmogorov-Smirnov (KS) tests and Population Stability Index (PSI).
"""

import os
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

def calculate_psi(baseline: np.ndarray, current: np.ndarray, num_bins: int = 10) -> float:
    """Calculate Population Stability Index (PSI) between baseline and current distributions."""
    baseline = baseline[~np.isnan(baseline)]
    current = current[~np.isnan(current)]
    
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(baseline, percentiles)
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
    current_counts, _ = np.histogram(current, bins=bin_edges)

    baseline_pct = np.clip(baseline_counts / len(baseline), 1e-4, 1.0)
    current_pct = np.clip(current_counts / len(current), 1e-4, 1.0)

    psi_val = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
    return float(psi_val)

def check_feature_drift(baseline_df: pd.DataFrame, current_df: pd.DataFrame, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Evaluates continuous features for statistical distribution shifts.
    Flags features where p-value < alpha (KS Test) or PSI > 0.10.
    """
    monitored_cols = [c for c in ["recency", "history", "ite_score"] if c in baseline_df.columns and c in current_df.columns]
    
    drift_report: Dict[str, Any] = {
        "status": "PASS",
        "total_features_evaluated": len(monitored_cols),
        "drifted_features": [],
        "metrics": {}
    }

    for col in monitored_cols:
        base_series = baseline_df[col].dropna().values
        curr_series = current_df[col].dropna().values

        ks_stat, p_value = ks_2samp(base_series, curr_series)
        psi = calculate_psi(base_series, curr_series)

        has_drift = (p_value < alpha) or (psi > 0.10)
        
        drift_report["metrics"][col] = {
            "ks_statistic": round(float(ks_stat), 4),
            "p_value": round(float(p_value), 5),
            "psi": round(float(psi), 4),
            "drift_detected": bool(has_drift),
            "status": "ALERT - DRIFT DETECTED" if has_drift else "STABLE"
        }

        if has_drift:
            drift_report["drifted_features"].append(col)

    if drift_report["drifted_features"]:
        drift_report["status"] = "WARNING_DRIFT_DETECTED"

    return drift_report

def run_drift_diagnostic():
    print("=" * 65)
    print("ECONOCAUSAL: AUTOMATED DATA DRIFT MONITOR")
    print("=" * 65)

    data_path = os.path.join("backend", "retail_data.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join("data", "customer_ite_scores.csv")

    if not os.path.exists(data_path):
        print("[FAIL] Baseline dataset not found.")
        return

    df = pd.read_csv(data_path)
    df.columns = [c.lower() for c in df.columns]

    if "ite_score" not in df.columns:
        np.random.seed(42)
        df["ite_score"] = np.random.normal(loc=0.0639, scale=0.03, size=len(df))

    # Split baseline vs simulated incoming live production batch
    split_idx = int(len(df) * 0.7)
    baseline_df = df.iloc[:split_idx].copy()
    
    # Simulate a sudden market shift on recency and spending for the test
    current_df = df.iloc[split_idx:].copy()
    current_df["history"] = current_df["history"] * 1.35  # 35% inflation in customer basket size

    report = check_feature_drift(baseline_df, current_df)

    print(f"Overall System Status: {report['status']}")
    print(f"Features Evaluated:   {report['total_features_evaluated']}")
    print(f"Drifted Features:     {report['drifted_features']}\n")

    for feat, metrics in report["metrics"].items():
        print(f" - [{feat.upper()}] Status: {metrics['status']}")
        print(f"    KS-Stat: {metrics['ks_statistic']} | p-val: {metrics['p_value']} | PSI: {metrics['psi']}")
    print("=" * 65)

if __name__ == "__main__":
    run_drift_diagnostic()