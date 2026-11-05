"""
EconoCausal - Data Science Interactive Uplift & Budget Optimization Dashboard
Built with Streamlit, SciPy, and EconML Uplift Outputs.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

# Page configuration
st.set_page_config(
    page_title="EconoCausal Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Custom styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #0e1117;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #1f2937;
    }
    </style>
""", unsafe_allow_html=True)

# Data loader
@st.cache_data
def load_data():
    candidate_paths = [
        os.path.join("backend", "retail_data.csv"),
        os.path.join("data", "customer_ite_scores.csv"),
        "retail_data.csv"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            # Standardize column names
            df.columns = [c.lower() for c in df.columns]
            if "ite_score" not in df.columns:
                if "ite" in df.columns:
                    df["ite_score"] = df["ite"]
                else:
                    np.random.seed(42)
                    df["ite_score"] = np.random.normal(loc=0.0639, scale=0.03, size=len(df))
            return df

    # Synthetic fallback if path not resolved
    np.random.seed(42)
    n = 10000
    return pd.DataFrame({
        "recency": np.random.randint(1, 12, size=n),
        "history": np.random.exponential(scale=200, size=n) + 20,
        "channel": np.random.choice(["Web", "Phone", "Multichannel"], size=n),
        "ite_score": np.random.normal(loc=0.0639, scale=0.03, size=n)
    })

df = load_data()

st.title("⚡ EconoCausal: Causal Uplift & Allocation Engine")
st.markdown("Interactive Decision Optimization powered by **Double Machine Learning** and **SciPy Linear Programming**.")

# Sidebar controls
st.sidebar.header("Campaign Optimization Parameters")
budget = st.sidebar.number_input("Campaign Budget ($)", min_value=1000.0, max_value=100000.0, value=10000.0, step=1000.0)
cost_per_contact = st.sidebar.number_input("Outreach Cost per Customer ($)", min_value=0.10, max_value=20.0, value=1.50, step=0.10)

channel_options = ["All"]
if "channel" in df.columns:
    channel_options += sorted(df["channel"].dropna().unique().tolist())
selected_channel = st.sidebar.selectbox("Filter by Channel", channel_options)

# Filter dataset
filtered_df = df.copy()
if selected_channel != "All" and "channel" in df.columns:
    filtered_df = filtered_df[filtered_df["channel"] == selected_channel].reset_index(drop=True)

total_population = len(filtered_df)

# Run SciPy Optimization
max_contacts = int(budget / max(cost_per_contact, 0.01))
max_contacts = min(max_contacts, total_population)

c = -filtered_df["ite_score"].values
A = np.ones((1, total_population))
b = np.array([max_contacts])
bounds = [(0, 1) for _ in range(total_population)]

solver_result = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")

if solver_result.success:
    selected_mask = solver_result.x > 0.5
else:
    selected_mask = np.zeros(total_population, dtype=bool)
    top_k = np.argsort(c)[:max_contacts]
    selected_mask[top_k] = True

targeted_count = int(np.sum(selected_mask))
total_expected_conversions = float(np.sum(filtered_df.loc[selected_mask, "ite_score"]))
total_spend = targeted_count * cost_per_contact

# Random baseline benchmark
np.random.seed(42)
random_uplift = filtered_df["ite_score"].sample(n=max(1, targeted_count), random_state=42).sum()
efficiency = round(total_expected_conversions / max(float(random_uplift), 1e-5), 2)

# Top KPI Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Population", f"{total_population:,}")
col2.metric("Targeted Customers", f"{targeted_count:,}")
col3.metric("Incremental Conversions", f"+{total_expected_conversions:.1f}")
col4.metric("Optimizer Efficiency", f"{efficiency}x vs Random")

st.markdown("---")

# Layout: Chart + Data Sample
chart_col, data_col = st.columns([3, 2])

with chart_col:
    st.subheader("Uplift Decile Distribution")
    filtered_df["decile"] = pd.qcut(filtered_df["ite_score"], q=10, labels=False, duplicates="drop")
    decile_means = (
        filtered_df.groupby("decile", observed=False)["ite_score"]
        .mean()
        .sort_index(ascending=False) * 100
    )
    decile_df = pd.DataFrame({
        "Decile": [f"D{10 - i}" for i in range(len(decile_means))],
        "Mean Incremental Lift (%)": decile_means.values
    })
    st.bar_chart(decile_df.set_index("Decile"), color="#6366f1")

with data_col:
    st.subheader("Targeted Customer Cohort")
    available_cols = [col for col in ["recency", "history", "channel", "ite_score"] if col in filtered_df.columns]
    st.dataframe(
        filtered_df[selected_mask][available_cols].head(15),
        use_container_width=True
    )