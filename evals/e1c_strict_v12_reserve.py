from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT
OUT=ROOT/'data/e1c_strict_v12_canary_manifest.json'; SALT='e1c-strict-v12-independent-canary'
def freeze(rows,source_revision):
 p=json.loads((ROOT/'data/e1c_strict_v12_prereg.json').read_text(encoding='utf-8')); b=json.loads((ROOT/'data/e1c_strict_v12_selection_boundary.json').read_text(encoding='utf-8')); blocked=set(b['explicit_prior_canary_exclusions']); ranked=[]
 for x in rows:
  if isinstance(x,dict) and x.get('instance_id') not in blocked and all(isinstance(x.get(k),str) and x[k] for k in ('instance_id','repo','base_commit','image')) and len(x['base_commit'])==40: ranked.append((hashlib.sha256(f"{SALT}|{x['instance_id']}".encode()).hexdigest(),{k:x[k] for k in ('instance_id','repo','base_commit','image')}))
 ranked.sort(); sel=[]; seen=set()
 for _,x in ranked:
  if x['instance_id'] not in seen: seen.add(x['instance_id']); sel.append(x)
  if len(sel)==3: break
 if len(sel)!=3: raise ValueError('need 3 untouched identities')
 v={'schema':'e1c-strict-v12-external-canary-reserve-v1','source':'official_swebench_task_repo_task_yaml','source_revision':source_revision,'identity_frozen_before_statement_materialization':True,'selection_salt':SALT,'mechanism_prereg_sha256':p['prereg_sha256'],'tasks':sel,'provider_calls':0,'task_content_inspected':False}; encoded=json.dumps(v,indent=2)+'\n'; OUT.write_text(encoded,encoding='utf-8'); return {'instance_ids':[x['instance_id'] for x in sel],'manifest_sha256':hashlib.sha256(encoded.encode()).hexdigest()}

