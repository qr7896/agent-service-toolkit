from __future__ import annotations
import argparse,json
from pathlib import Path
def calc(row,alpha=.01,beta=1.0,gamma=1.0):
 denom=alpha*row["retained_proxy_tokens"]+beta*row["cost"]+gamma*row["risk"]
 return row["unique_gain"]/denom if denom else 0.0
def audit(budget,alpha=.01,beta=1.0,gamma=1.0):
 rows=[]
 for x in budget["rows"]:
  y=dict(x);y["meu"]=calc(x,alpha,beta,gamma);rows.append(y)
 by={}
 for a in sorted({x["action"] for x in rows}):
  vals=[x["meu"] for x in rows if x["action"]==a];by[a]={"n":len(vals),"mean_meu":sum(vals)/len(vals),"min_meu":min(vals),"max_meu":max(vals)}
 return {"protocol":"v2-meu-token-aware-offline-v1","weights":{"alpha_proxy_token":alpha,"beta_cost":beta,"gamma_risk":gamma},"records":len(rows),"by_action":by,"rows":rows,
 "claim_boundary":"Offline descriptive diagnostic; proxy-token weights are not learned/calibrated and this metric must not drive runtime control or support causal superiority claims."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--budget",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.budget.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"records":r["records"],"by_action":r["by_action"]}))
if __name__=="__main__":main()
