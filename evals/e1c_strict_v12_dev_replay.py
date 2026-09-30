from __future__ import annotations
import hashlib,json
from pathlib import Path
from evals.e1c_admission import ROOT
from evals.e1c_strict_v12_probe import candidate_plan
OUT=ROOT/'data/e1c_strict_v12_dev_replay.json'
def build():
 cache=json.loads((ROOT/'data/e1c_strict_v9_exposed_v7_projection_cache.json').read_text())['rows']; rows=[]
 for fn,lineage in [('data/e1c_strict_v6_postfreeze_assessment.json','strict_v6_exposed'),('data/e1c_strict_v7_postfreeze_assessment.json','strict_v7_exposed')]:
  for old in json.loads((ROOT/fn).read_text()).get('rows',[]):
   b=old.get('bundle') or {}; issue=b.get('issue'); loc=b.get('localization')
   if not isinstance(issue,str) or not isinstance(loc,dict):
    c=cache.get(old['instance_id'],{}); issue=c.get('issue') or (ROOT/old['statement_path']).read_text(encoding='utf-8'); loc=c.get('localization') or {'candidates':[]}
   p=candidate_plan(issue,loc); rows.append({'lineage':lineage,'instance_id':old['instance_id'],'candidate_count':p['candidate_count'],'executable_candidate_count':p['executable_candidate_count'],'candidate_origins':[x.get('origin') for x in p['candidates']]})
 v={'schema':'e1c-strict-v12-development-replay-v1','provider_calls':0,'live_model_run':False,'independent_evidence':False,'task_count':len(rows),'candidate_task_count':sum(x['candidate_count']>0 for x in rows),'executable_candidate_task_count':sum(x['executable_candidate_count']>0 for x in rows),'rows':rows}; v['summary_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); return v
if __name__=='__main__':
 v=build(); OUT.write_text(json.dumps(v,indent=2)+'\n'); print(json.dumps({k:v[k] for k in ['task_count','candidate_task_count','executable_candidate_task_count','provider_calls','summary_sha256']},indent=2)); [print(x['instance_id'],x['executable_candidate_count'],x['candidate_origins']) for x in v['rows']]
