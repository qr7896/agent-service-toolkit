from __future__ import annotations
import argparse,json
from pathlib import Path

def validate(report):
 rows=report["rows"]
 bad=[r["task_id"] for r in rows if r["early_stop"]["unique_evidence"]<r["v1"]["unique_evidence"]]
 return {"protocol":"v2-early-stop-safety-gate-v1","tasks":len(rows),"evidence_count_regressions":bad,
  "all_equal_unique_evidence":not bad and all(r["delta"]["unique_evidence"]==0 for r in rows),
  "all_nonincreasing_actions":all(r["delta"]["actions"]<=0 for r in rows),
  "aggregate":report["aggregate"],
  "eligible_for_control":False,
  "reason":"Evidence replay is encouraging but downstream editor/test outcome is absent; remain shadow-only.",
  "claim_boundary":"This gate deliberately cannot authorize control without downstream task-outcome evidence."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=validate(json.loads(a.input.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
