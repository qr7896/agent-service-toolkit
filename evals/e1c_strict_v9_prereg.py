"""Freeze strict-v9 mechanism before any new independent canary selection."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from evals.e1c_admission import ROOT

OUT=ROOT/"data/e1c_strict_v9_prereg.json"; BOUNDARY=ROOT/"data/e1c_strict_v9_selection_boundary.json"
FILES=("e1c_strict_v5_boundary.py","e1c_strict_v6_probe.py","e1c_strict_v7_witness_ir.py","e1c_strict_v7_probe.py","e1c_strict_v7_runner.py","e1c_strict_v8_source_contract.py","e1c_strict_v8_probe.py","e1c_strict_v9_observable.py","e1c_strict_v9_probe.py")
def ident(name):
 p=ROOT/"evals"/name; raw=p.read_bytes(); return {"path":p.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"size_bytes":len(raw)}
def build():
 raw=BOUNDARY.read_bytes(); b=json.loads(raw); assert b["canary_selected"] is False
 files=[ident(x) for x in FILES]
 v={"schema":"e1c-strict-v9-reproducer-prereg-v1","provider_calls":0,"live_model_run":False,"canary_selected_at_freeze":False,"prior_canary_reuse_allowed":False,"selection_salt":"e1c-strict-v9-independent-canary","canary_task_count":3,"minimum_candidate_reproducer_tasks":2,"minimum_trusted_reproducers":2,"live_allowed_before_admission":False,"mechanism_files":files,"mechanism_sha256":hashlib.sha256(json.dumps(files,sort_keys=True,separators=(",",":")).encode()).hexdigest(),"selection_boundary_sha256":hashlib.sha256(raw).hexdigest(),"currently_executable_kinds":["call_result","python_scenario","source_usage","source_effect","semantic_postcondition","nonfailure_postcondition"],"unsupported_or_unresolved_behavior":"fail_closed_no_executable_reproducer","development_replay_is_independent_evidence":False}
 v["prereg_sha256"]=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest(); return v
def write():
 v=build(); OUT.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return v
if __name__=="__main__": print(json.dumps(write(),indent=2))
