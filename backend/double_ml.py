import os
import pandas as pd
from econml.dml import LinearDML
from sklearn.linear_model import LogisticRegression, LinearRegression

# 1. Load our customer data
print("Step 1: Loading customer data...")
df = pd.read_csv("data/retail_data.csv")

# 2. Pick the customer features we care about
# history: past spend, recency: months since last visit, used_discount: past coupon use, is_referral: referred friend
features = ["history", "recency", "used_discount", "is_referral"]
X = df[features]

# Treatment: 1 if customer got an offer, 0 if no offer
T = (df["offer"] != "No Offer").astype(int)

# Outcome: 1 if customer bought something, 0 if not
Y = df["conversion"]

print(f"Loaded {len(df)} customers. Calculating individual uplift scores...")

# 3. Simple Double ML Model
# It uses basic linear models under the hood so it runs fast and is easy to explain
simple_dml = LinearDML(
    model_y=LinearRegression(),        # Simple model for purchase behavior
    model_t=LogisticRegression(),      # Simple model for who gets offers
    discrete_treatment=True,
    random_state=42
)

# 4. Train the model
simple_dml.fit(Y, T, X=X, W=None)

# 5. Predict how much the offer helps EACH customer (ITE = Individual Treatment Effect)
df["ite_score"] = simple_dml.effect(X)

# 6. Save the results to a new CSV file
os.makedirs("data", exist_ok=True)
df.to_csv("data/customer_ite_scores.csv", index=False)

print("\nSuccess! Results saved to data/customer_ite_scores.csv")
print(f"Average uplift per customer: +{df['ite_score'].mean() * 100:.2f}%")
print(f"Top 5 sample scores:\n{df[['history', 'recency', 'ite_score']].head()}")