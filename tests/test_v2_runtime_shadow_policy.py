from evals.v2_runtime_shadow_policy import ContextualShadowPolicy,PairedShadowDecisionLogger
def model():
 return {"centroids":{"files":[0,0,0,0,0,0],"stop":[2,2,2,2,2,2]},"scales":[1]*6}
def before(actions=0):
 return {"spent":{"actions":actions,"cost":0,"risk":0},"remaining":{"actions":4-actions,"cost":4,"risk":1},"unique_evidence":0}
def test_shadow_does_not_replace_executed_action():
 out=[];l=PairedShadowDecisionLogger("x",ContextualShadowPolicy(model()),out)
 r=l.record(before=before(),candidates=["files"],chosen_action="files",utility={});assert r["executed_action"]=="files" and r["shadow_action"]=="files"
def test_budget_filters_unsafe_candidate():
 out=[];l=PairedShadowDecisionLogger("x",ContextualShadowPolicy(model()),out)
 r=l.record(before={"spent":{"actions":4,"cost":4,"risk":1},"remaining":{"actions":0,"cost":0,"risk":0},"unique_evidence":0},candidates=["files"],chosen_action="stop",utility={})
 assert r["safe_candidates"]==["stop"] and r["shadow_action"]=="stop"
