from evals.v2_contextual_compare import compare
def r(t,step,a,split="train",tried=0):
 return {"task_id":t,"step":step,"state":{"split":split,"actions_tried":tried},"candidates":[{"action":"files"},{"action":"stop"}],"chosen_action":a}
def test_paired_counts_sum():
 rows=[r("a",0,"files"),r("b",1,"stop",tried=2),r("d",0,"files","dev"),r("e",1,"stop","dev",2)]
 x=compare(rows); assert x["both_correct"]+x["frequency_only_correct"]+x["contextual_only_correct"]+x["neither_correct"]==2
