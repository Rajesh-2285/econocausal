"""
EconoCausal - FastAPI Backend Service & Dashboard Serving Layer
Provides health diagnostics, static dashboard rendering, and real-time
constrained SciPy linear programming budget allocation endpoints.
"""

import os
from typing import Optional, List
import numpy as np
import pandas as pd
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from scipy.optimize import linprog

# ---------------------------------------------------------
# App Initialization & Templates
# ---------------------------------------------------------
app = FastAPI(
    title="econocausal API",
    description="Causal Machine Learning & Constrained Uplift Budget Optimization Platform",
    version="1.0.0"
)

# Resolve templates directory relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ---------------------------------------------------------
# Data Artifact Loader
# ---------------------------------------------------------
def load_customer_data() -> pd.DataFrame:
    """Load benchmark dataset containing ITE uplift scores."""
    candidate_paths = [
        os.path.join(os.path.dirname(BASE_DIR), "data", "customer_ite_scores.csv"),
        os.path.join(BASE_DIR, "retail_data.csv"),
        os.path.join(os.path.dirname(BASE_DIR), "backend", "retail_data.csv")
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            # Ensure uplift column exists
            if "ite_score" not in df.columns:
                if "ite" in df.columns:
                    df["ite_score"] = df["ite"]
                elif "predicted_ite" in df.columns:
                    df["ite_score"] = df["predicted_ite"]
                else:
                    # Fallback uplift assignment if synthetic base
                    np.random.seed(42)
                    df["ite_score"] = np.random.normal(loc=0.06, scale=0.03, size=len(df))
            return df
    raise FileNotFoundError("Customer data artifact could not be located.")

# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class OptimizationRequest(BaseModel):
    budget: float = 10000.0
    cost_per_contact: float = 1.50
    channel_filter: Optional[str] = "All"

class OptimizationResponse(BaseModel):
    status: str
    total_customers_evaluated: int
    targeted_customers_count: int
    budget_allocated: float
    total_expected_incremental_conversions: float
    efficiency_gain_vs_random: float
    decile_uplift_distribution: List[float]

# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serve the complete frontend dashboard UI."""
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/health")
def health_check():
    """Service health and diagnostics check."""
    data_loaded = True
    try:
        df = load_customer_data()
        total_records = len(df)
    except Exception:
        data_loaded = False
        total_records = 0

    return {
        "status": "healthy",
        "service": "econocausal-backend",
        "dataset_ready": data_loaded,
        "total_records_available": total_records,
        "solver": "scipy-highs"
    }

@app.post("/api/optimize", response_model=OptimizationResponse)
def run_budget_optimization(payload: OptimizationRequest):
    """
    Executes SciPy Linear Programming (HiGHS) to maximize incremental
    conversions subject to budget constraints:
      max sum(ITE_i * x_i) subject to sum(cost_i * x_i) <= budget
    """
    try:
        df = load_customer_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Optional channel filtering
    if payload.channel_filter and payload.channel_filter != "All" and "channel" in df.columns:
        df = df[df["channel"].str.lower() == payload.channel_filter.lower()].reset_index(drop=True)

    total_eval = len(df)
    if total_eval == 0:
        raise HTTPException(status_code=400, detail="No customer records match filter criteria.")

    max_contacts = int(payload.budget / max(payload.cost_per_contact, 0.01))
    max_contacts = min(max_contacts, total_eval)

    # SciPy linprog formulation: Minimize -sum(ITE_i * x_i)
    c = -df["ite_score"].values
    A = np.ones((1, total_eval))
    b = np.array([max_contacts])
    bounds = [(0, 1) for _ in range(total_eval)]

    res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

    if not res.success:
        raise HTTPException(status_code=500, detail="SciPy solver failed to find feasible allocation.")

    selected_mask = res.x > 0.5
    targeted_count = int(np.sum(selected_mask))
    expected_conversions = float(np.sum(df.loc[selected_mask, "ite_score"]))
    actual_spend = targeted_count * payload.cost_per_contact

    # Compute uplift decile distribution (10 bins)
    df["decile"] = pd.qcut(df["ite_score"], q=10, labels=False, duplicates="drop")
    decile_uplift = (
        df.groupby("decile", observed=False)["ite_score"]
        .mean()
        .sort_index(ascending=False)
        .round(4)
        .tolist()
    )

    # Random baseline benchmark
    np.random.seed(42)
    random_sample = df["ite_score"].sample(n=targeted_count, random_state=42).sum()
    efficiency = round(expected_conversions / max(float(random_sample), 1e-5), 2)

    return OptimizationResponse(
        status="SUCCESS",
        total_customers_evaluated=total_eval,
        targeted_customers_count=targeted_count,
        budget_allocated=round(actual_spend, 2),
        total_expected_incremental_conversions=round(expected_conversions, 2),
        efficiency_gain_vs_random=efficiency,
        decile_uplift_distribution=decile_uplift
    )