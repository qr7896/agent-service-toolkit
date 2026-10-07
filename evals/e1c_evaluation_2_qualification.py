"""Bounded, zero-model candidate qualification; not a semantic truth verdict."""

from __future__ import annotations

import ast
import hashlib
import json

from evals.e1c_evaluation_2_issue_fixture_facts import CAPABILITIES, expression
from evals.e1c_evaluation_2_issue_quote_refs import catalogue
from evals.e1c_evaluation_2_public_api_windows import resolve_symbol
from evals.e1c_evaluation_2_report_anchor_dev import report_anchors


def imports(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            result.update({a.asname or a.name: node.module + "." + a.name for a in node.names})
        elif isinstance(node, ast.Import):
            result.update({a.asname or a.name.split(".")[0]: a.name if a.asname else a.name.split(".")[0] for a in node.names})
    return result


def canonical(value, aliases):
    if isinstance(value, list):
        return [canonical(v, aliases) for v in value]
    if not isinstance(value, dict):
        return value
    if value.get("kind") == "reference" and value["name"] in aliases:
        return {"kind": "qualified_reference", "name": aliases[value["name"]]}
    result = {k: canonical(v, aliases) for k, v in value.items()}
    if result.get("kind") == "attribute" and result["owner"].get("kind") == "qualified_reference":
        return {"kind": "qualified_reference", "name": result["owner"]["name"] + "." + result["name"]}
    return result


def structure_status(actual, expected):
    if isinstance(actual, dict) and isinstance(expected, dict):
        if actual.get("kind") == "qualified_reference" and expected.get("kind") in {"reference", "attribute"}:
            # Omitted public imports must not be silently inferred or rejected.
            leaf = expected["name"]
            return "unproven" if actual["name"].split(".")[-1] == leaf else "different"
        if set(actual) != set(expected):
            return "different"
        statuses = [structure_status(actual[k], expected[k]) for k in actual]
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return "different"
        statuses = [structure_status(a, e) for a, e in zip(actual, expected, strict=True)]
    else:
        return "same" if json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True) else "different"
    return "different" if "different" in statuses else "unproven" if "unproven" in statuses else "same"


def inspect_program(payload, frozen, workspace):
    tree = ast.parse(payload["setup_source"] + "\n" + payload["target_action"])
    aliases = imports(tree)
    rejected, unknown, constraints, bindings = [], [], [], []
    definitions = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    assignments = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assignments.setdefault(node.targets[0].id, []).append(node.value)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id in aliases:
            rejected.append("import_alias_shadowed")
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in aliases:
            rejected.append("import_alias_shadowed")
        if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, (ast.Store, ast.Del)):
            root = node.value
            while isinstance(root, (ast.Attribute, ast.Subscript)):
                root = root.value
            if isinstance(root, ast.Name) and root.id in aliases:
                rejected.append("production_import_object_mutated")
            else:
                unknown.append("instance_or_container_mutation_unproven")
        if isinstance(node, ast.Call) and ((isinstance(node.func, ast.Name) and node.func.id in CAPABILITIES)
                or isinstance(node.func, ast.Attribute) and node.func.attr in CAPABILITIES):
            rejected.append("dynamic_capability_outside_qualification_scope")
    if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.If, ast.For, ast.While, ast.With, ast.Try)) for n in ast.walk(tree)):
        unknown.append("custom_behavior_or_control_flow_unproven")
    for block in frozen.get("public_fixture_facts", []):
        public_aliases = {a["alias"] or a["name"]: fact["module"] + "." + a["name"]
                          for fact in block["facts"] if fact["kind"] == "import" and fact.get("module")
                          for a in fact["names"]}
        for fact in block["facts"]:
            if fact["kind"] not in {"fixture_binding", "fixture_class"}:
                continue
            expected, observed = None, []
            try:
                if fact["kind"] == "fixture_binding":
                    expected = canonical(fact["value"], public_aliases)
                    observed = [canonical(expression(n), aliases) for n in assignments.get(fact["name"], [])]
                else:
                    expected = canonical({"bases": fact["bases"], "fields": fact["fields"]}, public_aliases)
                    for node in [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == fact["name"]]:
                        if node.decorator_list or node.keywords or any(not isinstance(n, (ast.Assign, ast.Pass)) or
                                isinstance(n, ast.Assign) and (len(n.targets) != 1 or not isinstance(n.targets[0], ast.Name)) for n in node.body):
                            raise ValueError("custom fixture class")
                        fields = [{"name": n.targets[0].id, "value": expression(n.value)} for n in node.body if isinstance(n, ast.Assign)
                                  and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)]
                        observed.append(canonical({"bases": [expression(n) for n in node.bases], "fields": fields}, aliases))
            except ValueError:
                unknown.append("public_fixture_expression_unproven")
            comparisons = [structure_status(v, expected) for v in observed]
            status = "unknown_missing_or_unsupported" if not observed else "public_structure_changed" if "different" in comparisons else (
                "unknown_public_reference_scope" if "unproven" in comparisons else "matches_public_structure"
            )
            constraints.append({"name": fact["name"], "kind": fact["kind"], "status": status})
            if status == "public_structure_changed":
                rejected.append("public_fixture_constraint_changed")
            elif status.startswith("unknown"):
                unknown.append("public_fixture_constraint_unproven")
    # Reachability through simple fixture bindings/classes only; arbitrary helper
    # functions stay unknown. This is dependency syntax, not runtime equivalence.
    pending = {n.id for n in ast.walk(ast.parse(payload["target_action"])) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    visited = set()
    hashes = {row["path"]: row["source_sha256"] for row in frozen["windows"]}
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        if name in aliases:
            module, symbol = aliases[name].rsplit(".", 1) if "." in aliases[name] else (aliases[name], "")
            record = resolve_symbol(workspace, module, symbol) if symbol else None
            if record:
                path = record["path"].relative_to(workspace).as_posix()
                digest = hashlib.sha256(record["path"].read_bytes()).hexdigest()
                if path not in hashes or digest != hashes[path]:
                    rejected.append("production_binding_source_unverified")
                else:
                    bindings.append({"alias": name, "symbol": symbol, "path": path, "source_sha256": digest})
        for node in [*assignments.get(name, []), *([definitions[name]] if name in definitions else [])]:
            pending.update(n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load))
    if not bindings:
        unknown.append("target_production_dependency_unproven")
    return {"rejected": sorted(set(rejected)), "unknown": sorted(set(unknown)), "public_constraints": constraints,
            "production_bindings": bindings, "runtime_reachability_or_value_equivalence_proven": False}


def qualify(payload, frozen, workspace, candidate, observation, *, normal_controls_pass, target_repeatable_failure):
    program = inspect_program(payload, frozen, workspace)
    anchors = report_anchors(frozen["issue"])
    # Exact source quote remains mandatory; roles are not semantic certificates.
    spans = catalogue(frozen["issue"])["spans"]
    matched = [a for a in anchors["anchors"] if spans[a["quote_ref"]]["text"] == payload["expected_quote"]]
    failures = list(program["rejected"])
    missing = list(program["unknown"])
    if not matched:
        missing.append("public_expectation_anchor_unproven")
    if observation.get("original_probe_sha256") != candidate["probe_sha256"] or observation.get("schema") != "e1c2-source-bound-exception-observation-v2":
        failures.append("observation_bound_to_another_probe_or_method")
    if not observation.get("canonical_git_and_effective_file_hash_required"):
        missing.append("canonical_runtime_source_identity_unproven")
    if not normal_controls_pass or not target_repeatable_failure or observation.get("returncode") != 1:
        failures.append("normal_or_target_or_instrumented_gate_failed")
    correspondence = any(r.get("matches_public_message") or r.get("declared_missing_keyword") for r in observation.get("records", []))
    status = "rejected" if failures else "unknown" if missing else "mechanism_supported_candidate" if correspondence else "behavior_candidate_mechanism_unproven"
    return {"schema": "e1c2-bounded-qualification-v1", "status": status, "rejected": sorted(set(failures)),
            "unknown": sorted(set(missing)), "program_evidence": program, "expectation_anchor_kinds": [a["kind"] for a in matched],
            "exception_correspondence": correspondence, "semantic_alignment_proven": False, "trusted_reproducer": False,
            "inventory_is_not_all_possible_public_constraints": True, "Gold_used": False, "provider_calls": 0}
