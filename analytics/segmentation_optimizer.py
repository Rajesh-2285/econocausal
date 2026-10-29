"""
Customer Segmentation & Constrained SciPy Budget Allocation
Categorizes users into Uplift Quadrants (Persuadables, Sure Things, Lost Causes, Sleeping Dogs)
and executes mathematical budget optimization to maximize incremental business ROI.
"""

import os
import numpy as np
import pandas as pd
from scipy.optimize import linprog

def segment_and_optimize():
    print("=" * 65)
    print("ECONOCAUSAL: CUSTOMER SEGMENTATION & ROI OPTIMIZATION")
    print("=" * 65)

    data_path = os.path.join("data", "customer_ite_scores.csv")
    if not os.path.exists(data_path):
        print(f"[FAIL] Data artifact {data_path} not found.")
        return

    df = pd.read_csv(data_path)
    total_customers = len(df)
    print(f"[LOAD] Loaded {total_customers:,} customer records.")

    # Locate ITE uplift column
    possible_cols = ["ite_score", "ite", "predicted_ite"]
    ite_col = next((c for c in possible_cols if c in df.columns), None)
    if not ite_col:
        print("[FAIL] No ITE column found in customer scores.")
        return
    print(f"[INFO] Using uplift column: '{ite_col}'")

    # 1. 4-Quadrant Customer Segmentation
    # High ITE (>0.05) -> Persuadables
    # Low ITE with baseline conversion -> Sure Things
    # Negative ITE (< -0.01) -> Sleeping Dogs / Do Not Disturb
    # Neutral/Zero ITE -> Lost Causes
    conditions = [
        (df[ite_col] > 0.04),
        (df[ite_col] < -0.01),
        (df[ite_col] <= 0.04) & (df[ite_col] >= 0.01)
    ]
    choices = ["Persuadables", "Sleeping Dogs", "Sure Things"]
    df["segment"] = np.select(conditions, choices, default="Lost Causes")

    segment_counts = df["segment"].value_counts()
    print("\n[SEGMENTATION BREAKDOWN]")
    for seg, count in segment_counts.items():
        pct = (count / total_customers) * 100
        print(f" - {seg:<15}: {count:,} ({pct:.1f}%)")

    # 2. SciPy Linear Programming Optimization
    # Maximize total incremental uplift subject to budget constraint
    campaign_budget = 10000.0   # $10,000 total budget
    cost_per_contact = 1.50     # $1.50 per customer outreach
    max_contacts = int(campaign_budget / cost_per_contact)

    # Objective: Maximize sum(ITE_i * x_i)  => Minimize -sum(ITE_i * x_i)
    c = -df[ite_col].values
    
    # Constraint: sum(x_i) <= max_contacts
    A = np.ones((1, total_customers))
    b = np.array([max_contacts])

    bounds = [(0, 1) for _ in range(total_customers)]

    print(f"\n[SOLVER] Optimizing budget: ${campaign_budget:,.2f} (Max targeted: {max_contacts:,})")
    res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

    if res.success:
        selected_mask = res.x > 0.5
        targeted_count = int(np.sum(selected_mask))
        incremental_conversions = float(np.sum(df.loc[selected_mask, ite_col]))
        actual_spend = targeted_count * cost_per_contact

        print("\n[OPTIMIZATION & ROI RESULTS]")
        print(f" - Solver Status:                SUCCESS")
        print(f" - Targeted Customers:           {targeted_count:,} / {total_customers:,}")
        print(f" - Total Budget Allocated:       ${actual_spend:,.2f}")
        print(f" - Expected Incremental Uplift:  +{incremental_conversions:,.1f} conversions")
        
        # Benchmark vs Random Selection
        random_uplift = df[ite_col].sample(n=targeted_count, random_state=42).sum()
        lift_multiplier = (incremental_conversions / max(random_uplift, 1e-5))
        print(f" - Uplift vs. Random Campaign:   {lift_multiplier:.2f}x efficiency gain")
    else:
        print("[FAIL] Optimization routine failed.")
    print("=" * 65)

if __name__ == "__main__":
    segment_and_optimize()