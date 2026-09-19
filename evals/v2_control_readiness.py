from __future__ import annotations
import argparse,json
from pathlib import Path

def gate(replay,downstream):
 evidence_ok=all(r["delta"]["unique_evidence"]==0 for r in replay["rows"])
 preservation=downstream["outcome_preserved"]==downstream["tasks"] and downstream["tasks"]>0
 return {"protocol":"v2-control-readiness-v1","evidence_replay_preserved":evidence_ok,
  "oracle_outcome_preserved":preservation,"oracle_v1_resolved":downstream["v1_resolved"],"oracle_early_stop_resolved":downstream["early_stop_resolved"],
  "eligible_for_autonomous_control":False,
  "remaining_blockers":["non-oracle editor outcome preservation","prospective non-sealed DEV validation","explicit protocol freeze before any sealed TEST"],
  "claim_boundary":"Oracle preservation is necessary evidence but insufficient to authorize autonomous policy control."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--downstream",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=gate(json.loads(a.replay.read_text(encoding="utf-8")),json.loads(a.downstream.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
