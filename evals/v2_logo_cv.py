from __future__ import annotations
import argparse,json
from collections import defaultdict
from pathlib import Path
from evals.v2_grouped_robustness import source_problem_id
from evals.v2_supervised_policy import train_frequency_policy,predict as fp
from evals.v2_contextual_policy import train_centroid_policy,predict as cp

def leave_one_group_out(rows):
 base=[r for r in rows if r.get("state",{}).get("split") in {"train","dev"}]
 groups=sorted({source_problem_id(r["task_id"]) for r in base})
 results=[]
 for g in groups:
  train=[]
  hold=[]
  for r in base:
   rr={**r,"state":dict(r.get("state",{}))}
   if source_problem_id(r["task_id"])==g:
    rr["state"]["split"]="dev";hold.append(rr)
   else:
    rr["state"]["split"]="train";train.append(rr)
  merged=train+hold
  f=train_frequency_policy(merged);c=train_centroid_policy(merged);n=len(hold)
  fa=sum(fp(f,r)==r["chosen_action"] for r in hold)/n;ca=sum(cp(c,r)==r["chosen_action"] for r in hold)/n
  results.append({"source_problem":g,"records":n,"frequency":round(fa,4),"contextual":round(ca,4),"delta_pp":round((ca-fa)*100,2)})
 weighted_n=sum(x["records"] for x in results)
 return {"protocol":"v2-logo-cv-v1","source_problems":len(groups),"folds":results,
 "weighted_frequency":round(sum(x["frequency"]*x["records"] for x in results)/weighted_n,4),
 "weighted_contextual":round(sum(x["contextual"]*x["records"] for x in results)/weighted_n,4),
 "positive_folds":sum(x["delta_pp"]>0 for x in results),"tied_folds":sum(x["delta_pp"]==0 for x in results),"negative_folds":sum(x["delta_pp"]<0 for x in results),
 "claim_boundary":"Leave-one-source-problem-out behavior-cloning cross-validation over existing train+dev only; no sealed TEST, IPS, or repair-rate claim."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--dataset",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in a.dataset.read_text(encoding="utf-8").splitlines() if x.strip()];r=leave_one_group_out(rows);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
