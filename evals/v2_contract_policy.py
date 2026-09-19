from __future__ import annotations
import argparse,json,math
from collections import Counter,defaultdict
from pathlib import Path
from evals.v2_feature_contract import FEATURE_NAMES,from_decision_record,from_policy_state
ORDER=("files","lexical","semantic","structural","stop")

def train(rows):
 data=[r for r in rows if r.get("state",{}).get("split")=="train"]; sums=defaultdict(lambda:[0.0]*len(FEATURE_NAMES));counts=Counter()
 for r in data:
  a=r["chosen_action"];v=from_decision_record(r).vector();counts[a]+=1
  for i,x in enumerate(v):sums[a][i]+=x
 cents={a:[x/counts[a] for x in xs] for a,xs in sums.items()};allv=[from_decision_record(r).vector() for r in data];sc=[]
 for i in range(len(FEATURE_NAMES)):
  xs=[v[i] for v in allv];m=sum(xs)/len(xs);sc.append(math.sqrt(sum((x-m)**2 for x in xs)/len(xs)) or 1.0)
 return {"protocol":"v2-feature-contract-centroid-v1","features":list(FEATURE_NAMES),"centroids":cents,"scales":sc,"train_records":len(data)}

def predict_vector(model,v,candidates):
 viable=[a for a in candidates if a in model["centroids"]]
 if not viable:return "stop" if "stop" in candidates else candidates[0]
 def d(a):return sum(((v[i]-model["centroids"][a][i])/model["scales"][i])**2 for i in range(len(v)))
 return min(viable,key=lambda a:(d(a),ORDER.index(a)))

def predict_record(model,row):return predict_vector(model,from_decision_record(row).vector(),[c["action"] for c in row["candidates"]])
def predict_runtime(model,before,candidates,step):return predict_vector(model,from_policy_state(before,step).vector(),candidates)

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--dataset",type=Path,required=True);ap.add_argument("--model",type=Path,required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in a.dataset.read_text(encoding="utf-8").splitlines() if x.strip()];m=train(rows);a.model.write_text(json.dumps(m,indent=2),encoding="utf-8")
 dev=[r for r in rows if r.get("state",{}).get("split")=="dev"];print(json.dumps({"train":m["train_records"],"dev":len(dev),"dev_agreement":round(sum(predict_record(m,r)==r["chosen_action"] for r in dev)/len(dev),4)}))
if __name__=="__main__":main()
