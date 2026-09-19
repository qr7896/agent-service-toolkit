from __future__ import annotations
import argparse,json
from pathlib import Path

def complete_set_recovery(row:dict,selected_ids:set[str])->bool:
 groups=row.get("required_evidence_groups") or []
 return bool(groups) and all(any(eid in selected_ids for eid in group) for group in groups)

def evaluate(rows:list[dict],selections:dict[str,list[str]])->dict:
 out=[]
 for row in rows:
  sid=str(row["external_state_id"]);selected=set(selections.get(sid,[]))
  recovered=complete_set_recovery(row,selected)
  out.append({"external_state_id":sid,"selected_items":len(selected),"complete_set_recovered":recovered})
 return {"protocol":"external-complete-set-recovery-v1","states":len(out),
         "complete_set_recovered":sum(x["complete_set_recovered"] for x in out),
         "complete_set_recovery_rate":sum(x["complete_set_recovered"] for x in out)/len(out) if out else 0.0,
         "rows":out,
         "claim_boundary":"Generic compatibility metric over externally supplied required-evidence groups; use upstream benchmark evaluator as authoritative whenever available."}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--states",type=Path,required=True);ap.add_argument("--selections",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 rows=json.loads(a.states.read_text(encoding="utf-8"));sel=json.loads(a.selections.read_text(encoding="utf-8"));r=evaluate(rows,sel);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in r.items() if k!="rows"}))
if __name__=="__main__":main()
