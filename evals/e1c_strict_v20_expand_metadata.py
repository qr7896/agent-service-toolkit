from __future__ import annotations
import hashlib,json,re
from evals.e1c_admission import ROOT
TREE=ROOT/'.codex/e1c_swebench_tree.json'; OUT=ROOT/'data/e1c_strict_v20_clean_metadata_pool.json'
def build():
 tree=json.loads(TREE.read_text()); b=json.loads((ROOT/'data/e1c_strict_v20_selection_boundary.json').read_text()); assert tree['sha']==b['task_repo_revision'] and tree['truncated'] is False
 blocked=set(b['explicit_prior_canary_exclusions']); rows=[]
 for x in tree['tree']:
  m=re.fullmatch(r'tasks/([^/]+)/task\.yaml',x.get('path',''))
  if x.get('type')=='blob' and m and m.group(1) not in blocked: rows.append({'instance_id':m.group(1),'task_yaml_path':x['path'],'task_yaml_blob_sha':x['sha'],'task_yaml_size':x.get('size')})
 rows.sort(key=lambda x:x['instance_id']); v={'schema':'e1c-strict-v20-clean-metadata-pool-v1','source':'frozen_swebench_git_tree_names_only','source_revision':tree['sha'],'tree_truncated':False,'task_content_inspected':False,'outcome_inspected':False,'provider_calls':0,'effective_exclusion_count':len(blocked),'clean_identity_count':len(rows),'tasks':rows};v['pool_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();OUT.write_text(json.dumps(v,indent=2)+'\n');return v
if __name__=='__main__':
 v=build();print(json.dumps({k:v[k] for k in ('source_revision','effective_exclusion_count','clean_identity_count','pool_sha256')},indent=2))
