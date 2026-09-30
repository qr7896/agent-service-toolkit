"""Post-freeze zero-provider assessment for strict-v9 independent canary."""
from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT
from evals.e1c_strict_v6_runtime import build_bundle
from evals.e1c_strict_v8_postfreeze import fetch_statement_bounded, materialize_source_bounded
from evals.e1c_strict_v9_prereg import build as build_prereg
from evals.e1c_strict_v9_probe import candidate_plan
from evals.e1c_strict_v9_selection_boundary import build as build_boundary
MANIFEST=ROOT/"data/e1c_strict_v9_canary_manifest.json"; PREREG=ROOT/"data/e1c_strict_v9_prereg.json"; BOUNDARY=ROOT/"data/e1c_strict_v9_selection_boundary.json"; ROOT_OUT=ROOT/".codex/e1c/strict-v9/postfreeze-v1"; OUT=ROOT/"data/e1c_strict_v9_postfreeze_assessment.json"
def certify_identity():
 m=json.loads(MANIFEST.read_text(encoding="utf-8")); p=json.loads(PREREG.read_text(encoding="utf-8")); b=json.loads(BOUNDARY.read_text(encoding="utf-8")); rows=m.get("tasks",[]); checks={"manifest_schema":m.get("schema")=="e1c-strict-v9-external-canary-reserve-v1","exact_task_count":len(rows)==3,"identity_frozen_before_statement":m.get("identity_frozen_before_statement_materialization") is True,"provider_calls_zero":m.get("provider_calls")==p.get("provider_calls")==0,"task_content_inspected_false":m.get("task_content_inspected") is False,"mechanism_prereg_matches":m.get("mechanism_prereg_sha256")==p.get("prereg_sha256"),"prereg_current":p==build_prereg(),"boundary_current":b==build_boundary()}; ids=[r.get("instance_id") for r in rows]; checks["unique_nonempty_ids"]=len(ids)==len(set(ids))==3 and all(ids); return {"ready":all(checks.values()),"checks":checks,"instance_ids":ids}
def run():
 cert=certify_identity();
 if not cert["ready"]: raise RuntimeError("strict_v9_identity_integrity_failed")
 m=json.loads(MANIFEST.read_text(encoding="utf-8")); rows=[]
 for task in m["tasks"]:
  iid=task["instance_id"]; root=ROOT_OUT/iid; root.mkdir(parents=True,exist_ok=True); sp=root/"problem_statement.md"; statement,sha=fetch_statement_bounded(iid,m["source_revision"],sp); sp.write_text(statement,encoding="utf-8"); source=materialize_source_bounded(task,root/"source"); plan=None; status="source_incomplete"; error=None
  if source["ready"]:
   try:
    bundle=build_bundle(statement=statement,workspace=root/"source",base_commit=task["base_commit"],forbidden_values=(iid,task["image"])); plan=candidate_plan(bundle["issue"],bundle["localization"]); status="supported"
   except Exception as exc: status="unsupported"; error=f"{type(exc).__name__}: {exc}"
  rows.append({"instance_id":iid,"statement_sha256":sha,"source":source,"projection_status":status,"projection_error":error,"candidate_count":int(plan.get("candidate_count",0)) if plan else 0,"executable_candidate_count":int(plan.get("executable_candidate_count",0)) if plan else 0,"plan":plan,"provider_calls":0})
 ready=sum(bool(r["source"]["ready"]) for r in rows); supported=sum(r["projection_status"]=="supported" for r in rows); executable=sum(r["executable_candidate_count"]>0 for r in rows); gate=ready==supported==3 and executable>=2
 v={"schema":"e1c-strict-v9-postfreeze-assessment-v1","provider_calls":0,"live_model_run":False,"identity_certificate":cert,"source_ready_count":ready,"projection_supported_count":supported,"candidate_task_count":sum(r["candidate_count"]>0 for r in rows),"executable_candidate_task_count":executable,"minimum_executable_candidate_tasks":2,"candidate_gate_passed":gate,"image_pull_allowed_by_candidate_gate":gate,"official_admission_allowed_by_candidate_gate":gate,"live_allowed":False,"reason":"ready_for_image_and_official_admission" if gate else "seal_pre_live_insufficient_executable_reproducers","rows":rows}; v["summary_sha256"]=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest(); OUT.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return v
if __name__=="__main__":
 r=run(); print(json.dumps({k:r[k] for k in ("source_ready_count","projection_supported_count","candidate_task_count","executable_candidate_task_count","candidate_gate_passed","reason","provider_calls","summary_sha256")},indent=2))
