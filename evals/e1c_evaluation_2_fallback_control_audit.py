"""One-shot zero-provider audit of frozen V4 DEV A candidates; no Gold reads."""

from __future__ import annotations

import hashlib
import json

from evals.e1c_evaluation_2_container_health import is_transport_failure, require_engine
from evals.e1c_evaluation_2_counterfactual_fast_dev import verify_workspace
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_fallback_control import derive_control
from evals.e1c_evaluation_2_issue_input import SOURCE
from evals.e1c_evaluation_2_probe import execute_candidate, verified_local_image

PREVIOUS = ROOT / ".codex/e1c/evaluation_2/controller-generation-old-dev-v4"
OUT = ROOT / ".codex/e1c/evaluation_2/fallback-control-zero-dev-v1"
PINNED = {"freeze.json": "40cd232e56945628f8c1f6e0946d3b1f659bb574081c252e1aaa51029c3ef2fb",
          "state.json": "14ad5c4f45a553c0f48a716cd6a59cbf9977dfe8e416308737724ece0393e796",
          "provider_calls.jsonl": "41f25f5d82b5f4fca1aeea682ac77b6ee57364bb981e276b5666b872a1886fd0"}


def audit():
    if OUT.exists():
        raise FileExistsError("one-shot namespace already exists; preserve it, do not retry")
    if any(_sha(PREVIOUS / name) != digest for name, digest in PINNED.items()):
        raise ValueError("previous frozen V4 records differ")
    freeze = json.loads((PREVIOUS / "freeze.json").read_bytes())
    tasks = freeze["tasks"]
    if freeze["fixed_denominator"] != 12 or len(tasks) != 9:
        raise ValueError("expected fixed DEV12 and its nine admitted tasks")
    rows, materials = [], {}
    for task in tasks:
        iid = task["instance_id"]
        path = PREVIOUS / "inputs" / f"{iid}.json"
        frozen = json.loads(path.read_bytes())
        if _sha(path) != task["input_sha256"]:
            raise ValueError("previous input identity differs")
        workspace = SOURCE / iid
        verify_workspace(frozen, workspace)
        image = verified_local_image(iid)
        if image != task["image_id"]:
            raise ValueError("previous image identity differs")
        candidate_path = PREVIOUS / iid / "A/candidate.json"
        material = {"input_file_sha256": _sha(path), "production_sha256": {
            row["path"]: row["source_sha256"] for row in frozen["windows"]}}
        if candidate_path.exists():
            material["candidate_sha256"] = _sha(candidate_path)
            candidate = json.loads(candidate_path.read_bytes())
            if candidate["input_sha256"] != frozen["input_sha256"]:
                raise ValueError("candidate input identity differs")
            if hashlib.sha256(candidate["source"].encode()).hexdigest() != candidate["probe_sha256"]:
                raise ValueError("candidate source identity differs")
            control, proof = derive_control(candidate, frozen, workspace)
        else:
            control, proof = None, {"compiled": False, "status": "no_A_candidate"}
        materials[iid] = material
        rows.append((iid, task, frozen, image, control, proof))
    require_engine(tuple(row[3] for row in rows))
    modules = ("fallback_control", "fallback_control_audit", "counterfactual_contract", "probe", "source_contract")
    _save(OUT / "freeze.json", {"schema": "e1c2-fallback-control-zero-dev-freeze-v1",
                               "previous_records": PINNED, "fixed_denominator": 12,
                               "materials": materials, "method_sha256": {
                                   name: _sha(ROOT / f"evals/e1c_evaluation_2_{name}.py") for name in modules},
                               "provider_calls": 0, "gold_reads": 0, "new_model_result": False})
    result = []
    for iid, task, frozen, image, control, proof in rows:
        row = {"instance_id": iid, "proof": proof, "status": proof["status"]}
        if control:
            require_engine((image,))
            _save(OUT / iid / "control.json", control)
            executions = []
            for repetition in (1, 2):
                execution = execute_candidate(control, image, frozen["base_commit"], OUT / iid / f"control{repetition}",
                                              timeout_seconds=120,
                                              missing_optional_import=task["environment"]["missing_optional_import"])
                _save(OUT / iid / f"control{repetition}_execution.json", execution)
                if is_transport_failure(execution) or any(
                    run["returncode"] == 90 or run["timed_out"] for run in execution["runs"]
                ):
                    raise RuntimeError("infrastructure/source identity failure; not fixture evidence")
                executions.append(execution)
            row["control_pass"] = all(len(e["runs"]) == 1 and e["runs"][0]["returncode"] == 0 for e in executions)
            row["control_returncodes"] = [[r["returncode"] for r in e["runs"]] for e in executions]
            row["status"] = "control_pass_semantics_unverified" if row["control_pass"] else "control_failed_fixture_unproven"
        _save(OUT / iid / "audit.json", row)
        result.append(row)
        print(f"{iid}: {row['status']}", flush=True)
    value = {"schema": "e1c2-fallback-control-zero-dev-result-v1", "fixed_denominator": 12,
             "audited_tasks": len(tasks), "A_candidates": sum("candidate_sha256" in m for m in materials.values()),
             "compiled_controls": sum(r["proof"]["compiled"] for r in result),
             "constant_oracle_rejected": sum(r["status"] == "constant_oracle_rejected" for r in result),
             "control_failed": sum(r["status"] == "control_failed_fixture_unproven" for r in result),
             "provider_calls": 0, "gold_reads": 0, "trusted_reproducer_count": 0,
             "new_reproduction_score": False, "rows": result,
             "previous_records_unchanged": all(_sha(PREVIOUS / n) == d for n, d in PINNED.items())}
    if not value["previous_records_unchanged"]:
        raise ValueError("previous frozen records changed during audit")
    _save(OUT / "result.json", value)
    return value


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False))
