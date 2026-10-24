import pandas as pd
from dowhy import CausalModel

def run_causal_pipeline():
    print("[1/5] Loading real benchmark dataset...")
    df = pd.read_csv("data/retail_data.csv")

    # Binarize treatment: 1 if discount/offer sent, 0 if 'No Offer'
    df["treatment"] = (df["offer"] != "No Offer").astype(int)

    print(f"Total customers: {len(df)}")
    print(f"Treated (Offers Sent): {df['treatment'].sum()}")
    print(f"Control (No Offer): {(df['treatment'] == 0).sum()}")

    # Define the Causal Directed Acyclic Graph (DAG)
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

    print("\n[2/5] Initializing DoWhy Causal Graphical Model...")
    model = CausalModel(
        data=df,
        treatment="treatment",
        outcome="conversion",
        graph=causal_graph.replace("\n", " ")
    )

    print("\n[3/5] Identifying Causal Effect via Backdoor Criterion...")
    identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)

    print("\n[4/5] Estimating Average Treatment Effect (ATE)...")
    estimate = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.propensity_score_matching"
    )
    print(f"Estimated Baseline ATE: {estimate.value:.4f} (+{estimate.value * 100:.2f}% uplift)")

    print("\n[5/5] Running Robustness Refutation Tests...")

    # Refutation 1: Placebo Treatment Refuter
    # Replaces true treatment with random noise. New ATE should drop to ~0.
    print("\n--- Test 1: Placebo Treatment Refutation ---")
    refute_placebo = model.refute_estimate(
        identified_estimand,
        estimate,
        method_name="placebo_treatment_refuter",
        placebo_type="permute"
    )
    print(refute_placebo)

    # Refutation 2: Add Random Common Cause Refuter
    # Injects an unobserved random variable as a confounder. Baseline ATE should remain stable.
    print("\n--- Test 2: Random Common Cause Refutation ---")
    refute_random = model.refute_estimate(
        identified_estimand,
        estimate,
        method_name="random_common_cause"
    )
    print(refute_random)

    return model, estimate

if __name__ == "__main__":
    run_causal_pipeline()