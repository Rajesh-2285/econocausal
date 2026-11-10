# ⚡ EconoCausal: Dynamic Pricing via Double Machine Learning

An end-to-end Causal AI and Prescriptive Optimization system designed to differentiate between organic baseline behavior and true incremental treatment effects ($P(\text{Conversion})$ vs $\text{ITE}$). The platform allocates limited promotional budgets to maximize ROI by targeting strictly "Persuadable" customer segments.

---

## Architecture Overview

```
                                      [ Retail Customer Records (64,000) ]
                                                        │
                                                        ▼
                                       [ Microsoft DoWhy Causal DAG ]
                                  (Identified & Refuted Common Confounders)
                                                        │
                                                        ▼
                                       [ EconML Double Machine Learning ]
                                 (First-Stage Residualization via LassoCV)
                                                        │
                                                        ▼
                                     [ Individual Treatment Effects (ITE) ]
                                                        │
                                                        ▼
                                  [ Prescriptive SciPy HiGHS Linear Solver ]
                                     Maximize Lift Subject to Budget <= B
                                                        │
                                ┌───────────────────────┴───────────────────────┐
                                ▼                                               ▼
                    [ FastAPI REST Endpoints ]                    [ Interactive Dashboards ]
                     - GET /health                                 - FastAPI / Jinja2 UI (Port 8000)
                     - POST /api/optimize                          - Streamlit Analytics (Port 8501)
                     - backend/drift_detector.py
```

---

## Module Breakdown

1. **Causal Graphing & Identification (`backend/causal_engine.py`)**
   - Microsoft DoWhy DAG modeling treatments (`offer`), confounders (`recency`, `history`), and outcome (`conversion`).
   - Statistical refutation tests (Placebo Treatment and Random Common Cause).

2. **Double Machine Learning Engine (`backend/double_ml.py`, `models/dml_hyperparams.py`)**
   - Estimates individual treatment effects using out-of-fold orthogonalization.
   - Evaluates candidate residualizers (`LassoCV`, `ElasticNetCV`, `GradientBoosting`, `RandomForest`).

3. **Prescriptive Budget Optimizer (`analytics/segmentation_optimizer.py`, `backend/optimizer.py`)**
   - Solves constrained linear programs via SciPy HiGHS simplex method.
   - Groups users into 4 quadrants: Persuadables, Sure Things, Lost Causes, and Sleeping Dogs.

4. **Automated Drift Monitor (`backend/drift_detector.py`)**
   - Continuous feature distribution checks via Kolmogorov-Smirnov (KS) two-sample tests and Population Stability Index (PSI).

5. **API & Visualization Suite (`backend/api.py`, `dashboard/app.py`)**
   - FastAPI microservice with automated Swagger documentation (`/docs`).
   - Live interactive charts for budget adjustments, decile lift distributions, and customer prescription tables.

---

## Quickstart Guide (Windows PowerShell)

### 1. Local Environment Setup

```powershell
# Activate Python virtual environment
.\venv\Scripts\Activate.ps1

# Install project dependencies
pip install -r backend/requirements.txt
pip install jinja2 uvicorn streamlit plotly pytest httpx
```

### 2. Run Automated Integration Tests

```powershell
python -m pytest tests/test_pipeline.py -v
```

### 3. Launch Services

#### FastAPI Service & Embedded Dashboard
```powershell
python -m uvicorn backend.api:app --reload --port 8000
```
- **Web Dashboard:** `http://127.0.0.1:8000/`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`
- **Health Diagnostics:** `http://127.0.0.1:8000/health`

#### Streamlit Analytical UI
```powershell
streamlit run dashboard/app.py --server.port 8501
```
- **Interactive UI:** `http://localhost:8501/`

---

## API Contract Specification

### Request (`POST /api/optimize`)
```json
{
  "budget": 10000.0,
  "cost_per_contact": 1.50,
  "channel_filter": "All"
}
```

### Response (`200 OK`)
```json
{
  "status": "SUCCESS",
  "total_customers_evaluated": 64000,
  "targeted_customers_count": 6666,
  "budget_allocated": 9999.0,
  "total_expected_incremental_conversions": 528.7,
  "efficiency_gain_vs_random": 1.30,
  "decile_uplift_distribution": [0.124, 0.098, 0.081, 0.067, 0.052, 0.040, 0.031, 0.018, 0.004, -0.006]
}
```