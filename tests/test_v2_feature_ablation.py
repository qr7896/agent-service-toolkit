from evals.v2_feature_ablation import ablate,GROUPS
def r(t,s,a,step=0,af=0):
 return {"task_id":t,"step":step,"state":{"split":s,"artifact_files":af},"candidates":[{"action":"files"},{"action":"stop"}],"chosen_action":a}
def test_ablation_has_expected_groups():
 rows=[r("a","train","files",0,0),r("b","train","stop",1,2),r("d","dev","files",0,0),r("e","dev","stop",1,2)]
 x=ablate(rows);assert set(x["scores"])==set(GROUPS) and x["scores"]["full"]==1.0
