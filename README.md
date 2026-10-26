

Backend causal inference pipeline and API service developed on the `Rajesh` branch. This engine estimates heterogeneous treatment effects across customer segments using Double Machine Learning (DML), validates causal robustness via refutation tests, and optimizes marketing spend under constrained budget limits.

## Key Features

- **Causal Graph & Identification**: Baseline causal DAG formulated with DoWhy to isolate treatment assignment mechanisms and estimate Average Treatment Effect (ATE).
- **Refutation Validation**: Placebo treatment and random common cause refutation tests to verify estimate stability against unobserved bias.
- **Double Machine Learning Uplift**: EconML-based estimation yielding individual treatment effect (`ITE`) scores across customer profiles, exported to `data/customer_ite_scores.csv`.
- **Constrained Optimization**: SciPy-powered allocation engine prioritizing high-uplift persuadables within campaign budget and maximum cost constraints.
- **FastAPI Bridge**: High-performance REST service providing live `/health` status, dynamic decile Qini cumulative gain curves, and ranked customer target rosters.

## Quickstart (Windows PowerShell)

1. Activate your virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
Install dependencies:PowerShellpip install -r requirements.txt
Start the FastAPI backend server:PowerShellpython -m backend.api
Service Endpoints:Interactive API Docs: http://127.0.0.1:8000/docs (default redirect from http://127.0.0.1:8000/)Health Check: http://127.0.0.1:8000/healthOptimization Endpoint: POST http://127.0.0.1:8000/api/optimizeAPI Contract SpecificationRequest (POST /api/optimize)JSON{
  "budget": 10000,
  "max_offer_cost": 20,
  "target_group": "all",
  "rows": [],
  "columns": []
}
Response (200 OK)JSON{
  "customers": [
    {
      "customer_id": "C00001",
      "offer": "Discount",
      "ite": 0.1287
    }
  ],
  "qini": {
    "x": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    "model": [0.0, 0.045, 0.098, 0.152, 0.201, 0.245, 0.282, 0.311, 0.334, 0.348, 0.355],
    "random": [0.0, 0.035, 0.071, 0.106, 0.142, 0.177, 0.213, 0.248, 0.284, 0.319, 0.355]
  },
  "allocation": [
    {
      "customer_id": "C00001",
      "offer": "Discount",
      "ite": 0.1287,
      "estimated_cost": 20
    }
  ],
  "summary": {
    "customers_selected": 200,
    "budget_used": 4000,
    "estimated_incremental_conversions": 24.3
  }
}

---

### What to do after saving on GitHub

Once you commit this file directly on GitHub, sync your local PC by running:

```cmd
git pull origin Rajesh
