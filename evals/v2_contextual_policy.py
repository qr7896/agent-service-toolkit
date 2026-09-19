from __future__ import annotations
import argparse, json, math
from collections import Counter, defaultdict
from pathlib import Path

ACTIONS=("files","lexical","semantic","structural","stop")
NUMERIC=("step","actions_tried","artifact_files","artifact_symbols","tokens_spent","cost_spent")

def vector(row):
 s=row.get("state",{})
 return [float(row.get("step",0)),float(s.get("actions_tried",0)),float(s.get("artifact_files",0)),float(s.get("artifact_symbols",0)),float(s.get("tokens_spent",0)),float(s.get("cost_spent",0))]

def train_centroid_policy(rows):
 train=[r for r in rows if r.get("state",{}).get("split")=="train"]
 if not train: raise ValueError("no train records")
 sums=defaultdict(lambda:[0.0]*len(NUMERIC)); counts=Counter()
 for r in train:
  a=r["chosen_action"]; counts[a]+=1
  for i,x in enumerate(vector(r)): sums[a][i]+=x
 centroids={a:[v/counts[a] for v in sums[a]] for a in counts}
 scales=[]
 allv=[vector(r) for r in train]
 for i in range(len(NUMERIC)):
  vals=[v[i] for v in allv]; mean=sum(vals)/len(vals); var=sum((x-mean)**2 for x in vals)/len(vals); scales.append(math.sqrt(var) or 1.0)
 return {"protocol":"v2-contextual-centroid-v1","features":list(NUMERIC),"train_records":len(train),"counts":dict(counts),"centroids":centroids,"scales":scales}

def predict(model,row):
 x=vector(row); candidates=[c["action"] for c in row["candidates"]]
 viable=[a for a in candidates if a in model["centroids"]]
 if not viable: return candidates[0]
 def dist(a): return sum(((x[i]-model["centroids"][a][i])/model["scales"][i])**2 for i in range(len(x)))
 return min(viable,key=lambda a:(dist(a),ACTIONS.index(a)))

def evaluate(model,rows,split):
 data=[r for r in rows if r.get("state",{}).get("split")==split]
 correct=sum(predict(model,r)==r["chosen_action"] for r in data)
 return {"split":split,"records":len(data),"tasks":len({r["task_id"] for r in data}),"accuracy":round(correct/len(data),4) if data else None}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--dataset",type=Path,required=True); ap.add_argument("--model",type=Path,required=True); ap.add_argument("--report",type=Path,required=True); args=ap.parse_args()
 rows=[json.loads(x) for x in args.dataset.read_text(encoding="utf-8").splitlines() if x.strip()]
 m=train_centroid_policy(rows); rep={"protocol":"v2-contextual-replay-v1","model":m,"dev":evaluate(m,rows,"dev"),"claim_boundary":"Supervised state-conditioned behavior agreement only; no IPS or causal policy value claim."}
 args.model.write_text(json.dumps(m,indent=2),encoding="utf-8"); args.report.write_text(json.dumps(rep,indent=2),encoding="utf-8"); print(json.dumps(rep))
if __name__=="__main__": main()
