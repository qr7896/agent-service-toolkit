from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

def analyze(path):
 rows=[json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
 pairs=Counter((r["executed_action"],r["shadow_action"]) for r in rows)
 disagreements=[r for r in rows if not r["agreement"]]
 return {"records":len(rows),"agreements":len(rows)-len(disagreements),"disagreements":len(disagreements),
 "pair_counts":{f"{a}->{b}":n for (a,b),n in sorted(pairs.items())},
 "disagreement_by_step":dict(Counter(str(r["step"]) for r in disagreements)),
 "claim_boundary":"Diagnostic shadow disagreement decomposition; executed V1 action is not ground truth optimality."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=analyze(a.input);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps(r))
if __name__=="__main__":main()
