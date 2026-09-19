from __future__ import annotations
import argparse,json
from pathlib import Path

def meu(unique_gain,tokens,cost,risk,alpha=1.0,beta=1.0,gamma=1.0):
 denom=alpha*tokens+beta*cost+gamma*risk
 return unique_gain/denom if denom>0 else 0.0

def audit(replay,alpha=1.0,beta=1.0,gamma=1.0):
 rows=[]
 for r in replay["rows"]:
  for step,a in enumerate(r["adaptive"]["actions"]):
   # Offline diagnostic only: "new" is runtime-observable unique ledger gain.
   tokens=0
   if a["action"]=="structural":
    # Action summaries do not carry bytes; use returned count only as zero-token placeholder.
    # Evidence-volume-aware MEU requires joining the budget audit and is intentionally not faked here.
    tokens=0
   rows.append({"task_id":r["task_id"],"step":step,"action":a["action"],"unique_gain":a["new"],"returned":a["returned"],
    "cost":a["cost"],"risk":a["risk"],"redundancy":a["redundancy"],
    "meu_without_token_term":meu(a["new"],0,a["cost"],a["risk"],0,beta,gamma)})
 return {"protocol":"v2-meu-offline-diagnostic-v1","weights":{"alpha_token":alpha,"beta_cost":beta,"gamma_risk":gamma},
  "records":len(rows),"rows":rows,
  "claim_boundary":"Offline diagnostic only. No Gold is used. Token term is deliberately excluded until per-action evidence-token accounting is joined; this file must not drive runtime control."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=audit(json.loads(a.replay.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"records":r["records"],"protocol":r["protocol"]}))
if __name__=="__main__":main()
