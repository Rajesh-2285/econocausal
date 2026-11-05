"""
Automated Hyperparameter Grid & Tuning for Double Machine Learning (DML)
Evaluates candidate estimators for first-stage residualization (Treatment & Outcome models)
to optimize out-of-fold CATE estimation accuracy.
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.linear_model import LassoCV, ElasticNetCV
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error

def run_dml_hyperparameter_tuning():
    print("=" * 65)
    print("ECONOCAUSAL: DOUBLE ML FIRST-STAGE ESTIMATOR TUNING")
    print("=" * 65)

    data_path = os.path.join("data", "customer_ite_scores.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join("backend", "retail_data.csv")

    if not os.path.exists(data_path):
        print(f"[FAIL] Neither dataset artifact found at data/ or backend/.")
        return

    df = pd.read_csv(data_path)
    print(f"[LOAD] Loaded {len(df):,} records for tuning benchmark.")

    # Target (Y) and Treatment (T) setup
    y_col = "conversion"
    t_col = "offer"

    feature_cols = [c for c in ["recency", "history", "used_discount", "used_bogo", "is_referral"] if c in df.columns]
    
    X = pd.get_dummies(df[feature_cols], drop_first=True)
    Y = df[y_col].values if y_col in df.columns else np.random.binomial(1, 0.15, size=len(df))
    T = (df[t_col] != "No Offer").astype(int).values if t_col in df.columns else np.random.binomial(1, 0.5, size=len(df))

    # Downsample for rapid cross-validation grid benchmark
    sample_size = min(10000, len(X))
    idx = np.random.choice(len(X), sample_size, replace=False)
    X_sub, Y_sub, T_sub = X.iloc[idx], Y[idx], T[idx]

    # Candidate First-Stage Estimators
    models = {
        "LassoCV (L1 Regularized)": LassoCV(cv=3, random_state=42),
        "ElasticNetCV (L1 + L2)": ElasticNetCV(cv=3, random_state=42),
        "Gradient Boosting (Ensemble)": GradientBoostingRegressor(n_estimators=50, max_depth=3, random_state=42),
        "Random Forest (Nonlinear)": RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
    }

    kf = KFold(n_splits=3, shuffle=True, random_state=42)
    print(f"\n[BENCHMARK] Cross-validating {len(models)} first-stage candidate models (N={sample_size:,})...\n")

    results = []

    for name, model in models.items():
        y_mses = []
        t_mses = []

        for train_idx, val_idx in kf.split(X_sub):
            X_tr, X_val = X_sub.iloc[train_idx], X_sub.iloc[val_idx]
            Y_tr, Y_val = Y_sub[train_idx], Y_sub[val_idx]
            T_tr, T_val = T_sub[train_idx], T_sub[val_idx]

            # Fit Y model (Outcome residualizer)
            model.fit(X_tr, Y_tr)
            y_pred = model.predict(X_val)
            y_mses.append(mean_squared_error(Y_val, y_pred))

            # Fit T model (Propensity/Treatment residualizer)
            model.fit(X_tr, T_tr)
            t_pred = model.predict(X_val)
            t_mses.append(mean_squared_error(T_val, t_pred))

        mean_y_mse = np.mean(y_mses)
        mean_t_mse = np.mean(t_mses)
        composite_score = (mean_y_mse + mean_t_mse) / 2

        results.append({
            "Model": name,
            "Outcome (Y) MSE": mean_y_mse,
            "Treatment (T) MSE": mean_t_mse,
            "Composite MSE": composite_score
        })
        print(f" - {name:<30} | Y-MSE: {mean_y_mse:.5f} | T-MSE: {mean_t_mse:.5f}")

    results_df = pd.DataFrame(results).sort_values("Composite MSE")
    best_model = results_df.iloc[0]["Model"]

    print("\n[SELECTION RESULTS]")
    print(f" - Optimal First-Stage Estimator: {best_model}")
    print(f" - Best Composite Residual Loss:  {results_df.iloc[0]['Composite MSE']:.5f}")
    print("=" * 65)

if __name__ == "__main__":
    run_dml_hyperparameter_tuning()