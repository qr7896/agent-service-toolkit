from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from evals.swe_tasks import load_tasks
from evals.v2_grouped_robustness import source_problem_id

def metrics(payload,gold):
 structural=[x for x in payload if x["source"]=="structural"]; target=[x for x in structural if x["path"] in gold]
 source=[x for x in structural if not Path(x["path"]).name.startswith("test_")]
 return {"structural_items":len(structural),"target_items":len(target),"source_items":len(source),
  "target_precision":len(target)/len(structural) if structural else None,
  "source_precision":len(source)/len(structural) if structural else None,
  "target_paths":sorted({x["path"] for x in target})}

def audit(replay,tasks_path):
 specs={source_problem_id(s.instance_id):s for s in load_tasks(tasks_path)};rows=[]
 for r in replay["rows"]:
  spec=specs[source_problem_id(r["task_id"])];m=metrics(r["adaptive"]["evidence_payload"],set(spec.gold_files));m["task_id"]=r["task_id"];m["decision"]=r["adaptive"]["adaptive_decision"];rows.append(m)
 esc=[r for r in rows if r["decision"]=="structural"]
 total=sum(r["structural_items"] for r in esc);target=sum(r["target_items"] for r in esc);source=sum(r["source_items"] for r in esc)
 return {"protocol":"v2-structural-noise-audit-v1","tasks":len(rows),"escalated_tasks":len(esc),"structural_items":total,"target_items":target,"source_items":source,
 "micro_target_precision":target/total if total else 0,"micro_source_precision":source/total if total else 0,
 "all_escalations_hit_target":all(r["target_items"]>0 for r in esc),"rows":rows,
 "claim_boundary":"Gold paths are used retrospectively for precision scoring only; not available to runtime retrieval."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--tasks",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.replay.read_text(encoding="utf-8")),a.tasks);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
