import pandas as pd
from dowhy import CausalModel

def run_causal_pipeline():
    print("[1/4] Loading real benchmark dataset...")
    df = pd.read_csv("data/retail_data.csv")

    # Binarize treatment: 1 if discount/offer sent, 0 if 'No Offer'
    df["treatment"] = (df["offer"] != "No Offer").astype(int)

    print(f"Total customers: {len(df)}")
    print(f"Treated (Offers Sent): {df['treatment'].sum()}")
    print(f"Control (No Offer): {(df['treatment'] == 0).sum()}")

    # Define the Causal Directed Acyclic Graph (DAG)
    # Encodes domain causal assumptions:
    # Prior history, recency, and past behavior confound both who receives targeting
    # and the probability of conversion.
    causal_graph = """
    digraph {
        history -> treatment;
        history -> conversion;
        recency -> treatment;
        recency -> conversion;
        used_discount -> treatment;
        used_discount -> conversion;
        is_referral -> treatment;
        is_referral -> conversion;
        treatment -> conversion;
    }
    """

    print("\n[2/4] Initializing DoWhy Causal Graphical Model...")
    model = CausalModel(
        data=df,
        treatment="treatment",
        outcome="conversion",
        graph=causal_graph.replace("\n", " ")
    )

    print("\n[3/4] Identifying Causal Effect via Backdoor Criterion...")
    identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
    print(identified_estimand)

    print("\n[4/4] Estimating Average Treatment Effect (ATE) via Propensity Score Matching...")
    estimate = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.propensity_score_matching"
    )
    print(f"\nEstimated Causal ATE: {estimate.value:.4f}")
    print(f"Meaning: Sending an offer increases conversion probability by {estimate.value * 100:.2f}%")

    return model, estimate

if __name__ == "__main__":
    run_causal_pipeline()