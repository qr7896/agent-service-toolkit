from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT
from evals.e1c_strict_v6_runtime import build_bundle
from evals.e1c_strict_v8_postfreeze import fetch_statement_bounded,materialize_source_bounded
from evals.e1c_strict_v13_probe import candidate_plan
MANIFEST=ROOT/'data/e1c_strict_v13_canary_manifest.json'; OUT=ROOT/'data/e1c_strict_v13_postfreeze_assessment.json'; ROOT_OUT=ROOT/'.codex/e1c/strict-v13/postfreeze-v1'
def run():
 m=json.loads(MANIFEST.read_text(encoding='utf-8')); rows=[]
 for t in m['tasks']:
  root=ROOT_OUT/t['instance_id']; root.mkdir(parents=True,exist_ok=True); sp=root/'problem_statement.md'
  try: s,h=fetch_statement_bounded(t['instance_id'],m['source_revision'],sp); sp.write_text(s,encoding='utf-8'); src=materialize_source_bounded(t,root/'source')
  except Exception as e: rows.append({'instance_id':t['instance_id'],'source':{'ready':False},'projection_status':'transport_blocked','error':f'{type(e).__name__}: {e}','candidate_count':0,'executable_candidate_count':0}); continue
  if not src['ready']: rows.append({'instance_id':t['instance_id'],'source':src,'projection_status':'source_incomplete','candidate_count':0,'executable_candidate_count':0}); continue
  try: b=build_bundle(statement=s,workspace=root/'source',base_commit=t['base_commit'],forbidden_values=(t['instance_id'],t['image'])); p=candidate_plan(b['issue'],b['localization']); rows.append({'instance_id':t['instance_id'],'statement_sha256':h,'source':src,'projection_status':'supported','candidate_count':p['candidate_count'],'executable_candidate_count':p['executable_candidate_count'],'plan':p})
  except Exception as e: rows.append({'instance_id':t['instance_id'],'source':src,'projection_status':'unsupported','error':f'{type(e).__name__}: {e}','candidate_count':0,'executable_candidate_count':0})
 ready=sum(bool(x['source'].get('ready')) for x in rows); supported=sum(x['projection_status']=='supported' for x in rows); exe=sum(x['executable_candidate_count']>0 for x in rows); gate=ready==supported==3 and exe>=2
 v={'schema':'e1c-strict-v13-postfreeze-assessment-v1','provider_calls':0,'live_model_run':False,'source_ready_count':ready,'projection_supported_count':supported,'candidate_task_count':sum(x['candidate_count']>0 for x in rows),'executable_candidate_task_count':exe,'minimum_executable_candidate_tasks':2,'candidate_gate_passed':gate,'official_image_acquisition_allowed':gate,'rows':rows}; v['summary_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest(); OUT.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return v
if __name__=='__main__':
 v=run(); print(json.dumps({k:v[k] for k in ['source_ready_count','projection_supported_count','candidate_task_count','executable_candidate_task_count','candidate_gate_passed','summary_sha256']},indent=2))
