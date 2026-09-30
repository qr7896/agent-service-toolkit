"""Strict-v9 development candidate plan; no task-specific rules."""
from __future__ import annotations
import hashlib,json
from evals.e1c_strict_v8_probe import candidate_plan as v8_candidate_plan
from evals.e1c_strict_v9_observable import observable_contracts

def candidate_plan(projected_issue: str, localization: dict, *, limit: int=10) -> dict:
    base=v8_candidate_plan(projected_issue,localization,limit=limit)
    rows=list(base["candidates"])
    rows.extend({"execution_ready":True,"origin":w["origin"],"witness":w} for w in observable_contracts(projected_issue,localization))
    dedup=[]; seen=set()
    for row in rows:
        witness=row.get("witness") or row.get("freeze",{}).get("witness") or {}; key=witness.get("witness_sha256") or row.get("row_sha256")
        if key in seen: continue
        seen.add(key); dedup.append(row)
        if len(dedup)>=limit: break
    executable=sum(bool(r.get("execution_ready")) for r in dedup)
    value={"schema":"e1c-strict-v9-candidate-plan-v1","candidate_count":len(dedup),"executable_candidate_count":executable,"status":"candidate_executable_witnesses" if executable else "no_executable_reproducer","candidates":dedup,"provider_calls":0,"benchmark_assertion_used":False}
    value["plan_sha256"]=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest(); return value
