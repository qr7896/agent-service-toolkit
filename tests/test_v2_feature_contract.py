from evals.v2_feature_contract import from_policy_state,from_decision_record,FEATURE_NAMES
def test_runtime_contract():
 x=from_policy_state({"spent":{"actions":2,"cost":1.5,"risk":.2},"unique_evidence":3,"mean_redundancy":.1},4)
 assert x.vector()==[4.0,2.0,3.0,1.5,.2,.1]
def test_record_policy_state_has_priority():
 r={"step":1,"state":{"artifact_files":99,"policy_state":{"spent":{"actions":1,"cost":2,"risk":.3},"unique_evidence":4,"mean_redundancy":.2}}}
 assert from_decision_record(r).evidence_items==4
