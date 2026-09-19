from __future__ import annotations
import argparse,json,re
from pathlib import Path
from evals.v2_structural_filter_v3 import select

_TOKEN=re.compile(r"\w+|[^\w\s]",re.UNICODE)
def approx_tokens(text): return len(_TOKEN.findall(text))
def size(items):
 chars=sum(len(x.get("content","")) for x in items);tokens=sum(approx_tokens(x.get("content","")) for x in items)
 return {"items":len(items),"chars":chars,"approx_tokens":tokens}

def audit(replay):
 rows=[]
 for r in replay["rows"]:
  payload=r["adaptive"]["evidence_payload"];struct=[x for x in payload if x.get("source")=="structural"];kept=select(payload)
  b=size(struct);a=size(kept)
  rows.append({"task_id":r["task_id"],"before":b,"after":a,
   "char_reduction_rate":1-a["chars"]/b["chars"] if b["chars"] else 0,
   "approx_token_reduction_rate":1-a["approx_tokens"]/b["approx_tokens"] if b["approx_tokens"] else 0})
 B={k:sum(x["before"][k] for x in rows) for k in ("items","chars","approx_tokens")};A={k:sum(x["after"][k] for x in rows) for k in B}
 return {"protocol":"v2-evidence-budget-audit-v1","tokenizer":"deterministic regex proxy, not provider tokenizer","before":B,"after":A,
 "reduction":{"items":1-A["items"]/B["items"],"chars":1-A["chars"]/B["chars"],"approx_tokens":1-A["approx_tokens"]/B["approx_tokens"]},
 "rows":rows,"claim_boundary":"Approx-token is a deterministic local proxy and must not be reported as provider/model prompt tokens."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.replay.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
