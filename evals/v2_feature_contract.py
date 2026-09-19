from __future__ import annotations
from dataclasses import dataclass,asdict

FEATURE_NAMES=("step","actions_tried","evidence_items","total_cost","total_risk","mean_redundancy")

@dataclass(frozen=True)
class EvidenceStateFeatures:
 step:int
 actions_tried:int
 evidence_items:int
 total_cost:float
 total_risk:float
 mean_redundancy:float
 def vector(self): return [float(getattr(self,k)) for k in FEATURE_NAMES]
 def to_dict(self): return asdict(self)

def from_policy_state(before:dict,step:int)->EvidenceStateFeatures:
 spent=before.get("spent",{})
 return EvidenceStateFeatures(step,int(spent.get("actions",0)),int(before.get("unique_evidence",0)),
  float(spent.get("cost",0.0)),float(spent.get("risk",0.0)),float(before.get("mean_redundancy",0.0)))

def from_decision_record(row:dict)->EvidenceStateFeatures:
 s=row.get("state",{});ps=s.get("policy_state")
 if isinstance(ps,dict): return from_policy_state(ps,int(row.get("step",0)))
 # Legacy deterministic records: use only fields with direct runtime meaning; no proxy fabrication.
 return EvidenceStateFeatures(int(row.get("step",0)),int(s.get("actions_tried",0)),
  int(s.get("artifact_files",0))+int(s.get("artifact_symbols",0))+int(s.get("artifact_tests",0))+int(s.get("artifact_callers",0)),
  float(s.get("cost_spent",0.0)),float(s.get("risk_spent",0.0)),float(s.get("mean_redundancy",0.0)))
