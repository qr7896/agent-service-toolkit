from evals.v2_evidence_sufficiency import classify
def test_labels_redundancy():
 x=classify({"case_details":[{"new_unique_evidence":0,"redundancy_delta":.5}]});assert x["counts"]["redundant_continue"]==1
