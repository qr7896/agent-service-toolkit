from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT
OUT=ROOT/'data/e1c_strict_v15_prereg.json'; B=ROOT/'data/e1c_strict_v15_selection_boundary.json'
FILES=('e1c_strict_v5_boundary.py','e1c_strict_v6_probe.py','e1c_strict_v7_witness_ir.py','e1c_strict_v7_probe.py','e1c_strict_v7_runner.py','e1c_strict_v8_source_contract.py','e1c_strict_v8_probe.py','e1c_strict_v9_observable.py','e1c_strict_v9_probe.py','e1c_strict_v10_observable.py','e1c_strict_v10_probe.py','e1c_strict_v14_observable.py','e1c_strict_v14_probe.py','e1c_strict_v15_probe.py')
def build():
 raw=B.read_bytes(); b=json.loads(raw); assert b['canary_selected'] is False; fs=[]
 for n in FILES:
  p=ROOT/'evals'/n; fs.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size})
 v={'schema':'e1c-strict-v15-reproducer-prereg-v1','provider_calls':0,'live_model_run':False,'canary_selected_at_freeze':False,'prior_canary_reuse_allowed':False,'selection_salt':'e1c-strict-v15-independent-canary','canary_task_count':3,'minimum_candidate_reproducer_tasks':2,'minimum_trusted_reproducers':2,'live_allowed_before_admission':False,'mechanism_files':fs,'mechanism_sha256':hashlib.sha256(json.dumps(fs,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'selection_boundary_sha256':hashlib.sha256(raw).hexdigest(),'development_replay_is_independent_evidence':False,'development_consensus_gate':'materially_exceeds_2_of_6','development_consensus_observed':4}; v['prereg_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
if __name__=='__main__': OUT.write_text(json.dumps(build(),indent=2)+'\n',encoding='utf-8'); print(json.dumps(build(),indent=2))
