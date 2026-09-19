from __future__ import annotations
import argparse,json
from pathlib import Path

# A path is a test only when it is an actual test module, not merely a source
# module whose basename starts with "test_" (e.g. src/agents/test_tools.py).
def is_test_path(path):
 name=Path(path).name
 return path.startswith("tests/") or name.startswith("test_research__") or name.endswith("_test.py")

def select(payload):
 out=[]
 for x in payload:
  if x.get("source")!="structural" or is_test_path(x["path"]):continue
  if x.get("relation_type") in {"definition","import","caller"}:out.append(x)
 return out

def audit(replay):
 before=after=0;rows=[]
 for r in replay["rows"]:
  struct=[x for x in r["adaptive"]["evidence_payload"] if x.get("source")=="structural"];kept=select(r["adaptive"]["evidence_payload"]);before+=len(struct);after+=len(kept)
  rows.append({"task_id":r["task_id"],"before":len(struct),"after":len(kept),"kept_paths":sorted({x["path"] for x in kept})})
 return {"protocol":"v2-structural-filter-v3","before":before,"after":after,"reduction":before-after,"reduction_rate":(before-after)/before if before else 0,"rows":rows,
 "claim_boundary":"Runtime-only path/relation filter. Test classification is path-aware to avoid false positives such as src/agents/test_tools.py."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--replay",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.replay.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
