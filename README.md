# EconoCausal: Dynamic Pricing via Double Machine Learning 
# EconoCausal

An end-to-end causal inference and uplift modeling platform combining DoWhy, EconML Double Machine Learning, SciPy budget optimization, and a React + Vite interactive dashboard.

---

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
