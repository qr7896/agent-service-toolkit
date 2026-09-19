from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
from evals.swe_tasks import grade,load_tasks,prepare
from evals.v2_grouped_robustness import source_problem_id

def evidence_paths(summary):
 return {x["path"] for x in summary.get("evidence",[])}

def oracle_edit(spec,root,allowed):
 written=[]
 for rel,content in spec.gold_sources.items():
  if rel in allowed:
   t=root/rel;t.parent.mkdir(parents=True,exist_ok=True);t.write_text(content,encoding="utf-8");written.append(rel)
 return written

def evaluate(replay_path,tasks_path):
 replay=json.loads(replay_path.read_text(encoding="utf-8"));specs={source_problem_id(s.instance_id):s for s in load_tasks(tasks_path)};rows=[]
 with tempfile.TemporaryDirectory(prefix="v2-downstream-") as tmp:
  base=Path(tmp)
  for rr in replay["rows"]:
   sid=source_problem_id(rr["task_id"]);spec=specs.get(sid)
   if spec is None:continue
   result={"task_id":rr["task_id"],"instance_id":sid}
   for branch,key in [("v1","v1"),("early_stop","early_stop")]:
    root=base/f"{branch}-{sid}";prepare(spec,root);before=grade(spec,root)
    allowed={x["path"] for x in rr[key].get("evidence_payload",[])}
    written=oracle_edit(spec,root,allowed);after=grade(spec,root)
    result[branch]={"allowed_files":sorted(allowed),"gold_written":written,"resolved":after["resolved"],"base_resolved":before["resolved"],"grade":after}
   result["preserved"]=result["v1"]["resolved"]==result["early_stop"]["resolved"]
   rows.append(result)
 return {"protocol":"v2-early-stop-oracle-downstream-v1","scope":"constrained Oracle Editor upper-bound preservation check",
  "tasks":len(rows),"v1_resolved":sum(r["v1"]["resolved"] for r in rows),"early_stop_resolved":sum(r["early_stop"]["resolved"] for r in rows),
  "outcome_preserved":sum(r["preserved"] for r in rows),"rows":rows,
  "claim_boundary":"Oracle editability upper bound only; not autonomous repair success and not evidence that a model editor can patch from early-stop context."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--tasks",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=evaluate(a.replay,a.tasks);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
