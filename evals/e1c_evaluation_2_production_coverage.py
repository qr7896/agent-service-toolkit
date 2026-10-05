"""Zero-call next-DEV input preparation with production and class-owner ranking."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

from evals.e1c_blind_boundary import BlindBoundaryViolation
from evals.e1c_blind_evidence import _definition_index, _production_python, extract_contract
from evals.e1c_evaluation_2_contract_ab_dev import ADMISSION, IDENTITY, ISSUE, SOURCE
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import input_json
from evals.e1c_strict_v5_boundary import (
    assert_production_relative_path,
    audit_repair_visible_payload,
)

NON_PRODUCTION = {"doc", "docs", "documentation", "example", "examples", "bench", "benchmark", "benchmarks", "build", "dist"}
OUT = ROOT / ".codex/e1c/evaluation_2/contract-coverage-dev-v2-ready"


def production_path(path: str) -> bool:
    assert_production_relative_path(path)
    return not any(part.lower() in NON_PRODUCTION or part.startswith(".") for part in Path(path).parts)


def freeze_input(seed: dict, workspace: Path) -> dict:
    definitions, _ = _definition_index(workspace)
    issue = seed["issue"]
    symbols = set(extract_contract(issue)["symbols"])
    plain_api_names = {name for name in re.findall(r"\b[A-Za-z_]\w*\b", issue) if "_" in name}
    # Public linked snake_case API names need not be enclosed in backticks.
    symbols.update(name for name in re.findall(r"\b[A-Za-z_]\w*\b", issue)
                   if "_" in name and name in definitions)
    # Reports may name an API differently from the frozen base. Prefix matches are retrieval hints only.
    for hint in plain_api_names - definitions.keys():
        prefixes = [name for name in definitions if "_" in name and not name.startswith("__") and hint.startswith(name + "_")]
        if prefixes:
            symbols.add(max(prefixes, key=len))
    traces = re.findall(r'File ["\']([^"\']+\.py)["\'], line (\d+), in ([A-Za-z_]\w*)', issue)
    ranked, owners = [], {}
    for symbol, items in definitions.items():
        eligible = []
        for item in items:
            try:
                if production_path(item["path"]):
                    eligible.append(item)
            except BlindBoundaryViolation:
                continue
        for item in eligible:
            relative = item["path"]
            if relative not in owners:
                tree = ast.parse((workspace / relative).read_text(encoding="utf-8", errors="replace"))
                owners[relative] = {child.lineno: node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
                                    for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))}
            owner = owners[relative].get(item["start_line"])
            trace = [(path, int(line)) for path, line, name in traces if name == symbol
                     and (path.replace("\\", "/").endswith(relative) or Path(path).name == Path(relative).name)
                     and item["start_line"] <= int(line) <= item["end_line"]]
            if symbol not in symbols and owner not in symbols and not trace:
                continue
            score = 1000 if trace else 750 if owner in symbols and symbol == "__init__" else 500
            if not trace and symbol in symbols and "_" in symbol and not symbol.startswith("__"):
                score = max(score, 850)
            if (owner or symbol).lower() in issue.splitlines()[0].lower():
                score += 150
            if symbol.startswith("__") and owner not in symbols:
                score -= 300 + min(150, len(eligible) * 10)
            lines = (workspace / relative).read_text(encoding="utf-8", errors="replace").splitlines()
            start = max(item["start_line"], trace[0][1] - 6) if trace else item["start_line"]
            text = "\n".join(lines[start - 1:min(item["end_line"], start + 45)])[:2500]
            row = {"path": relative, "symbol": symbol, "owner": owner, "start_line": start,
                   "end_line": start + text.count("\n"), "text": text, "source_sha256": item["source_sha256"],
                   "origin": "production_trace_or_qualified_definition"}
            try:
                audit_repair_visible_payload(row)
            except BlindBoundaryViolation:
                continue
            ranked.append((-score, relative, start, row))
    # Module-level aliases are executable API evidence even without a function definition.
    for file in workspace.rglob("*.py"):
        relative = file.relative_to(workspace).as_posix()
        try:
            if not _production_python(file, workspace) or not production_path(relative):
                continue
            raw = file.read_bytes()
            lines = raw.decode("utf-8", errors="replace").splitlines()
            pending = list(ast.parse("\n".join(lines)).body)
            while pending:
                node = pending.pop()
                if isinstance(node, ast.Assign):
                    names = [target.id for target in node.targets if isinstance(target, ast.Name) and target.id in plain_api_names]
                    for name in names:
                        start = max(1, node.lineno - 6)
                        text = "\n".join(lines[start - 1:node.lineno + 24])[:2500]
                        row = {"path": relative, "symbol": name, "owner": None, "start_line": start,
                               "end_line": start + text.count("\n"), "text": text,
                               "source_sha256": _sha(file), "origin": "public_api_module_alias"}
                        audit_repair_visible_payload(row)
                        ranked.append((-950, relative, start, row))
                elif isinstance(node, ast.If):
                    pending.extend([*node.body, *node.orelse])
                elif isinstance(node, (ast.Try, ast.TryStar)):
                    pending.extend([*node.body, *node.orelse, *node.finalbody, *(item for h in node.handlers for item in h.body)])
        except (SyntaxError, BlindBoundaryViolation, OSError):
            continue
    pool = [row for *_, row in sorted(ranked, key=lambda item: item[:3])] + seed["windows"]
    windows, seen = [], set()
    for row in pool:
        key = (row["path"], row.get("symbol"), row.get("owner"))
        try:
            if key in seen or not production_path(row["path"]):
                continue
        except BlindBoundaryViolation:
            continue
        row = {**row, "text": row["text"][:2500]}
        if len(input_json({"issue": issue, "windows": [*windows, row]})) > 23000:
            continue
        windows.append(row)
        seen.add(key)
        if len(windows) == 4:
            break
    value = {"schema": "e1c2-production-coverage-dev-input-v2-ready", "issue": issue,
             "issue_sha256": seed["issue_sha256"], "base_commit": seed["base_commit"], "windows": windows,
             "candidate_paths": [row["path"] for row in windows], "candidate_count": len(windows),
             "status": "ready_for_generation" if windows else "no_production_candidate"}
    value["input_sha256"] = audit_repair_visible_payload(value)
    return value


def prepare() -> dict:
    rows = []
    for task in json.loads(IDENTITY.read_bytes())["tasks"]:
        iid = task["instance_id"]
        if not all(json.loads((ADMISSION / iid / f"{phase}.json").read_bytes())["phase_pass"] for phase in ("base", "gold")):
            continue
        old = ISSUE / iid / "frozen_input_v4.json"
        seed = json.loads(old.read_bytes())
        head = subprocess.check_output(["git", "-C", str(SOURCE / iid), "rev-parse", "HEAD"], text=True, timeout=30).strip()
        dirty = subprocess.check_output(["git", "-C", str(SOURCE / iid), "status", "--porcelain", "--untracked-files=all"],
                                        text=True, timeout=90).strip()
        if head != seed["base_commit"] or dirty:
            raise ValueError("next DEV source must be clean at the frozen base")
        value = freeze_input(seed, SOURCE / iid)
        path = OUT / "inputs" / f"{iid}.json"
        if path.exists():
            if json.loads(path.read_bytes()) != value:
                raise ValueError("next DEV coverage input changed")
        else:
            _save(path, value)
        rows.append({"instance_id": iid, "input_sha256": _sha(path), "prior_input_sha256": _sha(old),
                     "candidate_paths": value["candidate_paths"]})
    if len(rows) != 9:
        raise ValueError("expected all nine admitted old DEV tasks")
    return {"prepared": len(rows), "rows": rows, "provider_calls": 0, "model_experiment_completed": False}


if __name__ == "__main__":
    print(json.dumps(prepare(), ensure_ascii=False))
