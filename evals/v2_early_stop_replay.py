from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
from evals.evidence_controller import EvidenceController
from evals.evidence_policy import EvidenceBudget,EvidencePolicy
from evals.evidence_runtime import WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.v2_runtime_shadow_policy import ContextualShadowPolicy

class EarlyStopPolicy(EvidencePolicy):
 def __init__(self,budget,shadow):
  super().__init__(budget);self.shadow=shadow;self.step=0
 def choose(self,ledger,candidates,utility=None):
  before=self.state(ledger);chosen=super().choose(ledger,candidates,utility)
  safe=[a for a in candidates if a=="stop" or self.allowed(ledger,a)]
  if "stop" not in safe:safe.append("stop")
  shadow=self.shadow.predict(before=before,candidates=safe,step=self.step);self.step+=1
  return "stop" if shadow=="stop" else chosen

def run_branch(case,shadow=None):
 with tempfile.TemporaryDirectory(prefix="v2-early-stop-") as tmp:
  root=Path(tmp)
  for rel,content in case.get("files",{}).items():
   target=root/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding="utf-8")
  adapter=WorkspaceRetrievalAdapter(SafeWorkspace(root))
  budget=EvidenceBudget(max_actions=case.get("max_actions",2),max_cost=10,max_risk=10)
  policy=EarlyStopPolicy(budget,shadow) if shadow else EvidencePolicy(budget)
  plans=iter(case["plans"]);result=EvidenceController(adapter,policy).run(lambda _:next(plans,{"candidates":["stop"]}),max_steps=case.get("max_actions",2)+1)
  summary=adapter.ledger.summary();summary["evidence_payload"]=adapter.ledger.payload()
  return summary,result["trace"]

def replay(cases,model):
 shadow=ContextualShadowPolicy(model);rows=[]
 for case in cases:
  base,_=run_branch(case);early,_=run_branch(case,shadow)
  rows.append({"task_id":case["task_id"],"v1":base,"early_stop":early,
   "delta":{"actions":early["action_count"]-base["action_count"],"unique_evidence":early["unique_evidence"]-base["unique_evidence"],
    "cost":round(early["total_cost"]-base["total_cost"],4),"risk":round(early["total_risk"]-base["total_risk"],4)}})
 return {"protocol":"v2-safe-early-stop-replay-v1","tasks":len(rows),"rows":rows,
  "aggregate":{"action_delta":sum(x["delta"]["actions"] for x in rows),"unique_evidence_delta":sum(x["delta"]["unique_evidence"] for x in rows),
   "cost_delta":round(sum(x["delta"]["cost"] for x in rows),4),"risk_delta":round(sum(x["delta"]["risk"] for x in rows),4)},
  "claim_boundary":"Deterministic evidence-trajectory replay only; no editor/model/downstream repair outcome, so equal evidence count does not prove task sufficiency."}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--cases",type=Path,required=True);ap.add_argument("--model",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 r=replay(json.loads(a.cases.read_text(encoding="utf-8")),a.model);a.output.write_text(json.dumps(r,indent=2),encoding="utf-8");print(json.dumps({"tasks":r["tasks"],"aggregate":r["aggregate"]}))
if __name__=="__main__":main()
