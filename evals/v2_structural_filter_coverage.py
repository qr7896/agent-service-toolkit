from __future__ import annotations
import argparse,json
from pathlib import Path
from evals.swe_tasks import load_tasks
from evals.v2_grouped_robustness import source_problem_id
from evals.v2_structural_filter import select
def score(replay,tasks_path):
 specs={source_problem_id(s.instance_id):s for s in load_tasks(tasks_path)};rows=[]
 for r in replay["rows"]:
  if r["adaptive"]["adaptive_decision"]!="structural":continue
  kept=select(r["adaptive"]["evidence_payload"]);gold=set(specs[source_problem_id(r["task_id"])].gold_files);hit=bool({x["path"] for x in kept}&gold)
  rows.append({"task_id":r["task_id"],"kept":len(kept),"gold_hit":hit})
 return {"protocol":"v2-structural-filter-coverage-v1","escalated_tasks":len(rows),"gold_hit_tasks":sum(x["gold_hit"] for x in rows),"all_gold_hit":all(x["gold_hit"] for x in rows),"rows":rows,
 "claim_boundary":"Gold used only after runtime-only filtering for retrospective coverage scoring."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--tasks",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=score(json.loads(a.replay.read_text(encoding="utf-8")),a.tasks);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
