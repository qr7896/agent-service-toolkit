from __future__ import annotations
import argparse, json, math
from collections import Counter, defaultdict
from pathlib import Path

ACTIONS=("files","lexical","semantic","structural","stop")

def features(row):
    s=row.get("state",{}); return {
      "step":int(row.get("step",0)),"actions_tried":int(s.get("actions_tried",0)),
      "artifact_files":int(s.get("artifact_files",0)),"artifact_symbols":int(s.get("artifact_symbols",0)),
      "tokens_spent":int(s.get("tokens_spent",0)),"cost_spent":float(s.get("cost_spent",0)),
    }

def train_frequency_policy(rows):
    train=[r for r in rows if r.get("state",{}).get("split")=="train"]
    if not train: raise ValueError("no train records")
    by_step=defaultdict(Counter); overall=Counter()
    for r in train: by_step[int(r["step"])][r["chosen_action"]]+=1; overall[r["chosen_action"]]+=1
    model={"protocol":"v2-supervised-frequency-v1","train_records":len(train),"train_tasks":len({r["task_id"] for r in train}),
           "overall":dict(overall),"by_step":{str(k):dict(v) for k,v in sorted(by_step.items())}}
    return model

def predict(model,row):
    candidates=[c["action"] for c in row["candidates"]]
    counts=model["by_step"].get(str(row["step"]),model["overall"])
    return max(candidates,key=lambda a:(counts.get(a,0),-ACTIONS.index(a)))

def evaluate(model,rows,split):
    data=[r for r in rows if r.get("state",{}).get("split")==split]
    correct=sum(predict(model,r)==r["chosen_action"] for r in data)
    baseline=sum(max((c["action"] for c in r["candidates"]),key=lambda a:-ACTIONS.index(a))==r["chosen_action"] for r in data)
    return {"split":split,"records":len(data),"tasks":len({r["task_id"] for r in data}),"accuracy":round(correct/len(data),4) if data else None,
            "fixed_order_baseline_accuracy":round(baseline/len(data),4) if data else None}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dataset",type=Path,required=True); ap.add_argument("--model",type=Path,required=True); ap.add_argument("--report",type=Path,required=True); args=ap.parse_args()
    rows=[json.loads(x) for x in args.dataset.read_text(encoding="utf-8").splitlines() if x.strip()]
    model=train_frequency_policy(rows); report={"protocol":"v2-supervised-replay-v1","model":model,"dev":evaluate(model,rows,"dev"),"claim_boundary":"Behavior-cloning agreement only; not IPS, causal policy value, or autonomous repair performance."}
    args.model.write_text(json.dumps(model,indent=2),encoding="utf-8"); args.report.write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report))
if __name__=="__main__": main()
