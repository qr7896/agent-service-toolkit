from __future__ import annotations
import argparse,json
from pathlib import Path

def compare(downstream,probe):
 unresolved={r["task_id"] for r in downstream["rows"] if not r["v1"]["resolved"]}
 rows=[r for r in probe["rows"] if r["task_id"] in unresolved]
 return {"protocol":"v2-coverage-escalation-summary-v1","unresolved_tasks":len(rows),
  "structural_gold_hit":sum(r["gold_hit"] for r in rows),
  "coverage_recovery_rate":sum(r["gold_hit"] for r in rows)/len(rows) if rows else 0,
  "candidate_rule":"if lexical yields no target-bearing source evidence and runtime-visible call symbols exist, consider bounded structural neighbors before stop",
  "claim_boundary":"Retrospective coverage recovery only; does not establish downstream repair benefit or authorize runtime control."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--downstream",type=Path,required=True);ap.add_argument("--probe",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=compare(json.loads(a.downstream.read_text(encoding="utf-8")),json.loads(a.probe.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
