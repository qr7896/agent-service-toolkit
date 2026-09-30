from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT
OUT=ROOT/'data/e1c_strict_v14_selection_boundary.json'; SALT='e1c-strict-v14-independent-canary'
def build():
 base=json.loads((ROOT/'data/e1c_strict_v13_selection_boundary.json').read_text(encoding='utf-8')); prev=json.loads((ROOT/'data/e1c_strict_v13_canary_manifest.json').read_text(encoding='utf-8')); excluded=list(dict.fromkeys(base['explicit_prior_canary_exclusions']+[x['instance_id'] for x in prev['tasks']]))
 v={'schema':'e1c-strict-v14-selection-boundary-v1','provider_calls':0,'task_content_inspected':False,'canary_selected':False,'mechanism_must_be_frozen_before_canary_selection':True,'selection_salt':SALT,'explicit_prior_canary_exclusions':excluded,'task_repo_revision':base['task_repo_revision'],'inventory_revision':base['inventory_revision'],'prior_canary_reuse_allowed':False,'outcome_conditioned_replacement_allowed':False}; v['boundary_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
if __name__=='__main__': OUT.write_text(json.dumps(build(),indent=2)+'\n',encoding='utf-8'); print(json.dumps(build(),indent=2))

