from __future__ import annotations
import argparse,json,statistics
from pathlib import Path

def summarize(report):
 folds=report["folds"]; deltas=[x["delta_pp"] for x in folds]
 return {"protocol":"v2-logo-summary-v1","folds":len(folds),"positive":sum(x>0 for x in deltas),"zero":sum(x==0 for x in deltas),"negative":sum(x<0 for x in deltas),
 "delta_pp":{"min":min(deltas),"median":statistics.median(deltas),"max":max(deltas),"mean":round(statistics.mean(deltas),2)},
 "weighted_frequency":report["weighted_frequency"],"weighted_contextual":report["weighted_contextual"],
 "claim_boundary":"Descriptive cross-validation robustness summary, not a confidence interval or causal effect."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=summarize(json.loads(a.input.read_text()));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
