from __future__ import annotations
import argparse,json
from pathlib import Path

def audit(meu):
 rows=[];positive=0
 for x in meu["rows"]:
  if x["action"]!="structural":continue
  rows.append({"task_id":x["task_id"],"structural_meu":x["meu"],"retained_proxy_tokens":x["retained_proxy_tokens"],"unique_gain":x["unique_gain"]})
  positive+=x["meu"]>0
 return {"protocol":"v2-meu-structural-summary-v1","structural_actions":len(rows),"positive_meu":positive,
 "all_positive":positive==len(rows),"rows":rows,
 "claim_boundary":"Descriptive under arbitrary frozen diagnostic weights only; positive MEU does not establish optimality or causal downstream benefit."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.input.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
