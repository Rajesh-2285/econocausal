# EconoCausal Frontend

React + Vite dashboard for the frontend tasks assigned to the EconoCausal team:
- CSV dataset upload and preview
- Campaign budget and per-offer cost inputs
- Qini/uplift curve plotted against a random-rollout baseline
- Searchable/filterable customer ITE table
- Budget allocation results view
- Backend health check

## Run on Windows (PowerShell)

1. Install Node.js LTS if `node -v` does not work.
2. Extract this folder, open PowerShell in this folder, then run:

```powershell
npm install
npm run dev
```

3. Open the local URL Vite prints (usually `http://localhost:5173`).

## Dataset handling

The CSV is parsed in the browser with Papa Parse. The dashboard previews the uploaded rows and checks for the expected retail dataset fields:

`recency, history, used_discount, used_bogo, zip_code, is_referral, channel, offer, conversion`

The frontend does not invent individual treatment effects, Qini points, ROI, savings, or optimized allocations. The retail CSV's observed `conversion` is an outcome, **not** an ITE score.

## Backend integration contract

The frontend currently uses `VITE_API_BASE_URL`, defaulting to `http://localhost:8000`.

- `GET /health` should return HTTP 2xx.
- `POST /api/optimize` receives JSON:

```json
{
  "budget": 10000,
  "max_offer_cost": 20,
  "target_group": "all",
  "rows": [],
  "columns": []
}
```

Implement this endpoint in the team backend and return whichever real outputs are available, for example:

```json
{
  "customers": [
    {
      "customer_id": "C001",
      "offer": "Discount",
      "ite": 0.12
    }
  ],
  "qini": {
    "x": [0.1, 0.2, 0.3],
    "model": [0.04, 0.09, 0.15],
    "random": [0.02, 0.04, 0.06]
  },
  "allocation": [
    {
      "customer_id": "C001",
      "offer": "Discount",
      "ite": 0.12,
      "estimated_cost": 10
    }
  ],
  "summary": {
    "customers_selected": 1,
    "budget_used": 10,
    "estimated_incremental_conversions": 0.12
  }
}
```

The example values above describe the **response shape only**. Do not use them as project results. The model team should provide real values and confirm units. The `qini` object can alternatively be named `uplift_curve`; the frontend expects `x`, `model`, and `random` arrays. If your backend already uses different routes/field names, update the fetch calls in `src/App.jsx` to match the actual API.

## What works before backend connection

- Dashboard layout and navigation
- CSV upload, row/column counts, and preview
- Descriptive conversion count/rate when the `conversion` column exists
- Budget form validation and API request
- Customer search/filter/sort when real ITE data is available
- Clear waiting states until the model/backend provides causal results

## Important project boundary

The dashboard cannot calculate trustworthy ITEs or a valid Qini curve from the raw columns alone. Those require the trained causal model and an evaluation procedure. This frontend is ready to consume those outputs; coordinate with the backend/model teammates for the actual endpoint and schema.
