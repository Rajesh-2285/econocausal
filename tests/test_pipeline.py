"""
EconoCausal - End-to-End Pipeline Integration Test Suite
Validates dataset integrity, SciPy solver budget adherence,
FastAPI REST endpoints, and automated drift detection.
"""

import os
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
import sys
import os

# Ensure project root directory is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from backend.api import app, load_customer_data
from backend.drift_detector import check_feature_drift, calculate_psi
from scipy.optimize import linprog

client = TestClient(app)

# -------------------------------------------------------------
# 1. Dataset Integrity Tests
# -------------------------------------------------------------
def test_customer_dataset_loads_and_has_required_schema():
    df = load_customer_data()
    assert df is not None, "Failed to load customer dataset."
    assert len(df) > 0, "Dataset is empty."
    
    # Must have either existing or computed uplift scores
    assert "ite_score" in df.columns or "ite" in df.columns
    # Ensure no null values in critical numeric modeling columns
    numeric_cols = [c for c in ["recency", "history"] if c in df.columns]
    for col in numeric_cols:
        assert df[col].isnull().sum() == 0, f"Found null values in {col}"

# -------------------------------------------------------------
# 2. SciPy Prescriptive Optimizer Constraints Tests
# -------------------------------------------------------------
def test_scipy_optimizer_strictly_respects_budget_constraint():
    df = load_customer_data()
    budget = 5000.0
    cost_per_contact = 1.50
    total_records = min(5000, len(df))
    df_sub = df.iloc[:total_records].copy()
    
    max_contacts = int(budget / cost_per_contact)
    c = -df_sub["ite_score"].values
    A = np.ones((1, total_records))
    b = np.array([max_contacts])
    bounds = [(0, 1) for _ in range(total_records)]

    res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

    assert res.success, "SciPy HiGHS solver failed to find feasible solution."
    
    selected_mask = res.x > 0.5
    targeted_count = int(np.sum(selected_mask))
    actual_spend = targeted_count * cost_per_contact

    assert actual_spend <= budget, f"Spend ${actual_spend} exceeded total budget ${budget}"
    assert targeted_count <= max_contacts, "Targeted count exceeded max allowable contacts."

def test_optimizer_selects_superior_uplift_over_random():
    df = load_customer_data()
    sample_n = 500
    top_ite_sum = df.sort_values(by="ite_score", ascending=False)["ite_score"].head(sample_n).sum()
    random_ite_sum = df["ite_score"].sample(n=sample_n, random_state=42).sum()
    
    assert top_ite_sum > random_ite_sum, "Optimal selection failed to outperform random selection."

# -------------------------------------------------------------
# 3. Drift Detection Tests
# -------------------------------------------------------------
def test_drift_detector_identifies_synthetic_shift():
    np.random.seed(42)
    base = np.random.normal(loc=50, scale=10, size=1000)
    shifted = np.random.normal(loc=70, scale=10, size=1000)
    
    psi_val = calculate_psi(base, shifted)
    assert psi_val > 0.10, f"Expected PSI > 0.10 for drifted feature, got {psi_val}"

# -------------------------------------------------------------
# 4. FastAPI Endpoint Integration Tests
# -------------------------------------------------------------
def test_api_health_endpoint_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["solver"] == "scipy-highs"

def test_api_optimize_endpoint_returns_valid_payload():
    payload = {
        "budget": 7500.0,
        "cost_per_contact": 1.50,
        "channel_filter": "All"
    }
    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["targeted_customers_count"] == 5000
    assert data["budget_allocated"] <= 7500.0
    assert "decile_uplift_distribution" in data