"""DEV-only import-prefix routing; never harvest names or values from assertions."""

from __future__ import annotations

import argparse
import ast
import json

from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_issue_fixture_facts import (
    ANSWER,
    CAPABILITIES,
    FENCES,
    FORBIDDEN,
    assertion_name,
)
from evals.e1c_evaluation_2_public_api_windows import resolve_symbol, window

OUT = ROOT / ".codex/e1c/evaluation_2/import-prefix-old-dev-audit-v1"


def invocation_status(source):
    """Conservative direct-script check; do not claim arbitrary code is reachable."""
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not functions or any(node.decorator_list or node.args.defaults or node.args.kw_defaults or node.returns
                            or getattr(node, "type_params", [])
                            or any(arg.annotation for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                                   *((node.args.vararg,) if node.args.vararg else ()), *((node.args.kwarg,) if node.args.kwarg else ())))
                            for node in functions):
        return "executable_or_unknown"
    inert = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef)
    if all(isinstance(node, inert) or isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
           and isinstance(node.value.value, str) for node in tree.body):
        return "function_bodies_not_invoked_by_direct_script"
    return "executable_or_unknown"


def import_prefix_seeds(statement):
    """Only leading absolute from-imports; the rest of each example is not visited."""
    seeds = []
    for number, match in enumerate(FENCES.finditer(statement.replace("\r\n", "\n")), 1):
        if match[1].strip().lower() not in {"", "py", "python"}:
            continue
        lines = match[2].splitlines()
        prompted = [line.lstrip()[4:] for line in lines if line.lstrip().startswith((">>> ", "... "))]
        try:
            tree = ast.parse("\n".join(prompted) if prompted else match[2])
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                break  # No traversal of assignments, calls, assertions, classes or functions.
            names = [alias.name for alias in node.names]
            roots = {name.split(".")[0] for name in names} if isinstance(node, ast.Import) else {(node.module or "").split(".")[0]}
            if (roots & FORBIDDEN or any(ANSWER.search(root) for root in roots)
                    or any(name == "*" or assertion_name(name) or ANSWER.search(name) for name in names)
                    or any(alias.asname and (assertion_name(alias.asname) or ANSWER.search(alias.asname)
                                             or alias.asname in CAPABILITIES) for alias in node.names)):
                break
            if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                if assertion_name(node.module):
                    break
                for alias in node.names:
                    seeds.append({"module": node.module, "symbol": alias.name, "block": number,
                                  "origin": "public_import_prefix_only"})
    return seeds


def import_windows(statement, workspace):
    output, seen = [], set()
    for seed in import_prefix_seeds(statement):
        record = resolve_symbol(workspace, seed["module"], seed["symbol"])
        if not record:
            continue
        key = (record["path"], record["symbol"])
        if key in seen:
            continue
        seen.add(key)
        item = window(record, workspace)
        item["origin"], item["origin_seed"] = seed["origin"], seed
        output.append(item)
        if len(output) == 4:
            break
    return output


def audit_old_dev():
    from evals import e1c_evaluation_2_contract_ab_dev as old
    from evals import e1c_evaluation_2_faithful_dev as faithful
    from evals.e1c_evaluation_2_counterfactual_fast_dev import verify_workspace

    source = faithful.OUT
    frozen = json.loads((source / "freeze.json").read_bytes())
    module = ROOT / "evals/e1c_evaluation_2_import_seed_audit.py"
    proof = {"schema": "e1c2-import-prefix-old-dev-zero-audit-v1", "module_sha256": _sha(module),
             "source_freeze_sha256": _sha(source / "freeze.json"), "provider_calls": 0,
             "source_modules": {name: _sha(ROOT / name) for name in (
                 "evals/e1c_evaluation_2_issue_fixture_facts.py", "evals/e1c_evaluation_2_public_api_windows.py")}}
    if (OUT / "freeze.json").exists():
        raise FileExistsError("audit already started; retain original namespace")
    _save(OUT / "freeze.json", proof)
    rows = []
    for row in frozen["tasks"]:
        iid = row["instance_id"]
        input_path, statement_path = source / "inputs" / f"{iid}.json", old.ISSUE / iid / "problem_statement.md"
        value = json.loads(input_path.read_bytes())
        if _sha(input_path) != row["input_sha256"] or _sha(statement_path) != value["public_statement_sha256"]:
            raise ValueError("frozen old DEV issue/input origin changed")
        workspace = old.SOURCE / iid
        verify_workspace(value, workspace)
        statement = statement_path.read_text(encoding="utf-8")
        added = import_windows(statement, workspace)
        existing = {(w["path"], w["symbol"]) for w in value["windows"]}
        item = {"instance_id": iid, "seeds": import_prefix_seeds(statement), "windows": added,
                "bound_windows": len(added), "new_definition_windows": sum((w["path"], w["symbol"]) not in existing for w in added),
                "public_statement_sha256": _sha(statement_path), "provider_calls": 0}
        _save(OUT / f"{iid}.json", item)
        rows.append({key: item[key] for key in ("instance_id", "bound_windows", "new_definition_windows")})
    result = {"fixed_denominator": 12, "audited": len(rows), "rows": rows, "provider_calls": 0,
              "new_canary_read": False, "model_input_changed": False, "generation_or_repair_score": None,
              "bounded_structural_reachability_only": True}
    _save(OUT / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit-old-dev",))
    parser.parse_args()
    print(json.dumps(audit_old_dev(), ensure_ascii=False))
