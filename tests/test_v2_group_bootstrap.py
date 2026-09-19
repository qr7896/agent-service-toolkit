from evals.v2_group_bootstrap import resample
def r(t,s,a):
 return {"task_id":t,"step":0,"state":{"split":s},"candidates":[{"action":"files"},{"action":"stop"}],"chosen_action":a}
def test_bootstrap_is_deterministic():
 rows=[r("research__a","train","files"),r("research__b","train","stop"),r("research__d","dev","files")]
 assert resample(rows,(1,2))==resample(rows,(1,2))
