from evals.v2_per_problem_ablation import leave_one_problem_out
def r(t,s,a):
 return {"task_id":t,"step":0,"state":{"split":s},"candidates":[{"action":"files"},{"action":"stop"}],"chosen_action":a}
def test_reports_unique_dev_problem():
 x=leave_one_problem_out([r("research__a","train","files"),r("v2obs__b","dev","files"),r("v2div0__b","dev","files")]);assert x["dev_source_problems"]==1
