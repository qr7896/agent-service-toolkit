from __future__ import annotations
import argparse,json
from pathlib import Path
from evals.serbench_upstream_resolver import resolve

def gate(root:Path|None=None)->dict:
 r=resolve(root)
 blockers=[]
 if not r["ready"]: blockers.append("upstream_checkout_unavailable")
 return {"protocol":"v2-external-eval-gate-v1","upstream":r,
  "example_allowed":not blockers,"cal500_allowed":False,"test500_allowed":False,
  "blockers":blockers,
  "next_action":"run official example integration" if not blockers else "provide verified SERBench checkout via SERBENCH_ROOT/--root",
  "claim_boundary":"Fail-closed orchestration gate; never treats local fixtures as official SERBench evaluation."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=gate(a.root);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
