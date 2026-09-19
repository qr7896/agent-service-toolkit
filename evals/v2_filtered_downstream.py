from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
from evals.swe_tasks import grade,load_tasks,prepare
from evals.v2_grouped_robustness import source_problem_id
from evals.v2_structural_filter_v3 import select

def evaluate(replay,tasks_path):
 specs={source_problem_id(s.instance_id):s for s in load_tasks(tasks_path)};rows=[]
 with tempfile.TemporaryDirectory(prefix="v2-filtered-oracle-") as tmp:
  base=Path(tmp)
  for rr in replay["rows"]:
   sid=source_problem_id(rr["task_id"]);spec=specs[sid];root=base/sid;prepare(spec,root)
   payload=rr["adaptive"]["evidence_payload"];allowed={x["path"] for x in payload if x["source"]!="structural"}|{x["path"] for x in select(payload)}
   written=[]
   for rel,c in spec.gold_sources.items():
    if rel in allowed:(root/rel).write_text(c,encoding="utf-8");written.append(rel)
   g=grade(spec,root);rows.append({"task_id":rr["task_id"],"resolved":g["resolved"],"allowed_files":sorted(allowed),"gold_written":written})
 return {"protocol":"v2-filter-v3-oracle-downstream-v1","tasks":len(rows),"resolved":sum(x["resolved"] for x in rows),"rows":rows,
 "claim_boundary":"Constrained Oracle editability after runtime-only structural filtering; not autonomous repair."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--tasks",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=evaluate(json.loads(a.replay.read_text(encoding="utf-8")),a.tasks);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"tasks":r["tasks"],"resolved":r["resolved"]}))
if __name__=="__main__":main()
