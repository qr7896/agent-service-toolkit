"""Zero-call public-input facts, never assertion or output-oracle serialization."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re

from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload, project_issue

FENCES = re.compile(r"(?ms)^\s*```([^\n]*)\n(.*?)^\s*```\s*$")
FORBIDDEN = {"pytest", "unittest", "os", "sys", "subprocess", "socket", "pathlib", "shutil", "importlib", "urllib", "requests",
             "httpx", "http", "aiohttp", "ftplib", "ctypes", "builtins", "pickle", "marshal", "runpy", "multiprocessing"}
CAPABILITIES = {"open", "eval", "exec", "compile", "__import__", "getattr", "setattr", "delattr", "globals", "locals", "vars", "input"}
ANSWER = re.compile(r"(?i)(?:^|_)(?:expected|actual|answer|result|output|gold|test)(?:$|_)")


def assertion_name(name):
    return name.rsplit(".", 1)[-1].lower().startswith("assert") or any(part.lstrip("_").startswith("test") for part in name.lower().split("."))


def expression(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool, type(None))):
        return {"kind": "literal", "value": node.value}
    if isinstance(node, ast.Name) and not node.id.startswith("__") and not ANSWER.search(node.id) and node.id not in CAPABILITIES:
        return {"kind": "reference", "name": node.id}
    if isinstance(node, ast.Attribute) and not node.attr.startswith("__") and node.attr not in CAPABILITIES and not assertion_name(node.attr):
        return {"kind": "attribute", "owner": expression(node.value), "name": node.attr}
    if isinstance(node, ast.Call) and all(keyword.arg is not None for keyword in node.keywords):
        return {"kind": "call", "callee": expression(node.func), "arguments": [expression(arg) for arg in node.args],
                "keywords": {keyword.arg: expression(keyword.value) for keyword in node.keywords}}
    if isinstance(node, (ast.List, ast.Tuple)):
        return {"kind": type(node).__name__.lower(), "items": [expression(item) for item in node.elts]}
    if isinstance(node, ast.Dict) and all(key is not None for key in node.keys):
        return {"kind": "mapping", "items": [[expression(key), expression(value)] for key, value in zip(node.keys, node.values, strict=True)]}
    if isinstance(node, ast.Subscript):
        return {"kind": "selection", "owner": expression(node.value), "index": expression(node.slice)}
    if isinstance(node, ast.Slice):
        return {"kind": "slice", "lower": expression(node.lower) if node.lower else None,
                "upper": expression(node.upper) if node.upper else None, "step": expression(node.step) if node.step else None}
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)):
        return {"kind": "operation", "operator": type(node.op).__name__, "left": expression(node.left), "right": expression(node.right)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return {"kind": "unary", "operator": type(node.op).__name__, "operand": expression(node.operand)}
    raise ValueError("unsupported or oracle-like expression")


def extract_facts(statement):
    # Keep the existing fail-closed prose policy, not its lossy code-fence heuristic.
    projection = project_issue(statement)
    normalized = statement.replace("\r\n", "\n")
    blocks, rejected = [], []
    for number, match in enumerate(FENCES.finditer(normalized), 1):
        if match[1].strip().lower() not in {"", "python", "py"}:
            rejected.append({"block": number, "reason": "non_python"})
            continue
        try:
            raw_lines = match[2].splitlines()
            prompted = [n for n, line in enumerate(raw_lines) if line.lstrip().startswith((">>> ", "... "))]
            code = "\n".join(raw_lines[n].lstrip()[4:] for n in prompted) if prompted else match[2]
            tree = ast.parse(code)
            nodes = list(ast.walk(tree))
            imports = [node for node in nodes if isinstance(node, (ast.Import, ast.ImportFrom))]
            roots = {alias.name.split(".")[0] for node in imports if isinstance(node, ast.Import) for alias in node.names}
            roots.update(node.module.split(".")[0] for node in imports if isinstance(node, ast.ImportFrom) and node.module)
            roots.update(alias.asname for node in imports for alias in node.names if alias.asname)
            if (roots & FORBIDDEN or any(isinstance(node, (ast.Assert, ast.FunctionDef, ast.AsyncFunctionDef,
                    ast.Raise, ast.Try, ast.TryStar, ast.With, ast.AsyncWith, ast.Compare, ast.Lambda)) for node in nodes)
                    or any(isinstance(node, ast.ClassDef) and (node.name.lower().startswith("test") or node.decorator_list or node.keywords) for node in nodes)
                    or any(assertion_name(alias.name) for node in imports for alias in node.names)
                    or any(isinstance(node, ast.ImportFrom) and node.module and assertion_name(node.module) for node in imports)
                    or any(isinstance(node, ast.Call) and assertion_name(node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else "") for node in nodes)
                    or any(isinstance(node, ast.Name) and (ANSWER.search(node.id) or node.id in CAPABILITIES or node.id in FORBIDDEN) for node in nodes)):
                raise ValueError("oracle_or_capability_block")
            facts = []
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    facts.append({"kind": "import", "module": node.module if isinstance(node, ast.ImportFrom) else None,
                                  "relative_level": node.level if isinstance(node, ast.ImportFrom) else 0,
                                  "names": [{"name": alias.name, "alias": alias.asname} for alias in node.names]})
                elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    facts.append({"kind": "fixture_binding", "name": node.targets[0].id, "value": expression(node.value)})
                elif isinstance(node, ast.ClassDef):
                    fields = []
                    for child in node.body:
                        if isinstance(child, ast.Assign) and len(child.targets) == 1 and isinstance(child.targets[0], ast.Name):
                            fields.append({"name": child.targets[0].id, "value": expression(child.value)})
                        elif isinstance(child, ast.Pass) or (isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant) and isinstance(child.value.value, str)):
                            continue
                        else:
                            raise ValueError("unsupported_fixture_class")
                    facts.append({"kind": "fixture_class", "name": node.name, "bases": [expression(base) for base in node.bases], "fields": fields})
                elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name) and node.value.func.id == "print":
                        continue
                    facts.append({"kind": "public_call", "value": expression(node.value)})
                else:
                    raise ValueError("unsupported_statement")
            calls = [fact["value"] for fact in facts if fact["kind"] in {"public_call", "fixture_binding"} and fact["value"]["kind"] == "call"]
            value = {"block": number, "source_line": normalized[:match.start()].count("\n") + 1,
                     "facts": facts, "terminal_call": calls[-1] if calls else None,
                     "prompt_input_lines": [n + 1 for n in prompted], "output_lines_preserved": False}
            audit_repair_visible_payload(value)
            if len(json.dumps([*blocks, value], ensure_ascii=False)) > 6000:
                raise ValueError("fixture_fact_budget_exceeded")
            blocks.append(value)
        except (ValueError, SyntaxError, BlindBoundaryViolation) as exc:
            rejected.append({"block": number, "reason": str(exc) if isinstance(exc, ValueError) else type(exc).__name__})
    return {"schema": "e1c2-public-fixture-facts-v1", "prose_sha256": projection.sha256,
            "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(), "blocks": blocks,
            "rejected_blocks": rejected, "executed": False, "assertion_oracle_preserved": False,
            "facts_sha256": audit_repair_visible_payload(blocks)}


def audit_dev():
    from evals import e1c_evaluation_2_contract_ab_dev as old
    from evals import e1c_evaluation_2_issue_input as public
    from evals.e1c_evaluation_2_public_api_windows import terminal_windows

    source = ROOT / ".codex/e1c/evaluation_2/hybrid-dev-v3"
    frame = json.loads((source / "freeze.json").read_bytes())
    tree = json.loads(public.TREE.read_bytes())
    identity = json.loads(old.IDENTITY.read_bytes())
    if tree["source_revision"] != identity["source_revision"]:
        raise ValueError("public blob metadata revision changed")
    destination = ROOT / ".codex/e1c/evaluation_2/public-fixture-facts-dev-v5"
    _save(destination / "freeze.json", {"module_sha256": _sha(ROOT / "evals/e1c_evaluation_2_issue_fixture_facts.py"),
                                      "source_freeze_sha256": _sha(source / "freeze.json"),
                                      "locator_sha256": _sha(ROOT / "evals/e1c_evaluation_2_public_api_windows.py"),
                                      "public_tree_metadata_sha256": _sha(public.TREE), "provider_calls": 0})
    rows = []
    for task in frame["tasks"]:
        iid = task["instance_id"]
        raw = old.ISSUE / iid / "problem_statement.md"
        if not raw.is_file():
            raise FileNotFoundError("raw public issue unavailable; cannot reconstruct from projection")
        content = raw.read_bytes()
        blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        if blob != tree["sha"].get(f"tasks/{iid}/problem_statement.md"):
            raise ValueError("raw public issue differs from official frozen blob")
        facts = extract_facts(content.decode("utf-8"))
        evidence = terminal_windows(facts, old.SOURCE / iid)
        facts["terminal_production_windows"] = evidence
        _save(destination / f"{iid}.json", facts)
        rows.append({"instance_id": iid, "public_statement_sha256": _sha(raw), "accepted_blocks": len(facts["blocks"]),
                     "rejected_blocks": len(facts["rejected_blocks"]), "facts_sha256": facts["facts_sha256"]})
        rows[-1]["terminal_windows"] = [{"path": row["path"], "symbol": row["symbol"], "owner": row.get("owner"),
                                        "relation_type": row["relation_type"], "depth": row["depth"]} for row in evidence]
    result = {"fixed_denominator": 12, "audited": len(rows), "rows": rows, "provider_calls": 0,
              "model_experiment_executed": False, "independent_validation": False}
    _save(destination / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit-dev",))
    parser.parse_args()
    print(json.dumps(audit_dev(), ensure_ascii=False))
