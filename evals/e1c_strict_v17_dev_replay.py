from __future__ import annotations
import hashlib,json
from pathlib import Path
from evals.e1c_admission import ROOT
from evals.e1c_strict_v17_probe import candidate_plan
OUT=ROOT/'data/e1c_strict_v17_dev_replay.json'
def run():
 old=json.loads((ROOT/'data/e1c_strict_v16_dev_replay.json').read_text()); cache=json.loads((ROOT/'data/e1c_strict_v9_exposed_v7_projection_cache.json').read_text())['rows']; rows=[]
 for r in old['rows']:
  c=cache.get(r['instance_id'])
  if c is None: rows.append(r); continue
  p=candidate_plan(c['issue'],c['localization']); rows.append({'lineage':r['lineage'],'instance_id':r['instance_id'],'candidate_count':p['candidate_count'],'executable_candidate_count':p['executable_candidate_count'],'candidate_origins':[x.get('origin') for x in p['candidates']],'consensus_path_count':p['consensus_path_count'],'consensus_paths':p['consensus_paths']})
 v={'schema':'e1c-strict-v17-development-replay-v1','provider_calls':0,'live_model_run':False,'independent_evidence':False,'task_count':6,'candidate_task_count':sum(x['candidate_count']>0 for x in rows),'executable_candidate_task_count':sum(x['executable_candidate_count']>0 for x in rows),'consensus_candidate_task_count':sum(x['consensus_path_count']>0 for x in rows),'rows':rows}; v['summary_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); OUT.write_text(json.dumps(v,indent=2)+'\n'); return v
if __name__=='__main__': print(json.dumps(run(),indent=2))
