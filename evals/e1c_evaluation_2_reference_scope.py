"""Offline conditional reference-scope audit, never a semantic certificate."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from unittest.mock import patch

from evals import e1c_evaluation_2_qualification as original
from evals import e1c_evaluation_2_qualification_v2 as bounded
from evals.e1c_evaluation_2_public_api_windows import resolve_symbol
from evals.e1c_evaluation_2_qualification_v3 import git_blob


def reference_path(value):
    if value.get("kind") == "reference":
        return value["name"]
    if value.get("kind") == "attribute":
        owner = reference_path(value["owner"])
        return owner + "." + value["name"] if owner else None
    return None


def inspect_scope(payload, frozen, workspace):
    """Keep strict qualification unchanged; report assumptions separately.

    ponytail: sequential offline audit uses the existing checker hook; not a
    concurrent live-policy implementation. Export-chain equivalence is unknown.
    """
    strict = bounded.inspect_program(payload, frozen, workspace)
    hashes = {r["path"]: r["source_sha256"] for r in frozen["windows"]}
    roots = {p.removeprefix("src/").split("/")[0].removesuffix(".py") for p in hashes}
    assumptions, unresolved = [], []

    def compare(actual, expected):
        if isinstance(actual, dict) and isinstance(expected, dict):
            public_name = reference_path(expected)
            if actual.get("kind") == "qualified_reference" and public_name:
                qualified = actual["name"]
                if not qualified.endswith("." + public_name):
                    return "different"
                module, symbol = qualified.rsplit(".", 1)
                record = resolve_symbol(workspace, module, symbol) if module.split(".")[0] in roots else None
                reason = "scope_definition_unresolved_or_outside_frozen_library"
                if record:
                    path = record["path"].relative_to(workspace).as_posix()
                    raw = record["path"].read_bytes()
                    source_sha = hashlib.sha256(raw).hexdigest()
                    tree = ast.parse(raw)
                    # A same-file later assignment/import can replace a definition.
                    bindings = [n for n in tree.body if
                                isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == record["symbol"]
                                or isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and any(
                                    isinstance(t, ast.Name) and t.id == record["symbol"]
                                    for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))
                                or isinstance(n, (ast.Import, ast.ImportFrom)) and any(
                                    (a.asname or a.name.split(".")[0]) == record["symbol"] for a in n.names)]
                    reason = "scope_definition_not_uniquely_bound_to_frozen_base"
                    if len(bindings) == 1 and hashes.get(path) == source_sha and frozen.get("base_commit"):
                        canonical = git_blob(workspace, frozen["base_commit"], path)
                        if raw.replace(b"\r\n", b"\n") == canonical:
                            assumptions.append({"public_reference": public_name, "conditional_binding": qualified,
                                                "path": path, "source_sha256": source_sha,
                                                "canonical_base_sha256": hashlib.sha256(canonical).hexdigest(),
                                                "public_import_explicit": False, "export_chain_equivalence_proven": False})
                            return "same"
                unresolved.append({"public_reference": public_name, "conditional_binding": qualified, "reason": reason})
                return "unproven"
            if set(actual) != set(expected):
                return "different"
            statuses = [compare(actual[k], expected[k]) for k in actual]
        elif isinstance(actual, list) and isinstance(expected, list):
            if len(actual) != len(expected):
                return "different"
            statuses = [compare(a, e) for a, e in zip(actual, expected, strict=True)]
        else:
            return "same" if json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True) else "different"
        return "different" if "different" in statuses else "unproven" if "unproven" in statuses else "same"

    with patch.object(original, "structure_status", compare):
        conditional = bounded.inspect_program(payload, frozen, workspace)
    alternatives = {}
    for row in assumptions:
        alternatives.setdefault(row["public_reference"], set()).add(row["conditional_binding"])
    conflict = any(len(values) > 1 for values in alternatives.values())
    status = ("rejected" if strict["rejected"] or conditional["rejected"] or conflict else
              "unknown" if conditional["unknown"] else "conditional_structure_supported" if assumptions else "explicit_structure_supported")
    return {"schema": "e1c2-conditional-reference-scope-v1", "status": status,
            "strict_program_evidence": strict, "conditional_program_evidence": conditional,
            "scope_assumptions": assumptions, "unresolved_references": unresolved,
            "conflicting_public_bindings": conflict, "semantic_alignment_proven": False,
            "trusted_reproducer": False, "Gold_used": False, "provider_calls": 0,
            "not_integrated_into_live_policy": True, "original_public_facts_modified": False}


def audit_dev():
    from evals.e1c_blind_boundary import assert_agent_path
    from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
    from evals.e1c_evaluation_2_issue_input import SOURCE
    from evals.e1c_evaluation_2_issue_quote_refs import resolve
    from evals.e1c_evaluation_2_qualification_v3 import authority_overlay, load_authority

    source = ROOT / ".codex/e1c/evaluation_2/report-anchor-reference-dev-v1"
    out = ROOT / ".codex/e1c/evaluation_2/reference-scope-zero-v1"
    if out.exists():
        raise FileExistsError("scope audit namespace already started; no replay")
    prior = json.loads((ROOT / "data/e1c_evaluation_2_authority_integration_results.json").read_bytes())
    authority_path = ROOT / ".codex/e1c/evaluation_2/qualification-source-authority-zero-v2/result.json"
    authority = load_authority(authority_path, prior["source_records"]["qualification-source-authority-zero-v2"])
    seal = json.loads((source / "generation-seal.json").read_bytes())
    if _sha(source / "generation-seal.json") != "5997675327f8f246b179413f0c2df5efd2b66fd2edacc2f6db430796588ea86f":
        raise ValueError("original producer seal changed")
    for relative, digest in seal["files"].items():
        if _sha(assert_agent_path(source / relative, workspace=source)) != digest:
            raise ValueError("sealed producer file changed")
    frame = json.loads((source / "freeze.json").read_bytes())
    selected = {r["instance_id"]: r["selected_turn"] for r in json.loads((source / "state.json").read_bytes())["rows"]}
    modules = ["evals/e1c_evaluation_2_reference_scope.py", "evals/e1c_evaluation_2_qualification.py",
               "evals/e1c_evaluation_2_qualification_v2.py", "evals/e1c_evaluation_2_qualification_v3.py",
               "evals/e1c_evaluation_2_public_api_windows.py", "evals/e1c_evaluation_2_issue_fixture_facts.py"]
    _save(out / "freeze.json", {"provider_calls": 0, "Gold_read": False, "source_seal_sha256": _sha(source / "generation-seal.json"),
                              "authority_sha256": _sha(authority_path), "module_hashes": {p: _sha(ROOT / p) for p in modules},
                              "protocol_sha256": _sha(ROOT / "docs/research/E1C2_REFERENCE_SCOPE_V1_PROTOCOL_2026-10-07.md")})
    rows = []
    for task in frame["tasks"]:
        iid = task["instance_id"]
        turn = source / iid / f"turn-{selected[iid]}"
        frozen = json.loads((turn / "input.json").read_bytes())
        response = json.loads((turn / "response.json").read_bytes())
        payload = json.loads(response["raw"])["probe"]
        if "issue_quote_ref" in payload:
            payload, _ = resolve(payload, frozen["issue"])
        scope = {"instance_id": iid, "base_commit": frozen["base_commit"], "image": task["image_id"]}
        augmented, proofs = authority_overlay(frozen, SOURCE / iid, scope, authority)
        result = inspect_scope(payload, augmented, SOURCE / iid)
        result.update({"original_input_sha256": _sha(turn / "input.json"), "original_response_sha256": _sha(turn / "response.json"),
                       "additional_authority": proofs})
        _save(out / (iid + ".json"), result)
        rows.append({"instance_id": iid, "status": result["status"], "scope_assumptions": result["scope_assumptions"],
                     "unresolved_references": result["unresolved_references"], "result_sha256": _sha(out / (iid + ".json"))})
    result = {"rows": rows, "provider_calls": 0, "provider_tokens": 0, "Gold_read": False, "machine_trusted": 0,
              "original_qualification_modified": False, "new_runtime_experiment": False, "fixed_DEV_denominator": 12,
              "cached_reference_denominator": len(rows), "live_method_freeze_completed": False}
    _save(out / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit-dev",))
    parser.parse_args()
    print(json.dumps(audit_dev(), ensure_ascii=False), flush=True)
