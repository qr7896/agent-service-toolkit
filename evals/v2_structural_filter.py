from __future__ import annotations
import argparse,json
from pathlib import Path

def select(payload):
 # Runtime-only filter: keep structural definitions/imports and non-test source evidence;
 # discard test callers and generic caller noise.
 out=[]
 for x in payload:
  if x["source"]!="structural":continue
  is_test=Path(x["path"]).name.startswith("test_")
  if (not is_test and x.get("relation_type") in {"definition","import","caller"}) or (x.get("relation_type")=="definition" and not is_test):
   out.append(x)
 return out
def audit(replay):
 rows=[];before=after=0
 for r in replay["rows"]:
  p=r["adaptive"]["evidence_payload"];struct=[x for x in p if x["source"]=="structural"];kept=select(p);before+=len(struct);after+=len(kept)
  rows.append({"task_id":r["task_id"],"structural_before":len(struct),"structural_after":len(kept),"reduction":len(struct)-len(kept),"kept_paths":sorted({x["path"] for x in kept})})
 return {"protocol":"v2-runtime-structural-filter-v1","structural_before":before,"structural_after":after,"reduction":before-after,
  "reduction_rate":(before-after)/before if before else 0,"rows":rows,
  "claim_boundary":"Filter uses only runtime path/relation metadata; coverage impact requires separate retrospective scoring."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.replay.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
