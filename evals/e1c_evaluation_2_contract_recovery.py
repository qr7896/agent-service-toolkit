"""Explicit comparison grammar and source-proven construction-frontier proofs.

Never invent an oracle, fixture value or control. Rejected old programs remain
rejected records; these transformations belong to a separate method identity.
"""

from __future__ import annotations

import ast
import hashlib
import re

from evals.e1c_evaluation_2_contract_method import CONTRACT_KEYS
from evals.e1c_evaluation_2_source_contract import rephase_setup


def tree_sha(tree):
    return hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()


def normalize_comparison(payload):
    if set(payload) != CONTRACT_KEYS or any(not isinstance(v, str) for v in payload.values()):
        raise ValueError("invalid_contract_fields")
    proof = {"schema": "e1c2-comparison-grammar-v1", "wrapper_added": False,
             "raw_program_equivalence_claimed": False, "predicate_changed": False}
    if payload["oracle"] != "value_relation":
        return dict(payload), proof
    tree = ast.parse(payload["assertion"])
    if len(tree.body) != 1:
        raise ValueError("one_explicit_comparison_required")
    node = tree.body[0]
    predicate = node.test if isinstance(node, ast.Assert) else node.value if isinstance(node, ast.Expr) else None
    if not isinstance(predicate, ast.Compare):
        raise ValueError("one_explicit_comparison_required")
    if any(tree_sha(predicate.left) == tree_sha(c) for c in predicate.comparators):
        raise ValueError("tautological_oracle")
    proof["predicate_sha256"] = tree_sha(predicate)
    if isinstance(node, ast.Assert):
        return dict(payload), proof
    wrapped = ast.fix_missing_locations(ast.Module(body=[ast.Assert(test=predicate, msg=None)], type_ignores=[]))
    normalized = {**payload, "assertion": ast.unparse(wrapped)}
    if tree_sha(ast.parse(normalized["assertion"]).body[0].test) != proof["predicate_sha256"]:
        raise ValueError("comparison predicate changed during grammar normalization")
    proof["wrapper_added"] = True
    return normalized, proof


def compile_contract(payload, frozen, workspace):
    canonical, grammar = normalize_comparison(payload)
    shifted, frontier = rephase_setup(canonical, frozen, workspace)
    before = ast.parse(canonical["setup_source"] + "\n" + canonical["target_action"])
    after = ast.parse(shifted["setup_source"] + "\n" + shifted["target_action"])
    if tree_sha(before) != tree_sha(after):
        raise ValueError("construction frontier changed the full target action program")
    if any(shifted[k] != canonical[k] for k in ("issue_quote", "expected_quote", "oracle", "assertion", "control_action")):
        raise ValueError("construction frontier changed oracle or control")
    return canonical, {"grammar": grammar, "frontier": frontier,
                       "target_action_program_ast_unchanged_after_frontier": True,
                       "target_action_program_ast_sha256": tree_sha(before),
                       "issue_quotes_or_control_changed": False}


def failure_phase(control, execution, payload):
    if hashlib.sha256(control["source"].encode()).hexdigest() != execution["probe_sha256"]:
        raise ValueError("execution does not match the generated control")
    setup_lines = len((payload["setup_source"].rstrip() + "\n").splitlines())
    control_lines = len(payload["control_action"].strip().splitlines())
    tree = ast.parse(control["source"])
    rows = []
    for run in execution.get("runs", []):
        frame = re.search(r'File "/e1c2_probe\.py", line (\d+), in <module>', run.get("log_tail", ""))
        if not frame:
            rows.append({"phase": "unknown_no_direct_generated_frame"})
            continue
        line = int(frame[1])
        node = next((n for n in tree.body if n.lineno <= line <= (n.end_lineno or n.lineno)), None)
        phase = "setup" if line <= setup_lines else "control_action" if line <= setup_lines + control_lines else "controller_check"
        rows.append({"phase": phase, "generated_line": line, "statement_kind": type(node).__name__ if node else "unknown",
                     "statement_ast_sha256": tree_sha(node) if node else None})
    return {"schema": "e1c2-generated-failure-phase-v1", "rows": rows,
            "semantic_bug_alignment_proven": False, "program_changed": False}
