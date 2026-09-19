from __future__ import annotations
import argparse,json
from pathlib import Path
def compare(base,adaptive):
 return {"protocol":"v2-adaptive-vs-v1-summary-v1","tasks":adaptive["tasks"],
 "v1_oracle_resolved":base["v1_resolved"],"adaptive_oracle_resolved":adaptive["resolved"],
 "resolved_delta":adaptive["resolved"]-base["v1_resolved"],
 "claim_boundary":"Constrained Oracle editability comparison; not autonomous repair rate. Adaptive retrieval uses no Gold for decisions."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--baseline",type=Path,required=True);ap.add_argument("--adaptive",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=compare(json.loads(a.baseline.read_text(encoding="utf-8")),json.loads(a.adaptive.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
