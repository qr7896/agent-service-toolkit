"""Metadata-only strict-v9 selection boundary extending all sealed canaries."""
from __future__ import annotations
import hashlib,json
from evals.e1c_admission import ROOT

OUT=ROOT/"data/e1c_strict_v9_selection_boundary.json"
SALT="e1c-strict-v9-independent-canary"

def build():
 base=json.loads((ROOT/"data/e1c_strict_v8_selection_boundary.json").read_text(encoding="utf-8"))
 v8=json.loads((ROOT/"data/e1c_strict_v8_canary_manifest.json").read_text(encoding="utf-8"))
 excluded=list(dict.fromkeys(base["explicit_prior_canary_exclusions"]+[r["instance_id"] for r in v8["tasks"]]))
 value={"schema":"e1c-strict-v9-selection-boundary-v1","provider_calls":0,"task_content_inspected":False,"canary_selected":False,"mechanism_must_be_frozen_before_canary_selection":True,"selection_salt":SALT,"contamination_count":base["contamination_count"]+len(v8["tasks"]),"base_v8_boundary_sha256":hashlib.sha256((ROOT/"data/e1c_strict_v8_selection_boundary.json").read_bytes()).hexdigest(),"explicit_prior_canary_exclusions":excluded,"v8_manifest_sha256":hashlib.sha256((ROOT/"data/e1c_strict_v8_canary_manifest.json").read_bytes()).hexdigest(),"task_repo_revision":base["task_repo_revision"],"inventory_revision":base["inventory_revision"],"prior_canary_reuse_allowed":False,"outcome_conditioned_replacement_allowed":False}
 value["boundary_sha256"]=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest(); return value
def write():
 v=build(); OUT.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return v
if __name__=="__main__": print(json.dumps(write(),indent=2))
