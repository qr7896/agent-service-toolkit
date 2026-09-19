from __future__ import annotations
import argparse,json
from pathlib import Path

def audit(budget):
 rows=[]
 for x in budget["rows"]:
  denom=x["retained_proxy_tokens"]
  rows.append({"task_id":x["task_id"],"step":x["step"],"action":x["action"],
   "unique_gain_per_100_proxy_tokens":100*x["unique_gain"]/denom if denom else None,
   "unique_gain_per_cost":x["unique_gain"]/x["cost"] if x["cost"] else None,
   "unique_gain_per_risk":x["unique_gain"]/x["risk"] if x["risk"] else None})
 by={}
 for action in sorted({x["action"] for x in rows}):
  group=[x for x in rows if x["action"]==action];by[action]={}
  for metric in ("unique_gain_per_100_proxy_tokens","unique_gain_per_cost","unique_gain_per_risk"):
   vals=[x[metric] for x in group if x[metric] is not None];by[action][metric]=sum(vals)/len(vals)
 return {"protocol":"v2-weight-free-efficiency-v1","by_action":by,"rows":rows,
  "claim_boundary":"Weight-free descriptive ratios using runtime-observable unique evidence, not Gold useful evidence or downstream policy value."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--budget",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.budget.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"by_action":r["by_action"]}))
if __name__=="__main__":main()
