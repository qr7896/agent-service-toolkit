from __future__ import annotations
import argparse,json
from collections import defaultdict
from pathlib import Path

def evaluate(rows):
 by=defaultdict(list)
 for r in rows:by[r["task_id"]].append(r)
 cases=[]
 for task,rs in sorted(by.items()):
  rs=sorted(rs,key=lambda x:x["step"])
  for i,r in enumerate(rs[:-1]):
   if r["shadow_action"]=="stop" and r["executed_action"]!="stop":
    nxt=rs[i+1];b=r["policy_state"];a=nxt["policy_state"]
    gain=max(0,a.get("unique_evidence",0)-b.get("unique_evidence",0))
    dc=round(a["spent"]["cost"]-b["spent"]["cost"],4);dr=round(a["spent"]["risk"]-b["spent"]["risk"],4)
    red=round(a.get("mean_redundancy",0)-b.get("mean_redundancy",0),4)
    cases.append({"task_id":task,"step":r["step"],"continue_action":r["executed_action"],"new_unique_evidence":gain,
      "incremental_cost":dc,"incremental_risk":dr,"redundancy_delta":red,
      "descriptive_stop_savings":{"cost":dc,"risk":dr,"actions":1},
      "continue_added_unique_evidence":gain>0})
 return {"protocol":"v2-stop-continue-counterfactual-descriptive-v1","cases":len(cases),
  "continue_added_unique_evidence_cases":sum(x["continue_added_unique_evidence"] for x in cases),
  "zero_unique_gain_cases":sum(not x["continue_added_unique_evidence"] for x in cases),
  "total_incremental_cost":round(sum(x["incremental_cost"] for x in cases),4),
  "total_incremental_risk":round(sum(x["incremental_risk"] for x in cases),4),
  "case_details":cases,
  "claim_boundary":"Observed continuation marginal evidence/cost only. Early-stop outcome is unobserved, so this is not a causal counterfactual or proof that stopping is better."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 rows=[json.loads(x) for x in a.input.read_text(encoding="utf-8").splitlines() if x.strip()];r=evaluate(rows);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="case_details"}))
if __name__=="__main__":main()
