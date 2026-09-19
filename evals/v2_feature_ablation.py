from __future__ import annotations
import argparse,json,math
from collections import Counter,defaultdict
from pathlib import Path

ALL=("step","actions_tried","artifact_files","artifact_symbols","tokens_spent","cost_spent")
GROUPS={
 "full":ALL,
 "step_only":("step",),
 "no_step":tuple(x for x in ALL if x!="step"),
 "evidence_only":("actions_tried","artifact_files","artifact_symbols"),
 "budget_only":("tokens_spent","cost_spent"),
 "no_evidence":("step","tokens_spent","cost_spent"),
}
ORDER=("files","lexical","semantic","structural","stop")

def val(row,k):
 if k=="step": return float(row.get("step",0))
 return float(row.get("state",{}).get(k,0))

def train(rows,features):
 data=[r for r in rows if r.get("state",{}).get("split")=="train"]; sums=defaultdict(lambda:[0.0]*len(features)); counts=Counter()
 for r in data:
  a=r["chosen_action"];counts[a]+=1
  for i,k in enumerate(features):sums[a][i]+=val(r,k)
 cents={a:[x/counts[a] for x in xs] for a,xs in sums.items()};sc=[]
 for k in features:
  xs=[val(r,k) for r in data];m=sum(xs)/len(xs);sc.append(math.sqrt(sum((x-m)**2 for x in xs)/len(xs)) or 1.0)
 return cents,sc

def accuracy(rows,features):
 cents,sc=train(rows,features);dev=[r for r in rows if r.get("state",{}).get("split")=="dev"]
 def pred(r):
  cand=[c["action"] for c in r["candidates"] if c["action"] in cents]
  def d(a):return sum(((val(r,k)-cents[a][i])/sc[i])**2 for i,k in enumerate(features))
  return min(cand,key=lambda a:(d(a),ORDER.index(a)))
 return round(sum(pred(r)==r["chosen_action"] for r in dev)/len(dev),4)

def ablate(rows):
 scores={name:accuracy(rows,fs) for name,fs in GROUPS.items()};full=scores["full"]
 return {"protocol":"v2-feature-ablation-v1","dev_records":sum(r.get("state",{}).get("split")=="dev" for r in rows),"scores":scores,
 "delta_vs_full_pp":{k:round((v-full)*100,2) for k,v in scores.items()},
 "claim_boundary":"Descriptive supervised behavior-agreement ablation; correlated features and small source-problem count prevent causal feature attribution."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--dataset",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in a.dataset.read_text(encoding="utf-8").splitlines() if x.strip()];r=ablate(rows);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
