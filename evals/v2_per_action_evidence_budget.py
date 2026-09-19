from __future__ import annotations
import argparse,json,re
from pathlib import Path
from evals.v2_structural_filter_v3 import select
_TOKEN=re.compile(r"\w+|[^\w\s]",re.UNICODE)
def toks(s): return len(_TOKEN.findall(s or ""))

def audit(replay):
 rows=[]
 for r in replay["rows"]:
  actions=r["adaptive"]["actions"];payload=r["adaptive"]["evidence_payload"]
  for i,a in enumerate(actions):
   source=a["action"];items=[x for x in payload if x["source"]==source]
   # For structural, report both raw acquisition and V3 retained context.
   retained=select(payload) if source=="structural" else items
   rows.append({"task_id":r["task_id"],"step":i,"action":source,"unique_gain":a["new"],"cost":a["cost"],"risk":a["risk"],
    "raw_items":len(items),"raw_chars":sum(len(x["content"]) for x in items),"raw_proxy_tokens":sum(toks(x["content"]) for x in items),
    "retained_items":len(retained),"retained_chars":sum(len(x["content"]) for x in retained),"retained_proxy_tokens":sum(toks(x["content"]) for x in retained)})
 return {"protocol":"v2-per-action-evidence-budget-v1","records":len(rows),"rows":rows,
 "claim_boundary":"Deterministic regex proxy tokens, not provider tokens. Structural retained_* reflects runtime-only V3 filtering."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.replay.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"records":r["records"]}))
if __name__=="__main__":main()
