"""Read-only, exact-base static export chains; runtime objects remain unproven."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re

from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_evaluation_2_qualification_v3 import git_blob
from evals.e1c_strict_v5_boundary import assert_production_relative_path


def export_chain(workspace, qualified, base_commit, seen=frozenset()):
    if not re.fullmatch(r"[0-9a-f]{40}", base_commit) or not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", qualified):
        raise ValueError("exact base and qualified production reference required")
    if qualified in seen or len(seen) > 4:
        return {"status": "unknown", "reason": "export_cycle_or_depth", "chain": []}
    module, symbol = qualified.rsplit(".", 1)
    paths = []
    for prefix in ("", "src/"):
        for suffix in (".py", "/__init__.py"):
            name = assert_production_relative_path(prefix + module.replace(".", "/") + suffix)
            path = assert_agent_path(workspace / name, workspace=workspace)
            if path.is_file() and not path.is_symlink() and path.stat().st_size <= 1_000_000:
                paths.append((name, path))
    if len(paths) != 1:
        return {"status": "unknown", "reason": "module_missing_or_ambiguous", "chain": []}
    name, path = paths[0]
    raw = path.read_bytes()
    canonical = git_blob(workspace, base_commit, name)
    if raw.replace(b"\r\n", b"\n") != canonical:
        return {"status": "unknown", "reason": "export_source_differs_from_base", "chain": []}
    proof = {"qualified": qualified, "path": name, "host_sha256": hashlib.sha256(raw).hexdigest(),
             "canonical_sha256": hashlib.sha256(canonical).hexdigest()}
    tree = ast.parse(raw)
    matches = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            matches.append((node, None))
        elif isinstance(node, ast.ImportFrom):
            if any(a.name == "*" for a in node.names):
                return {"status": "unknown", "reason": "star_export", "chain": [proof]}
            parts = module.split(".") if path.name == "__init__.py" else module.split(".")[:-1]
            for alias in node.names:
                if (alias.asname or alias.name) == symbol:
                    if node.level > len(parts):
                        return {"status": "unknown", "reason": "relative_export_outside_package", "chain": [proof]}
                    target = ".".join(parts[:len(parts) - node.level + 1] + (node.module.split(".") if node.module else [])) if node.level else node.module
                    matches.append((node, target + "." + alias.name if target else None))
        elif isinstance(node, ast.Import) and any((a.asname or a.name.split(".")[0]) == symbol for a in node.names):
            return {"status": "unknown", "reason": "module_import_shadows_definition", "chain": [proof]}
        elif any(isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)) and n.id == symbol
                 or isinstance(n, (ast.Import, ast.ImportFrom)) and any(
                     a.name == "*" or (a.asname or a.name.split(".")[0]) == symbol for a in n.names)
                 for n in ast.walk(node)):
            return {"status": "unknown", "reason": "export_assignment_or_control_flow", "chain": [proof]}
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"exec", "eval", "globals", "locals", "setattr"}
            for n in ast.walk(node)
        ):
            return {"status": "unknown", "reason": "dynamic_module_export", "chain": [proof]}
    if len(matches) != 1:
        return {"status": "unknown", "reason": "export_missing_or_multiple_bindings", "chain": [proof]}
    node, target = matches[0]
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return {"status": "static_chain_supported", "chain": [proof], "runtime_object_identity_proven": False}
    if target is None:
        return {"status": "unknown", "reason": "module_export_not_definition", "chain": [proof]}
    result = export_chain(workspace, target, base_commit, seen | {qualified})
    return {**result, "chain": [proof, *result["chain"]]}


def audit_scope():
    from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
    from evals.e1c_evaluation_2_issue_input import SOURCE

    old = ROOT / ".codex/e1c/evaluation_2/reference-scope-zero-v1"
    out = ROOT / ".codex/e1c/evaluation_2/export-chain-zero-v1"
    if out.exists():
        raise FileExistsError("export audit namespace already started; no replay")
    source = ROOT / ".codex/e1c/evaluation_2/report-anchor-reference-dev-v1"
    selected = {r["instance_id"]: r["selected_turn"] for r in json.loads((source / "state.json").read_bytes())["rows"]}
    frame = json.loads((old / "result.json").read_bytes())
    _save(out / "freeze.json", {"scope_results_sha256": _sha(old / "result.json"), "provider_calls": 0, "Gold_read": False,
                              "module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_export_chain.py"),
                              "protocol_sha256": _sha(ROOT / "docs/research/E1C2_EXPORT_CHAIN_V1_PROTOCOL_2026-10-07.md")})
    rows = []
    for task in frame["rows"]:
        iid = task["instance_id"]
        input_path = source / iid / f"turn-{selected[iid]}" / "input.json"
        frozen = json.loads(input_path.read_bytes())
        for assumption in task["scope_assumptions"]:
            value = export_chain(SOURCE / iid, assumption["conditional_binding"], frozen["base_commit"])
            rows.append({"instance_id": iid, "public_reference": assumption["public_reference"],
                         "input_sha256": _sha(input_path), "base_commit": frozen["base_commit"], **value})
    result = {"rows": rows, "provider_calls": 0, "provider_tokens": 0, "Gold_read": False, "machine_trusted": 0,
              "runtime_object_identity_proven": False, "public_namespace_intent_proven": False,
              "original_qualification_modified": False, "new_runtime_experiment": False}
    _save(out / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit-scope",))
    parser.parse_args()
    print(json.dumps(audit_scope(), ensure_ascii=False), flush=True)
