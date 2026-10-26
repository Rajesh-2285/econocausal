import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="EconoCausal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptimizeRequest(BaseModel):
    budget: float = 10000.0
    max_offer_cost: float = 20.0
    target_group: str = "all"
    rows: List[Dict[str, Any]] = []
    columns: List[str] = []
@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/optimize")
def optimize_campaign(req: OptimizeRequest):
    scores_path = "data/customer_ite_scores.csv"

    # 1. Load real precomputed ITE scores or compute mock baseline if not present
    if os.path.exists(scores_path):
        df = pd.read_csv(scores_path)
    else:
        # Fallback if Double ML scores have not been generated yet
        df = pd.DataFrame({
            "history": np.random.uniform(50, 500, 1000),
            "ite_score": np.random.normal(0.0639, 0.02, 1000)
        })

    # Ensure customer identifier exists
    if "customer_id" not in df.columns:
        df["customer_id"] = [f"C{i+1:05d}" for i in range(len(df))]

    # 2. Rank customers by highest causal treatment effect
    sorted_df = df.sort_values(by="ite_score", ascending=False).reset_index(drop=True)

    # 3. Constrained Budget Allocation
    cost_per_offer = req.max_offer_cost if req.max_offer_cost > 0 else 20.0
    max_targets = int(req.budget / cost_per_offer) if req.budget > 0 else len(sorted_df)
    targeted_df = sorted_df.iloc[:max_targets]

    # 4. Generate Qini / Uplift Gain Curve coordinates
    deciles = np.linspace(0.0, 1.0, 11)
    x_curve = [round(float(q), 2) for q in deciles]
    total_ite = float(sorted_df["ite_score"].sum())

    model_curve = [0.0]
    for q in deciles[1:]:
        cutoff = int(q * len(sorted_df))
        model_curve.append(round(float(sorted_df.iloc[:cutoff]["ite_score"].sum()), 4))

    random_curve = [round(float(q * total_ite), 4) for q in deciles]

    # 5. Format payload strictly matching frontend requirements
    customers_payload = [
        {
            "customer_id": str(row["customer_id"]),
            "offer": "Discount",
            "ite": round(float(row["ite_score"]), 4)
        }
        for _, row in sorted_df.head(200).iterrows()
    ]

    allocation_payload = [
        {
            "customer_id": str(row["customer_id"]),
            "allocated_cost": cost_per_offer,
            "expected_uplift": round(float(row["ite_score"]), 4)
        }
        for _, row in targeted_df.head(200).iterrows()
    ]

    return {
        "customers": customers_payload,
        "qini": {
            "x": x_curve,
            "model": model_curve,
            "random": random_curve
        },
        "allocation": allocation_payload,
        "summary": {
            "budget": req.budget,
            "max_offer_cost": cost_per_offer,
            "targeted_count": len(targeted_df),
            "expected_incremental_conversions": round(float(targeted_df["ite_score"].sum()), 2)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api:app", host="127.0.0.1", port=8000, reload=True)