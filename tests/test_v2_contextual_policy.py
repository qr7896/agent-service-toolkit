from evals.v2_contextual_policy import train_centroid_policy,predict,evaluate
def r(t,step,a,split="train",tried=0):
 return {"task_id":t,"step":step,"state":{"split":split,"actions_tried":tried},"candidates":[{"action":"files"},{"action":"stop"}],"chosen_action":a}
def test_context_changes_prediction():
 rows=[r("a",0,"files",tried=0),r("b",1,"stop",tried=2)]
 m=train_centroid_policy(rows)
 assert predict(m,r("x",0,"files","dev",0))=="files"
 assert predict(m,r("y",1,"stop","dev",2))=="stop"
def test_dev_not_used_for_training():
 rows=[r("a",0,"files"),r("d",0,"stop","dev")]
 m=train_centroid_policy(rows); assert m["train_records"]==1 and predict(m,rows[-1])=="files"
