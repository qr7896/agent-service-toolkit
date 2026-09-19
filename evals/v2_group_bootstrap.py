from __future__ import annotations
import argparse,json,random
from pathlib import Path
from evals.v2_grouped_robustness import source_problem_id
from evals.v2_supervised_policy import train_frequency_policy,predict as fp
from evals.v2_contextual_policy import train_centroid_policy,predict as cp

def resample(rows,seeds=(11,23,37,51,71)):
 train=[r for r in rows if r.get("state",{}).get("split")=="train"]; dev=[r for r in rows if r.get("state",{}).get("split")=="dev"]
 groups=sorted({source_problem_id(r["task_id"]) for r in train}); out=[]
 for seed in seeds:
  rng=random.Random(seed); sampled=[rng.choice(groups) for _ in groups]
  boot=[r for g in sampled for r in train if source_problem_id(r["task_id"])==g]
  f=train_frequency_policy(boot);c=train_centroid_policy(boot);n=len(dev)
  fa=sum(fp(f,r)==r["chosen_action"] for r in dev)/n;ca=sum(cp(c,r)==r["chosen_action"] for r in dev)/n
  out.append({"seed":seed,"frequency":round(fa,4),"contextual":round(ca,4),"delta_pp":round((ca-fa)*100,2)})
 return {"protocol":"v2-group-bootstrap-v1","seeds":out,"consistent_contextual_direction":all(x["delta_pp"]>0 for x in out),"claim_boundary":"Group-bootstrap stability of behavior-cloning agreement only."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--dataset",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in a.dataset.read_text(encoding="utf-8").splitlines() if x.strip()];r=resample(rows);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
