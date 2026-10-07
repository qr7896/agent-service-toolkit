"""Zero-provider OLD DEV cache study of an execution-bound setup frontier.

Replay prior actions chronologically, not fresh feedback-conditioned generation.
Never choose by Gold, alter an oracle, invent a control or change the target AST.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import re
import shutil
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from langchain_core.messages import AIMessage

from evals import e1c_evaluation_2_ready_runtime_dev as ready
from evals.e1c_evaluation_2_container_health import is_transport_failure, require_engine
from evals.e1c_evaluation_2_contract_recovery import tree_sha
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_evaluation_2_source_contract import rephase_setup

SOURCE = ready.OUT
OUT = ROOT / ".codex/e1c/evaluation_2/runtime-frontier-zero-reference-v1"
PROTOCOL = ROOT / "docs/research/E1C2_RUNTIME_FRONTIER_ZERO_PROTOCOL_2026-10-07.md"
MODULES = (*ready.MODULES, "evals/e1c_evaluation_2_runtime_frontier_zero.py")
_configured, _execute = ready.configured, ready.execute_probe


def shift_from_control(payload, control, executions):
    proof = {"schema": "e1c2-execution-bound-setup-frontier-v1", "compiled": False,
             "target_program_changed": False, "oracle_changed": False, "untrusted_trace_not_semantic_proof": True}
    digest = hashlib.sha256(control["source"].encode()).hexdigest()
    prefix = payload["setup_source"].rstrip() + "\n"
    if control["probe_sha256"] != digest or not control["source"].startswith(prefix):
        raise ValueError("control is not bound to the phased setup program")
    if len(executions) != 2:
        raise ValueError("two failed normal controls required")
    lines = []
    for execution in executions:
        if execution["probe_sha256"] != digest or is_transport_failure(execution):
            raise ValueError("control trace binding or infrastructure differs")
        runs = execution.get("runs", [])
        if len(runs) != 1 or runs[0].get("timed_out") or runs[0].get("returncode") in {None, 0, 90, 125, 126, 127}:
            return payload, proof
        frames = re.findall(r'File "/e1c2_probe\.py", line (\d+), in <module>', runs[0].get("log_tail", ""))
        if not frames:
            return payload, proof
        lines.append(int(frames[-1]))
    if lines[0] != lines[1]:
        return payload, proof
    setup = ast.parse(payload["setup_source"])
    statement = next((n for n in setup.body if n.lineno <= lines[0] <= (n.end_lineno or n.lineno)), None)
    if not isinstance(statement, ast.Assign) or not isinstance(statement.value, ast.Call):
        return payload, proof
    suffix = [n for n in setup.body if n.lineno >= statement.lineno]
    bindings = {n.id for s in suffix for n in ast.walk(s) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))}
    control_loads = {n.id for n in ast.walk(ast.parse(payload["control_action"])) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    if bindings & control_loads:
        return payload, {**proof, "status": "normal_control_depends_on_moved_bindings"}
    source_lines = payload["setup_source"].splitlines(keepends=True)
    cut = statement.lineno - 1
    transformed = {**payload, "setup_source": "".join(source_lines[:cut]),
                   "target_action": "".join(source_lines[cut:]).rstrip() + "\n" + payload["target_action"]}
    before = ast.parse(payload["setup_source"] + "\n" + payload["target_action"])
    after = ast.parse(transformed["setup_source"] + "\n" + transformed["target_action"])
    if tree_sha(before) != tree_sha(after) or any(transformed[k] != payload[k] for k in payload if k not in {"setup_source", "target_action"}):
        raise ValueError("runtime frontier changed complete target, control or expected behavior")
    proof.update({"compiled": True, "generated_setup_line": statement.lineno, "statement_ast_sha256": tree_sha(statement),
                  "complete_target_program_ast_sha256": tree_sha(before), "control_probe_sha256": digest,
                  "control_free_names_disjoint_from_moved_bindings": True,
                  "alias_global_state_independence_proven": False})
    return transformed, proof


def execute_probe(payload, frozen, workspace, image, root, environment, locked=None):
    feedback, oracle, candidate, execution = _execute(payload, frozen, workspace, image, root, environment, locked)
    if feedback["status"] != "control_failed":
        return feedback, oracle, candidate, execution
    canonical = json.loads((root / "compiler.json").read_bytes())["canonical_contract"]
    phased, _ = rephase_setup(canonical, frozen, workspace)
    control = json.loads((root / "control_candidate.json").read_bytes())
    controls = [json.loads((root / f"control-{n}.json").read_bytes()) for n in (1, 2)]
    transformed, proof = shift_from_control(phased, control, controls)
    _save(root / "runtime-frontier.json", proof)
    if not proof["compiled"]:
        return feedback, oracle, candidate, execution
    retry = root / "frontier-validation"
    result = _execute(transformed, frozen, workspace, image, retry, environment, oracle)
    if result[2] is not None:
        _save(root / "candidate.json", result[2])
        _save(root / "execution.json", result[3])
        shutil.copytree(retry / "execution", root / "execution")
    return result


def preflight():
    records = json.loads((SOURCE / "generation-seal.json").read_bytes())
    if any(_sha(SOURCE / n) != h for n, h in records["files"].items()):
        raise ValueError("source responses/state/ledger changed")
    if json.loads((SOURCE / "state.json").read_bytes())["status"] != "completed":
        raise ValueError("sealed completed cache required")
    tasks = ready.inputs()
    require_engine(tuple(t["image_id"] for t, _, _ in tasks))
    return {"schema": "e1c2-runtime-frontier-zero-reference-v1", "tasks": [t for t, _, _ in tasks],
            "fixed_denominator": 12, "admitted_denominator": 9, "screen_denominator": 4, "full_admitted_DEV_run": False,
            "provider_calls": 0, "cached_not_new_generation": True, "feedback_conditioned_model_replay": False,
            "source_records": {n: _sha(SOURCE / n) for n in ("freeze.json", "state.json", "provider_calls.jsonl", "generation-seal.json")},
            "method_sha256": {n: _sha(ROOT / n) for n in MODULES}, "protocol_sha256": _sha(PROTOCOL)}


@contextmanager
def configured():
    with ExitStack() as stack:
        stack.enter_context(patch.object(ready, "OUT", OUT))
        stack.enter_context(patch.object(ready, "execute_probe", execute_probe))
        stack.enter_context(patch.object(ready, "preflight", preflight))
        stack.enter_context(_configured())
        yield


async def run():
    if OUT.exists():
        raise FileExistsError("zero cache study already started")
    _save(OUT / "freeze.json", preflight())
    state = {"status": "running", "provider_calls": 0, "fixed_denominator": 12, "screen_denominator": 4,
             "rows": [], "trusted_reproducer_count": 0, "cached_not_new_generation": True}
    _save(OUT / "state.json", state)
    with configured():
        for task, initial, workspace in ready.inputs():
            iid = task["instance_id"]

            async def invoke(msgs, turn, iid=iid):
                path = SOURCE / iid / f"turn-{turn}" / "response.json"
                if not path.is_file():
                    raise ProviderCacheMissing
                prior_input = json.loads((path.parent / "input.json").read_bytes())
                current_input = json.loads((OUT / iid / f"turn-{turn}" / "input.json").read_bytes())
                if prior_input != current_input:
                    raise ValueError("cached production input differs; no substitute response allowed")
                cached = json.loads(path.read_bytes())
                _save(OUT / iid / f"turn-{turn}" / "cache-source.json", {"response_sha256": _sha(path), "upstream_usage": cached["usage"], "new_provider_calls": 0})
                return AIMessage(content=cached["raw"], response_metadata={"finish_reason": cached["finish_reason"]},
                                 usage_metadata={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})

            try:
                row = await ready.run_task(initial, workspace, task["image_id"], OUT / iid, task["environment"], invoke)
            except ProviderCacheMissing:
                row = {"status": "upstream_cache_missing_no_provider_call"}
            state["rows"].append({"instance_id": iid, **row})
            (OUT / "state.json").write_text(input_json(state), encoding="utf-8")
            print(input_json({"instance_id": iid, "status": row["status"]}), flush=True)
        state["status"] = "completed"
        (OUT / "state.json").write_text(input_json(state), encoding="utf-8")
        ready.compiled.base.seal()
    return state


class ProviderCacheMissing(Exception):
    pass


def grade():
    with configured():
        return ready.compiled.grade()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "gold"))
    args = parser.parse_args()
    print(input_json(asyncio.run(run()) if args.command == "run" else grade()), flush=True)
