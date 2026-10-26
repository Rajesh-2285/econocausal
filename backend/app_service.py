import os
import pandas as pd
from dowhy import CausalModel

class CausalAppService:
    def __init__(self, data_path="data/retail_data.csv"):
        self.data_path = data_path
        self.df = None
        self.model = None
        self.identified_estimand = None
        self.estimate = None

    def load_data(self):
        """Loads dataset and prepares binary treatment."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Missing {self.data_path}")
        self.df = pd.read_csv(self.data_path)
        self.df["treatment"] = (self.df["offer"] != "No Offer").astype(int)
        return len(self.df)

    def initialize_causal_dag(self):
        """Builds Pearl's Causal Graphical Model."""
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
        self.model = CausalModel(
            data=self.df,
            treatment="treatment",
            outcome="conversion",
            graph=causal_graph.replace("\n", " ")
        )
        self.identified_estimand = self.model.identify_effect(proceed_when_unidentifiable=True)
        return self.identified_estimand.get_backdoor_variables()

    def get_ate_summary(self):
        """Computes baseline Average Treatment Effect."""
        self.estimate = self.model.estimate_effect(
            self.identified_estimand,
            method_name="backdoor.propensity_score_matching"
        )
        return {
            "baseline_ate": round(self.estimate.value, 4),
            "uplift_percentage": round(self.estimate.value * 100, 2)
        }

    def run_refutation_audit(self):
        """Runs Placebo and Noise injection sensitivity tests."""
        refute_placebo = self.model.refute_estimate(
            self.identified_estimand,
            self.estimate,
            method_name="placebo_treatment_refuter",
            placebo_type="permute"
        )
        refute_random = self.model.refute_estimate(
            self.identified_estimand,
            self.estimate,
            method_name="random_common_cause"
        )
        return {
            "placebo_effect": round(refute_placebo.new_effect, 6),
            "placebo_p_value": refute_placebo.refutation_result["p_value"],
            "noise_effect": round(refute_random.new_effect, 6),
            "noise_p_value": refute_random.refutation_result["p_value"]
        }

if __name__ == "__main__":
    print("Testing CausalAppService...")
    service = CausalAppService()
    rows = service.load_data()
    print(f"Loaded {rows:,} customer rows.")
    confounders = service.initialize_causal_dag()
    print(f"Adjustment Confounders: {confounders}")
    ate = service.get_ate_summary()
    print(f"ATE: +{ate['uplift_percentage']}%")
    audit = service.run_refutation_audit()
    print(f"Audit Results: {audit}")
    print("Service layer verification complete.")