from __future__ import annotations
import argparse,json
from pathlib import Path

def audit(report):
 rows=[r for r in report["rows"] if r["items_before"]>0]
 ratios=[]
 for r in rows:
  bt=r["approx_tokens_before"];at=r["approx_tokens_after"]
  ratios.append({"task_id":r["task_id"],"before":bt,"after":at,"reduction_rate":1-at/bt if bt else 0})
 vals=sorted(x["reduction_rate"] for x in ratios)
 return {"protocol":"v2-compression-robustness-v1","tasks":len(ratios),
 "min_reduction":min(vals) if vals else 0,"median_reduction":vals[len(vals)//2] if vals else 0,"max_reduction":max(vals) if vals else 0,
 "all_positive":all(x["reduction_rate"]>0 for x in ratios),"rows":ratios,
 "claim_boundary":"Per-task deterministic proxy-token compression; not provider token accounting."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.input.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
