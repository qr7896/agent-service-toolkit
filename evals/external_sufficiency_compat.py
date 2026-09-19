from __future__ import annotations
import argparse,json
from pathlib import Path

# Compatibility contract only. It deliberately does not implement SERBench or
# duplicate its evaluator. External records must be exported by the upstream
# benchmark and then normalized here.
REQUIRED=("external_state_id","repository","state_text","candidate_evidence")
OPTIONAL=("required_evidence_groups","source_commit","metadata")

def normalize(row:dict)->dict:
 missing=[k for k in REQUIRED if k not in row]
 if missing: raise ValueError(f"missing external fields: {missing}")
 candidates=row["candidate_evidence"]
 if not isinstance(candidates,list): raise ValueError("candidate_evidence must be a list")
 out={"external_state_id":str(row["external_state_id"]),"repository":str(row["repository"]),
      "state_text":str(row["state_text"]),"candidate_evidence":candidates}
 for k in OPTIONAL:
  if k in row: out[k]=row[k]
 return out

def inspect(rows:list[dict])->dict:
 normalized=[];errors=[]
 for i,row in enumerate(rows):
  try: normalized.append(normalize(row))
  except (TypeError,ValueError) as e: errors.append(f"row {i}: {e}")
 repos={x["repository"] for x in normalized}
 labelled=sum(bool(x.get("required_evidence_groups")) for x in normalized)
 return {"protocol":"external-sufficiency-compat-v1","records":len(normalized),"repositories":len(repos),
         "labelled_required_evidence_records":labelled,"errors":errors,
         "ready_for_compat_eval":bool(normalized) and not errors and labelled==len(normalized),
         "claim_boundary":"Schema adapter only; does not reproduce, vendor, or reimplement an external benchmark/evaluator."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 raw=json.loads(a.input.read_text(encoding="utf-8"));rows=raw if isinstance(raw,list) else raw.get("rows",[])
 report=inspect(rows);a.output.write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report))
if __name__=="__main__":main()
