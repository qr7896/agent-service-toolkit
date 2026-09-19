from __future__ import annotations
import argparse,json,re
from pathlib import Path
from evals.swe_tasks import load_tasks
from evals.v2_grouped_robustness import source_problem_id
TOK=re.compile(r"\w+|[^\w\s]",re.UNICODE)
def n_tok(items): return sum(len(TOK.findall(x.get("content",""))) for x in items)
def audit(matched,tasks_path):
 specs={source_problem_id(s.instance_id):s for s in load_tasks(tasks_path)};rows=[]
 for r in matched["rows"]:
  gold=set(specs[source_problem_id(r["task_id"])].gold_files)
  lp=r["lexical"]["evidence_payload"];sp=r["structural"]["retained_payload"]
  rows.append({"task_id":r["task_id"],
   "lexical":{"unique":r["lexical"]["summary"]["unique_evidence"],"proxy_tokens":n_tok(lp),"gold_hit":bool({x["path"] for x in lp}&gold),"cost":r["lexical"]["summary"]["total_cost"],"risk":r["lexical"]["summary"]["total_risk"]},
   "structural":{"unique":len(sp),"proxy_tokens":n_tok(sp),"gold_hit":bool({x["path"] for x in sp}&gold),"cost":r["structural"]["summary"]["total_cost"],"risk":r["structural"]["summary"]["total_risk"]}})
 return {"protocol":"v2-matched-retrieval-audit-v1","tasks":len(rows),
  "lexical_gold_hit":sum(x["lexical"]["gold_hit"] for x in rows),"structural_gold_hit":sum(x["structural"]["gold_hit"] for x in rows),
  "lexical_proxy_tokens":sum(x["lexical"]["proxy_tokens"] for x in rows),"structural_proxy_tokens":sum(x["structural"]["proxy_tokens"] for x in rows),
  "lexical_unique":sum(x["lexical"]["unique"] for x in rows),"structural_retained_unique":sum(x["structural"]["unique"] for x in rows),"rows":rows,
  "claim_boundary":"Gold is retrospective scoring only. Matched initial state/action count reduces one confound but does not randomize retrieval semantics or prove causal superiority."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--matched",type=Path,required=True);ap.add_argument("--tasks",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.matched.read_text(encoding="utf-8")),a.tasks);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
