"""Zero-call, DEV-only audit of issue-grounded probe shape.

This is a structural guard, not a semantic oracle or a trust verdict.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json

from evals.e1c_evaluation_2 import ROOT

DEV = ROOT / ".codex/e1c/evaluation_2/e1c2-unified-dev-v4-flash"
ISSUES = ROOT / ".codex/e1c/evaluation_2/issue-only"


def audit_probe(frozen: dict, candidate: dict) -> dict:
    """Flag unsupported probe shapes without inspecting tests or Gold."""
    issue, source, quote = frozen["issue"], candidate["source"], candidate["issue_quote"]
    if not isinstance(quote, str) or len(quote) < 8 or quote not in issue:
        raise ValueError("probe quote is not a public-issue span")
    if candidate["input_sha256"] != frozen["input_sha256"]:
        raise ValueError("candidate is not bound to the frozen public input")
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != candidate["probe_sha256"]:
        raise ValueError("candidate source digest differs")
    tree = ast.parse(source)
    assertions = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    if len(assertions) != 1 or not tree.body or tree.body[-1] is not assertions[0]:
        return {"shape": "unsupported_assertion", "semantic_status": "unverified"}
    assertion = assertions[0].test
    if isinstance(assertion, ast.Name):
        if any(isinstance(node, (ast.Try, ast.TryStar)) for node in ast.walk(tree)):
            return {"shape": "exception_swallowed", "semantic_status": "unverified"}
        if len(tree.body) < 3:
            return {"shape": "unguarded_completion", "semantic_status": "unverified"}
        completed, action = tree.body[-2], tree.body[-3]
        assigned_true = (
            isinstance(completed, ast.Assign)
            and len(completed.targets) == 1
            and isinstance(completed.targets[0], ast.Name)
            and completed.targets[0].id == assertion.id
            and isinstance(completed.value, ast.Constant)
            and completed.value.value is True
        )
        called = (
            isinstance(action, ast.Expr) and isinstance(action.value, ast.Call)
            or isinstance(action, ast.Assign) and isinstance(action.value, ast.Call)
        )
        shape = "completion_after_call" if assigned_true and called else "unguarded_completion"
    elif isinstance(assertion, ast.Compare):
        shape = "value_comparison"
    else:
        shape = "unsupported_assertion"
    return {"shape": shape, "semantic_status": "unverified"}


def audit_saved_dev() -> dict:
    """Read the frozen v4 DEV artifacts; do not execute a probe or provider."""
    state = json.loads((DEV / "state.json").read_text(encoding="utf-8"))
    if state.get("status") != "completed":
        raise ValueError("DEV run is not complete")
    rows = []
    for item in state["rows"]:
        iid = item["instance_id"]
        path = DEV / iid / "candidate.json"
        if not path.is_file():
            rows.append({"instance_id": iid, "shape": "no_candidate", "semantic_status": "unverified"})
            continue
        frozen = json.loads((ISSUES / iid / "frozen_input_v4.json").read_text(encoding="utf-8"))
        candidate = json.loads(path.read_text(encoding="utf-8"))
        rows.append({"instance_id": iid, **audit_probe(frozen, candidate)})
    return {"schema": "e1c2-dev-probe-shape-audit-v1", "denominator": len(state["rows"]),
            "rows": rows, "provider_calls": 0, "trusted_reproducer_count": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit-dev",))
    parser.parse_args()
    print(json.dumps(audit_saved_dev(), ensure_ascii=False, indent=2))
