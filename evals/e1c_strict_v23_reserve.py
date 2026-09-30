from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT
OUT=ROOT/'data/e1c_strict_v23_canary_manifest.json';SALT='e1c-strict-v23-independent-canary'
def freeze(rows,source_revision):
 p=json.loads((ROOT/'data/e1c_strict_v23_prereg.json').read_text());b=json.loads((ROOT/'data/e1c_strict_v20_selection_boundary.json').read_text());blocked=set(b['explicit_prior_canary_exclusions'])|{'sympy__sympy-21586','pvlib__pvlib-python-1026','pydata__xarray-2905'};ranked=[]
 for x in rows:
  if isinstance(x,dict) and x.get('instance_id') not in blocked:ranked.append((hashlib.sha256(f'{SALT}|{x["instance_id"]}'.encode()).hexdigest(),{'instance_id':x['instance_id'],'task_yaml_path':x.get('task_yaml_path'),'task_yaml_blob_sha':x.get('task_yaml_blob_sha')}))
 ranked.sort();sel=[];seen=set()
 for _,x in ranked:
  if x['instance_id'] not in seen:seen.add(x['instance_id']);sel.append(x)
  if len(sel)==3:break
 if len(sel)!=3:raise ValueError('need 3 untouched identities')
 v={'schema':'e1c-strict-v23-external-canary-reserve-v1','source':'frozen_swebench_git_tree_names_only','source_revision':source_revision,'identity_frozen_before_statement_materialization':True,'selection_salt':SALT,'mechanism_prereg_sha256':p['prereg_sha256'],'tasks':sel,'provider_calls':0,'task_content_inspected':False};encoded=json.dumps(v,indent=2)+'\n';OUT.write_text(encoded);return {'instance_ids':[x['instance_id'] for x in sel],'manifest_sha256':hashlib.sha256(encoded.encode()).hexdigest()}
if __name__=='__main__':
 src=json.loads((ROOT/'data/e1c_strict_v20_clean_metadata_pool.json').read_text());print(json.dumps(freeze(src['tasks'],src['source_revision']),indent=2))
