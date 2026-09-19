from __future__ import annotations
import argparse,json
from pathlib import Path

def classify(report):
 out=[]
 for x in report["case_details"]:
  if x["new_unique_evidence"]==0 and x["redundancy_delta"]>0: label="redundant_continue"
  elif x["new_unique_evidence"]==0: label="zero_unique_gain"
  else: label="novel_evidence_continue"
  out.append({**x,"descriptive_label":label})
 counts={}
 for x in out:counts[x["descriptive_label"]]=counts.get(x["descriptive_label"],0)+1
 return {"protocol":"v2-evidence-sufficiency-diagnostic-v1","counts":counts,"cases":out,
 "claim_boundary":"Labels describe observed evidence deltas, not task sufficiency or correctness after early stopping."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=classify(json.loads(a.input.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"counts":r["counts"]}))
if __name__=="__main__":main()
