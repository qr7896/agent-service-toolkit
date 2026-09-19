from __future__ import annotations
import argparse,json
from pathlib import Path

def summary(early,adaptive,base_down,adaptive_down):
 v1_actions=early["rows"][0]["v1"]["action_count"] if False else sum(r["v1"]["action_count"] for r in early["rows"])
 v1_cost=sum(r["v1"]["total_cost"] for r in early["rows"]);v1_risk=sum(r["v1"]["total_risk"] for r in early["rows"])
 es_actions=sum(r["early_stop"]["action_count"] for r in early["rows"]);es_cost=sum(r["early_stop"]["total_cost"] for r in early["rows"]);es_risk=sum(r["early_stop"]["total_risk"] for r in early["rows"])
 a=adaptive["aggregate"]
 rows=[
  {"policy":"v1_repeat_lexical","actions":v1_actions,"cost":round(v1_cost,4),"risk":round(v1_risk,4),"oracle_resolved":base_down["v1_resolved"]},
  {"policy":"pure_early_stop","actions":es_actions,"cost":round(es_cost,4),"risk":round(es_risk,4),"oracle_resolved":base_down["early_stop_resolved"]},
  {"policy":"adaptive_stop_or_structural","actions":a["actions"],"cost":a["cost"],"risk":a["risk"],"oracle_resolved":adaptive_down["resolved"]}]
 return {"protocol":"v2-cost-coverage-pareto-v1","tasks":adaptive["tasks"],"rows":rows,
  "descriptive_frontier":["pure_early_stop","adaptive_stop_or_structural"],
  "claim_boundary":"Pareto description uses constrained Oracle editability, not autonomous repair success; no policy winner is claimed."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--early",type=Path,required=True);ap.add_argument("--adaptive",type=Path,required=True);ap.add_argument("--baseline-downstream",type=Path,required=True);ap.add_argument("--adaptive-downstream",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=summary(*[json.loads(x.read_text(encoding="utf-8")) for x in [a.early,a.adaptive,a.baseline_downstream,a.adaptive_downstream]]);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
