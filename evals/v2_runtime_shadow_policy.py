from __future__ import annotations
import json
from pathlib import Path
from evals.evidence_runtime import ACTION_COST,ACTION_RISK
from evals.v2_contract_policy import predict_runtime

class ContextualShadowPolicy:
    """Predict V2 action from runtime state, but never controls execution."""
    version="v2-contextual-shadow-v1"
    def __init__(self, model_or_path):
        self.model=json.loads(Path(model_or_path).read_text()) if isinstance(model_or_path,(str,Path)) else model_or_path

    def predict(self, *, before, candidates, step):
        if not candidates:return "stop"
        return predict_runtime(self.model,before,candidates,step)

class PairedShadowDecisionLogger:
    def __init__(self, task_id, shadow_policy, writer):
        self.task_id=task_id;self.shadow_policy=shadow_policy;self.writer=writer;self.step=0
    def record(self, *, before, candidates, chosen_action, utility):
        safe=list(dict.fromkeys([a for a in candidates if a in ACTION_COST and
          before.get("remaining",{}).get("actions",0)>=1 and
          before.get("remaining",{}).get("cost",0)>=ACTION_COST[a] and
          before.get("remaining",{}).get("risk",0)>=ACTION_RISK[a]]))
        if "stop" not in safe:safe.append("stop")
        shadow=self.shadow_policy.predict(before=before,candidates=safe,step=self.step)
        row={"task_id":self.task_id,"step":self.step,"executed_action":chosen_action,"shadow_action":shadow,
             "agreement":shadow==chosen_action,"safe_candidates":safe,"policy_state":before}
        self.writer.append(row);self.step+=1;return row
