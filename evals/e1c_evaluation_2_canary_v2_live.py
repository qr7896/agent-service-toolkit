"""One-shot second canary using the DEV-validated v4 Flash mechanism."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from langchain_core.messages import HumanMessage

from agents.model_budget import _prompt_text
from agents.model_router import estimate_tokens
from evals import e1c_evaluation_2_unified_dev_v4 as flash
from evals.e1c_evaluation_2_canary_v2_select import FREEZE as METHOD_FREEZE
from evals.e1c_evaluation_2_canary_v2_select import IDENTITY, method
from evals.e1c_evaluation_2_canary_v2_stage import GRADER, OUT, PUBLIC, SOURCE, bind
from evals.e1c_evaluation_2_canary_v2_stage import materialize as stage_materialize
from evals.e1c_evaluation_2_dev_pilot import _sha
from evals.e1c_evaluation_2_unified_dev_v4 import base

bind()
RUN_ID = "e1c2-independent-canary-v2-flash"
base.RUN_ID = RUN_ID
base.OUT = OUT / "live"
base.FREEZE = base.OUT / "freeze.json"
base.LEDGER = base.OUT / "provider_calls.jsonl"
base.IDENTITY, base.ADMISSION = IDENTITY, GRADER
base.ISSUE, base.SOURCE = PUBLIC, SOURCE
base.MODEL = "deepseek-flash"
base.MAX_OUTPUT_TOKENS = 2600
base.TASK_TOKEN_CAP = 14_000
base.BATCH_TOKEN_CAP = 42_000
base.verified_local_image = stage_materialize.verified_image


def _cohort() -> list[dict]:
    locked = json.loads(METHOD_FREEZE.read_bytes())
    if locked != method() or locked["model"] != base.MODEL or locked["batch_provider_token_cap"] != base.BATCH_TOKEN_CAP:
        raise ValueError("preselection method or provider budget changed")
    identity = json.loads(IDENTITY.read_bytes())
    if identity.get("method_freeze_sha256") != _sha(METHOD_FREEZE) or len(identity.get("tasks", [])) != 3:
        raise ValueError("fixed second-canary identity changed")
    result = []
    for task in stage_materialize.rows():
        iid = task["instance_id"]
        phases = [GRADER / iid / f"{phase}.json" for phase in ("base", "gold")]
        admissions = [json.loads(path.read_bytes()) for path in phases]
        if any(row.get("instance_id") != iid or row.get("provider_calls") != 0 for row in admissions):
            raise ValueError("grader-only admission identity changed")
        record = {"instance_id": iid, "base_pass": admissions[0]["phase_pass"], "gold_pass": admissions[1]["phase_pass"]}
        if not all(row["phase_pass"] for row in admissions):
            record["status"] = "official_admission_failed_fixed_denominator"
            result.append(record)
            continue
        frozen_path = PUBLIC / iid / "frozen_input_v4.json"
        frozen = json.loads(frozen_path.read_bytes())
        if frozen.get("status") != "ready_for_generation" or frozen.get("base_commit") != task["base_commit"]:
            record["status"] = "no_issue_only_production_window"
            result.append(record)
            continue
        workspace = SOURCE / iid
        head = subprocess.check_output(["git", "-C", str(workspace), "rev-parse", "HEAD"], text=True, timeout=30).strip()
        status = subprocess.check_output(["git", "-C", str(workspace), "status", "--porcelain", "--untracked-files=all"], text=True, timeout=90).strip()
        if head != task["base_commit"] or status:
            raise ValueError("canary production workspace changed after exact-base materialization")
        stage_materialize.verified_image(iid)
        route, source = base.route(frozen)
        model_prompt = flash.prompt(frozen) if source is None else None
        reserve = math.ceil(estimate_tokens(_prompt_text([HumanMessage(content=model_prompt)])) * 1.4) + base.MAX_OUTPUT_TOKENS if model_prompt else 0
        record.update({"input_sha256": _sha(frozen_path), "method": route, "estimated_reserve": reserve})
        record["status"] = "budget_blocked_fixed_denominator" if reserve > base.TASK_TOKEN_CAP else "eligible"
        result.append(record)
    return result


def _admitted_inputs() -> list[tuple[str, dict, Path]]:
    return [
        (row["instance_id"], json.loads(path.read_bytes()), path)
        for row in _cohort() if row["status"] == "eligible"
        for path in [PUBLIC / row["instance_id"] / "frozen_input_v4.json"]
    ]


base._admitted_inputs = _admitted_inputs


def preflight() -> dict:
    cohort = _cohort()
    frozen = flash.preflight()
    frozen.update({
        "schema": "e1c2-independent-canary-v2-flash-freeze",
        "selection": "fixed_three_preregistered_metadata_only_no_replacement",
        "fixed_denominator": 3, "cohort": cohort,
        "method_freeze_sha256": _sha(METHOD_FREEZE), "canary_identity_sha256": _sha(IDENTITY),
        "adapter_sha256": _sha(Path(__file__)), "acquire_identity_sha256": _sha(IDENTITY),
        "elastic_token_ceiling": 42_000,
    })
    if frozen["max_provider_calls"] > 3 or frozen["total_reserve"] > 42_000:
        raise ValueError("canary model reserve exceeds preregistered batch budget")
    return frozen


base.preflight = preflight


if __name__ == "__main__":
    base.main()
