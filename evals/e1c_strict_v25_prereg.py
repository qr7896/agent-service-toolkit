from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT
OUT=ROOT/'data/e1c_strict_v25_prereg.json'
FILES=tuple(f'e1c_strict_v{i}_probe.py' for i in range(15,26) if (ROOT/'evals'/f'e1c_strict_v{i}_probe.py').exists())
def build():
 gate=json.loads((ROOT/'data/e1c_strict_v25_development_gate.json').read_text());rep=json.loads((ROOT/'data/e1c_strict_v25_dev_replay.json').read_text())
 assert rep['consensus_candidate_task_count']==gate['required_consensus_tasks']==6
 assert rep['minimum_consensus_family_support_per_task']>=gate['required_minimum_family_support_per_task']
 assert rep['total_consensus_family_support']>16
 fs=[]
 for n in FILES:
  p=ROOT/'evals'/n;fs.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size})
 v={'schema':'e1c-strict-v25-reproducer-prereg-v1','provider_calls':0,'live_model_run':False,'canary_selected_at_freeze':False,'prior_canary_reuse_allowed':False,'selection_salt':'e1c-strict-v25-independent-canary','canary_task_count':3,'minimum_candidate_reproducer_tasks':2,'minimum_trusted_reproducers':2,'live_allowed_before_admission':False,'mechanism_files':fs,'mechanism_sha256':hashlib.sha256(json.dumps(fs,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'development_gate_sha256':gate['gate_sha256'],'development_replay_sha256':rep['summary_sha256'],'development_consensus_tasks':6,'development_total_consensus_family_support':rep['total_consensus_family_support'],'development_minimum_family_support_per_task':rep['minimum_consensus_family_support_per_task'],'development_replay_is_independent_evidence':False};v['prereg_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();return v
if __name__=='__main__':
 v=build();OUT.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
