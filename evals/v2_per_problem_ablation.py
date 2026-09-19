from __future__ import annotations
import argparse,json
from pathlib import Path
from evals.v2_feature_ablation import GROUPS,accuracy
from evals.v2_grouped_robustness import source_problem_id

def leave_one_problem_out(rows):
 dev_groups=sorted({source_problem_id(r["task_id"]) for r in rows if r.get("state",{}).get("split")=="dev"})
 # Training remains frozen train-only; report per held-out dev problem agreement by filtering each group.
 results=[]
 for g in dev_groups:
  subset=[r for r in rows if r.get("state",{}).get("split")=="train" or source_problem_id(r["task_id"])==g]
  scores={k:accuracy(subset,v) for k,v in GROUPS.items()}
  results.append({"source_problem":g,"scores":scores})
 return {"protocol":"v2-per-source-problem-ablation-v1","dev_source_problems":len(dev_groups),"rows":results,
 "claim_boundary":"Per-source-problem descriptive behavior agreement; train set is unchanged and no causal attribution is implied."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--dataset",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in a.dataset.read_text(encoding="utf-8").splitlines() if x.strip()];r=leave_one_problem_out(rows);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
