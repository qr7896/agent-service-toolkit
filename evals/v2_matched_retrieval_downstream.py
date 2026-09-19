from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
from evals.swe_tasks import grade,load_tasks,prepare
from evals.v2_grouped_robustness import source_problem_id

def audit(matched,tasks_path):
 specs={source_problem_id(s.instance_id):s for s in load_tasks(tasks_path)};rows=[]
 with tempfile.TemporaryDirectory(prefix="v2-matched-down-") as tmp:
  base=Path(tmp)
  for r in matched["rows"]:
   spec=specs[source_problem_id(r["task_id"])]
   outcomes={}
   for arm,payload in (("lexical",r["lexical"]["evidence_payload"]),("structural",r["structural"]["retained_payload"])):
    root=base/(source_problem_id(r["task_id"])+"-"+arm);prepare(spec,root);allowed={x["path"] for x in payload};written=[]
    for rel,c in spec.gold_sources.items():
     if rel in allowed:(root/rel).write_text(c,encoding="utf-8");written.append(rel)
    outcomes[arm]={"resolved":grade(spec,root)["resolved"],"gold_written":written}
   rows.append({"task_id":r["task_id"],**outcomes})
 return {"protocol":"v2-matched-retrieval-oracle-downstream-v1","tasks":len(rows),
  "lexical_resolved":sum(x["lexical"]["resolved"] for x in rows),"structural_resolved":sum(x["structural"]["resolved"] for x in rows),"rows":rows,
  "claim_boundary":"Constrained Oracle editability under matched retrieval arms; not autonomous repair and not a causal randomized modality comparison."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--matched",type=Path,required=True);ap.add_argument("--tasks",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.matched.read_text(encoding="utf-8")),a.tasks);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
