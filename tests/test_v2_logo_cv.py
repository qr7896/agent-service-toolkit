from evals.v2_logo_cv import leave_one_group_out
def r(t,a):
 return {"task_id":t,"step":0,"state":{"split":"train"},"candidates":[{"action":"files"},{"action":"stop"}],"chosen_action":a}
def test_logo_has_one_fold_per_source_problem():
 x=leave_one_group_out([r("research__a","files"),r("v2obs__a","files"),r("research__b","stop")]);assert x["source_problems"]==2 and len(x["folds"])==2
