from evals.v2_grouped_robustness import source_problem_id,audit,grouped_compare
def r(t,split,a="files"):
 return {"task_id":t,"step":0,"state":{"split":split},"candidates":[{"action":"files"},{"action":"stop"}],"chosen_action":a}
def test_aliases_collapse():
 assert source_problem_id("v2div2__abc")=="abc" and source_problem_id("research__abc")=="abc"
 assert source_problem_id("v2obs__research__abc")=="abc"
def test_cross_split_alias_is_rejected():
 x=grouped_compare([r("research__abc","train"),r("v2obs__abc","dev")]);assert not x["evaluation_valid"] and "abc" in x["cross_split_source_problems"]
def test_clean_groups_are_valid():
 x=grouped_compare([r("research__a","train"),r("v2obs__b","dev")]);assert x["evaluation_valid"] and x["source_problems"]==2
