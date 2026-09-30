from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT
from evals.e1c_strict_v6_runtime import build_bundle
from evals.e1c_strict_v8_postfreeze import materialize_source_bounded
from evals.e1c_strict_v23_probe import candidate_plan
MANIFEST=ROOT/'data/e1c_strict_v23_canary_manifest.json';OUT=ROOT/'data/e1c_strict_v23_postfreeze_assessment.json';ROOT_OUT=ROOT/'.codex/e1c/strict-v23/postfreeze-v1'
def run():
 m=json.loads(MANIFEST.read_text());rows=[]
 for t in m['tasks']:
  root=ROOT_OUT/t['instance_id'];sp=root/'problem_statement.md';s=sp.read_text(encoding='utf-8');assert hashlib.sha256(sp.read_bytes()).hexdigest()==t['statement_sha256'];src=materialize_source_bounded(t,root/'source')
  if not src['ready']:rows.append({'instance_id':t['instance_id'],'source':src,'projection_status':'source_incomplete','candidate_count':0,'executable_candidate_count':0,'consensus_path_count':0});continue
  try:
   b=build_bundle(statement=s,workspace=root/'source',base_commit=t['base_commit'],forbidden_values=(t['instance_id'],t['image']));p=candidate_plan(b['issue'],b['localization'],source_root=root/'source');rows.append({'instance_id':t['instance_id'],'statement_sha256':t['statement_sha256'],'source':src,'projection_status':'supported','candidate_count':p['candidate_count'],'executable_candidate_count':p['executable_candidate_count'],'consensus_path_count':p['consensus_path_count'],'plan':p})
  except Exception as e:rows.append({'instance_id':t['instance_id'],'source':src,'projection_status':'unsupported','error':f'{type(e).__name__}: {e}','candidate_count':0,'executable_candidate_count':0,'consensus_path_count':0})
 ready=sum(bool(x['source'].get('ready')) for x in rows);supported=sum(x['projection_status']=='supported' for x in rows);exe=sum(x['executable_candidate_count']>0 for x in rows);cons=sum(x['consensus_path_count']>0 for x in rows);gate=ready==supported==3 and exe>=2
 v={'schema':'e1c-strict-v23-postfreeze-assessment-v1','provider_calls':0,'live_model_run':False,'mechanism_prereg_sha256':m['mechanism_prereg_sha256'],'source_ready_count':ready,'projection_supported_count':supported,'candidate_task_count':sum(x['candidate_count']>0 for x in rows),'executable_candidate_task_count':exe,'consensus_candidate_task_count':cons,'minimum_executable_candidate_tasks':2,'candidate_gate_passed':gate,'official_image_acquisition_allowed':gate,'rows':rows};v['summary_sha256']=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest();OUT.write_text(json.dumps(v,indent=2)+'\n');return v
if __name__=='__main__':
 v=run();print(json.dumps({k:v[k] for k in ['source_ready_count','projection_supported_count','candidate_task_count','executable_candidate_task_count','consensus_candidate_task_count','candidate_gate_passed','summary_sha256']},indent=2))
