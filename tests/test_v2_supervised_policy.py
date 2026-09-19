from evals.v2_supervised_policy import train_frequency_policy,predict,evaluate
def row(t,step,chosen,split="train",cands=("files","stop")):
 return {"task_id":t,"step":step,"state":{"split":split},"candidates":[{"action":a} for a in cands],"chosen_action":chosen}
def test_train_uses_train_only():
 rows=[row("a",0,"files"),row("b",0,"files"),row("d",0,"stop","dev")]
 m=train_frequency_policy(rows); assert m["train_records"]==2 and predict(m,rows[-1])=="files"
def test_evaluate_reports_behavior_clone_agreement():
 rows=[row("a",0,"files"),row("b",0,"files"),row("d",0,"files","dev")]
 m=train_frequency_policy(rows); e=evaluate(m,rows,"dev"); assert e["accuracy"]==1.0 and e["records"]==1
