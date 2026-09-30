"""Development-only strict-v9 replay on exposed v6/v7 material."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from evals.e1c_admission import ROOT
from evals.e1c_strict_v9_probe import candidate_plan

SOURCES=[("strict_v6_exposed",ROOT/"data/e1c_strict_v6_postfreeze_assessment.json",ROOT/"data/e1c_strict_v6_canary_manifest.json"),("strict_v7_exposed",ROOT/"data/e1c_strict_v7_postfreeze_assessment.json",ROOT/"data/e1c_strict_v7_canary_manifest.json")]
OUT=ROOT/"data/e1c_strict_v9_dev_replay.json"

def build():
 rows=[]
 for lineage,assessment_path,manifest_path in SOURCES:
  assessment=json.loads(assessment_path.read_text(encoding="utf-8")); manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
  tasks={t["instance_id"]:t for t in manifest["tasks"]}
  for old in assessment.get("rows",[]):
   task=tasks[old["instance_id"]]; statement_path=ROOT/old["statement_path"]
   bundle=old.get("bundle") or {}
   issue=bundle.get("issue")
   localization=bundle.get("localization")
   if not isinstance(issue,str) or not isinstance(localization,dict):
    # Reuse the already-saved v8 development projection for exposed v7 rows.
    cache_path=ROOT/"data/e1c_strict_v9_exposed_v7_projection_cache.json"
    cache=json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {"rows":{}}
    cached=cache.get("rows",{}).get(old["instance_id"],{})
    issue=cached.get("issue") or statement_path.read_text(encoding="utf-8")
    localization=cached.get("localization") or {"candidates":[]}
   plan=candidate_plan(issue,localization)
   rows.append({"lineage":lineage,"instance_id":old["instance_id"],"candidate_count":plan["candidate_count"],"executable_candidate_count":plan["executable_candidate_count"],"candidate_origins":[r.get("origin") for r in plan["candidates"]],"plan":plan})
 value={"schema":"e1c-strict-v9-development-replay-v1","provider_calls":0,"live_model_run":False,"independent_evidence":False,"may_open_c5":False,"may_open_dev30":False,"may_open_fresh30":False,"task_count":len(rows),"candidate_task_count":sum(r["candidate_count"]>0 for r in rows),"executable_candidate_task_count":sum(r["executable_candidate_count"]>0 for r in rows),"rows":rows}
 value["summary_sha256"]=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest(); return value

def main():
 value=build(); OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({k:value[k] for k in ["task_count","candidate_task_count","executable_candidate_task_count","provider_calls","summary_sha256"]},indent=2))
if __name__=="__main__": main()
