"""
Exploratory Data Analysis (EDA) & Channel Uplift Summary
Generates empirical conversion benchmarks across marketing channels,
discount types, and customer recency bins to support causal analysis.
"""

import os
import pandas as pd
import numpy as np

def generate_eda_report():
    print("=" * 65)
    print("ECONOCAUSAL: EXPLORATORY DATA ANALYSIS & CHANNEL SUMMARY")
    print("=" * 65)

    data_path = os.path.join("data", "customer_ite_scores.csv")
    if not os.path.exists(data_path):
        print(f"[FAIL] Data artifact {data_path} not found.")
        return

    df = pd.read_csv(data_path)
    total_records = len(df)
    print(f"[LOAD] Analyzing {total_records:,} customer records.\n")

    # 1. Overall Conversion & Offer Metrics
    overall_conv = df["conversion"].mean() * 100 if "conversion" in df.columns else 0.0
    print(f"[BENCHMARK] Baseline Conversion Rate: {overall_conv:.2f}%")

    if "offer" in df.columns and "conversion" in df.columns:
        print("\n--- CONVERSION RATE BY OFFER TYPE ---")
        offer_perf = df.groupby("offer")["conversion"].agg(["count", "mean"])
        offer_perf["conversion_pct"] = offer_perf["mean"] * 100
        for offer_name, row in offer_perf.iterrows():
            print(f" - {offer_name:<16}: {int(row['count']):>6,} users | Conv: {row['conversion_pct']:.2f}%")

    # 2. Channel Performance
    if "channel" in df.columns and "conversion" in df.columns:
        print("\n--- CHANNEL CONVERSION PERFORMANCE ---")
        chan_perf = df.groupby("channel")["conversion"].agg(["count", "mean"])
        chan_perf["conversion_pct"] = chan_perf["mean"] * 100
        for chan_name, row in chan_perf.iterrows():
            print(f" - {chan_name:<16}: {int(row['count']):>6,} users | Conv: {row['conversion_pct']:.2f}%")

    # 3. Recency & Spend Tier Analysis
    if "recency" in df.columns and "conversion" in df.columns:
        print("\n--- RECENCY TIER CONVERSION RATES ---")
        df["recency_group"] = pd.cut(df["recency"], bins=[0, 3, 6, 12], labels=["0-3 Months", "4-6 Months", "7+ Months"])
        rec_perf = df.groupby("recency_group", observed=False)["conversion"].mean() * 100
        for group, rate in rec_perf.items():
            print(f" - {group:<16}: Conv: {rate:.2f}%")

    # 4. Causal ITE Summary by Channel
    ite_col = "ite_score" if "ite_score" in df.columns else "ite"
    if ite_col in df.columns and "channel" in df.columns:
        print(f"\n--- MEAN CAUSAL UPLIFT ({ite_col.upper()}) BY CHANNEL ---")
        chan_ite = df.groupby("channel")[ite_col].mean()
        for chan, mean_ite in chan_ite.items():
            print(f" - {chan:<16}: Mean Incremental Uplift = +{mean_ite * 100:.2f}%")

    print("\n[SUMMARY] Empirical EDA complete. Channel heterogeneity confirms need for Causal DML.")
    print("=" * 65)

if __name__ == "__main__":
    generate_eda_report()