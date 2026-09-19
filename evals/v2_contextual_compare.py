from __future__ import annotations
import argparse,json
from pathlib import Path
from evals.v2_supervised_policy import train_frequency_policy,predict as freq_predict
from evals.v2_contextual_policy import train_centroid_policy,predict as ctx_predict

def compare(rows):
 f=train_frequency_policy(rows); c=train_centroid_policy(rows)
 dev=[r for r in rows if r.get("state",{}).get("split")=="dev"]
 both=f_only=c_only=neither=0
 for r in dev:
  y=r["chosen_action"]; fc=freq_predict(f,r)==y; cc=ctx_predict(c,r)==y
  if fc and cc: both+=1
  elif fc: f_only+=1
  elif cc: c_only+=1
  else: neither+=1
 n=len(dev)
 return {"protocol":"v2-paired-dev-comparison-v1","records":n,"both_correct":both,"frequency_only_correct":f_only,"contextual_only_correct":c_only,"neither_correct":neither,
 "frequency_accuracy":round((both+f_only)/n,4),"contextual_accuracy":round((both+c_only)/n,4),"accuracy_delta_pp":round(((c_only-f_only)/n)*100,2),
 "claim_boundary":"Paired behavior-cloning agreement on dev trajectories; not causal policy value."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--dataset",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in a.dataset.read_text(encoding="utf-8").splitlines() if x.strip()];r=compare(rows);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
