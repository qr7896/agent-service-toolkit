from evals.v2_matched_retrieval import replay
def test_empty(): assert replay([])["action_budget_per_arm"]==2
