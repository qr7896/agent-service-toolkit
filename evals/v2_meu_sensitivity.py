from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
from evals.v2_meu_token_aware import calc

# Reuse the existing MEU implementation; this file only audits weight sensitivity.
ALPHAS=(0.0,0.001,0.01,0.1,1.0)
BETAS=(0.25,1.0,4.0)
GAMMAS=(0.25,1.0,4.0)

def audit(budget):
 grid=[];structural_higher=0
 for alpha,beta,gamma in itertools.product(ALPHAS,BETAS,GAMMAS):
  by={}
  for action in ("lexical","structural"):
   vals=[calc(x,alpha,beta,gamma) for x in budget["rows"] if x["action"]==action]
   by[action]=sum(vals)/len(vals)
  higher=by["structural"]>by["lexical"];structural_higher+=higher
  grid.append({"alpha":alpha,"beta":beta,"gamma":gamma,"lexical_mean":by["lexical"],"structural_mean":by["structural"],"structural_higher":higher,"ratio":by["structural"]/by["lexical"] if by["lexical"] else None})
 return {"protocol":"v2-meu-weight-sensitivity-v1","grid_points":len(grid),"structural_higher_points":structural_higher,
  "structural_higher_fraction":structural_higher/len(grid),"grid":grid,
  "claim_boundary":"Sensitivity audit of an offline proxy metric. The grid is not fitted, statistical inference, policy evaluation, or evidence of causal superiority."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--budget",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();r=audit(json.loads(a.budget.read_text(encoding="utf-8")));a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="grid"}))
if __name__=="__main__":main()
