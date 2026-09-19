from evals.v2_contract_policy import train,predict_record,predict_runtime
def r(t,s,a,step=0):
 return {"task_id":t,"step":step,"state":{"split":s,"actions_tried":step},"candidates":[{"action":"files"},{"action":"stop"}],"chosen_action":a}
def test_same_contract_predicts_record_and_runtime():
 rows=[r("a","train","files",0),r("b","train","stop",2)];m=train(rows)
 rec=r("d","dev","files",0);before={"spent":{"actions":0,"cost":0,"risk":0},"unique_evidence":0,"mean_redundancy":0}
 assert predict_record(m,rec)==predict_runtime(m,before,["files","stop"],0)
