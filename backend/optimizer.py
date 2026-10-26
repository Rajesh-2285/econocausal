import os
import pandas as pd
import numpy as np

# 1. Load the customer data with the uplift scores calculated earlier
print("Step 1: Loading scored customer data...")
data_path = "data/customer_ite_scores.csv"

if not os.path.exists(data_path):
    raise FileNotFoundError("Run backend/double_ml.py first to create the scores file.")

df = pd.read_csv(data_path)

# 2. Segment customers into simple business buckets based on their uplift score
print("Step 2: Segmenting customers into groups...")
# Threshold: median uplift score
threshold = df["ite_score"].median()

def assign_segment(row):
    # If the offer helps them significantly, they are a "Persuadable"
    if row["ite_score"] >= threshold:
        return "Persuadable"
    # If they already spend a lot and the offer barely changes anything, they are a "Sure Thing"
    elif row["history"] > df["history"].median():
        return "Sure Thing"
    # Otherwise, it's low response and low spend
    else:
        return "Lost Cause"

df["segment"] = df.apply(assign_segment, axis=1)
print("Customer breakdown by segment:")
print(df["segment"].value_counts())

# 3. Budget Optimization: Pick the best customers under a fixed budget
print("\nStep 3: Running budget optimization...")
# Campaign assumptions
BUDGET = 5000.0        # Total marketing budget in dollars
COST_PER_OFFER = 1.0   # Sending a discount costs $1.00
REVENUE_PER_BUY = 25.0 # Average profit when a customer converts

max_offers = int(BUDGET / COST_PER_OFFER)

# Strategy: Sort customers by their uplift (ITE score) in descending order
# Give offers to the highest-uplift customers until the budget runs out
sorted_df = df.sort_values(by="ite_score", ascending=False).reset_index(drop=True)

# Select the top customers within budget
targeted_customers = sorted_df.iloc[:max_offers].copy()
targeted_customers["targeted"] = 1

# 4. Calculate Business Results (ROI)
expected_extra_buys = targeted_customers["ite_score"].sum()
expected_extra_revenue = expected_extra_buys * REVENUE_PER_BUY
net_profit = expected_extra_revenue - BUDGET
roi_percent = (net_profit / BUDGET) * 100

print("\n" + "=" * 45)
print("CAMPAIGN OPTIMIZATION RESULTS")
print("=" * 45)
print(f"Total Budget Spent       : ${BUDGET:,.2f}")
print(f"Customers Targeted       : {len(targeted_customers):,}")
print(f"Expected Extra Purchases : {expected_extra_buys:.1f}")
print(f"Expected Added Revenue   : ${expected_extra_revenue:,.2f}")
print(f"Net Profit               : ${net_profit:,.2f}")
print(f"Projected ROI            : {roi_percent:.1f}%")
print("=" * 45)

# 5. Save the targeted list locally
targeted_customers.to_csv("data/targeted_customers.csv", index=False)
print("\nSaved targeted roster to data/targeted_customers.csv")