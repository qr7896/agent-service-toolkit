from __future__ import annotations
import argparse,json
from pathlib import Path

def audit(budget,coverage,downstream):
 rows=[]
 for b in budget["rows"]:
  c=next((x for x in coverage["rows"] if x["task_id"]==b["task_id"]),None)
  d=next((x for x in downstream["rows"] if x["task_id"]==b["task_id"]),None)
  rows.append({"task_id":b["task_id"],"items_before":b["before"]["items"],"items_after":b["after"]["items"],
   "chars_before":b["before"]["chars"],"chars_after":b["after"]["chars"],
   "approx_tokens_before":b["before"]["approx_tokens"],"approx_tokens_after":b["after"]["approx_tokens"],
   "target_hit":None if c is None else c["gold_hit"],"oracle_resolved":None if d is None else d["resolved"]})
 esc=[r for r in rows if r["items_before"]>0]
 return {"protocol":"v2-compression-preservation-v1","escalated_tasks":len(esc),
 "all_target_coverage_preserved":all(r["target_hit"] for r in esc),"all_oracle_outcomes_resolved":all(r["oracle_resolved"] for r in rows),
 "aggregate_reduction":budget["reduction"],"rows":rows,
 "claim_boundary":"Joint descriptive audit: local evidence compression + retrospective target coverage + constrained Oracle outcome."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--budget",type=Path,required=True);ap.add_argument("--coverage",type=Path,required=True);ap.add_argument("--downstream",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 vals=[json.loads(x.read_text(encoding="utf-8")) for x in [a.budget,a.coverage,a.downstream]];r=audit(*vals);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
