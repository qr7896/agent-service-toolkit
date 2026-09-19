from __future__ import annotations
import argparse,json,re
from collections import defaultdict
from pathlib import Path
from evals.v2_supervised_policy import train_frequency_policy,predict as fp
from evals.v2_contextual_policy import train_centroid_policy,predict as cp

PREFIX=re.compile(r"^(?:v2rt__|v2obs__|v2div\d+__|research__)")

def source_problem_id(task_id:str)->str:
 previous=None
 while task_id != previous:
  previous=task_id; task_id=PREFIX.sub("",task_id)
 return task_id

def audit(rows):
 groups=defaultdict(lambda:defaultdict(int))
 for r in rows: groups[source_problem_id(r["task_id"])][r.get("state",{}).get("split","unknown")]+=1
 leaks={g:dict(v) for g,v in groups.items() if len(v)>1}
 return {"trajectory_ids":len({r["task_id"] for r in rows}),"source_problems":len(groups),"cross_split_source_problems":leaks}

def grouped_compare(rows):
 a=audit(rows)
 if a["cross_split_source_problems"]:
  return {**a,"evaluation_valid":False,"reason":"source problem appears across splits"}
 f=train_frequency_policy(rows);c=train_centroid_policy(rows);dev=[r for r in rows if r.get("state",{}).get("split")=="dev"]
 both=fo=co=neither=0
 for r in dev:
  y=r["chosen_action"];x=fp(f,r)==y;z=cp(c,r)==y
  if x and z:both+=1
  elif x:fo+=1
  elif z:co+=1
  else:neither+=1
 n=len(dev)
 return {**a,"evaluation_valid":True,"dev_records":n,"dev_source_problems":len({source_problem_id(r["task_id"]) for r in dev}),
 "frequency_accuracy":round((both+fo)/n,4),"contextual_accuracy":round((both+co)/n,4),"delta_pp":round((co-fo)/n*100,2),
 "paired":{"both":both,"frequency_only":fo,"contextual_only":co,"neither":neither},
 "claim_boundary":"Grouped source-problem audit prevents trajectory aliases crossing splits; agreement remains supervised behavior cloning."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--dataset",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in a.dataset.read_text(encoding="utf-8").splitlines() if x.strip()];r=grouped_compare(rows);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
