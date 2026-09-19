from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
from evals.evidence_controller import EvidenceController
from evals.evidence_policy import EvidenceBudget,EvidencePolicy
from evals.evidence_runtime import WorkspaceRetrievalAdapter
from evals.safe_workspace import SafeWorkspace
from evals.v2_runtime_shadow_policy import ContextualShadowPolicy,PairedShadowDecisionLogger

def collect_shadow(cases,model_path,output):
 rows=[];shadow=ContextualShadowPolicy(model_path)
 with tempfile.TemporaryDirectory(prefix="v2-context-shadow-") as tmp:
  root=Path(tmp)
  for case in cases:
   workspace=root/case["task_id"];workspace.mkdir(parents=True,exist_ok=True)
   for rel,content in case.get("files",{}).items():
    target=workspace/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding="utf-8")
   adapter=WorkspaceRetrievalAdapter(SafeWorkspace(workspace))
   logger=PairedShadowDecisionLogger(case["task_id"],shadow,rows)
   controller=EvidenceController(adapter,EvidencePolicy(EvidenceBudget(max_actions=case.get("max_actions",2),max_cost=10,max_risk=10)),decision_logger=logger)
   plans=iter(case["plans"])
   controller.run(lambda _:next(plans,{"candidates":["stop"]}),max_steps=case.get("max_actions",2)+1)
 output.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
 return {"records":len(rows),"agreements":sum(x["agreement"] for x in rows),"agreement_rate":round(sum(x["agreement"] for x in rows)/len(rows),4) if rows else None}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--cases",type=Path,required=True);ap.add_argument("--model",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 print(json.dumps(collect_shadow(json.loads(a.cases.read_text(encoding="utf-8")),a.model,a.output)))
if __name__=="__main__":main()
