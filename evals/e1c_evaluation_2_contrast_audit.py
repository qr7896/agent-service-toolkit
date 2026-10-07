"""Zero-execution diagnostics, not an oracle or semantic trust certificate."""

from __future__ import annotations

import ast


def contrast_evidence(payload):
    """Flag identical generated actions without replacing their code or values."""
    control = ast.parse(payload["control_action"])
    target = ast.parse(payload["target_action"])
    identical = ast.dump(control, include_attributes=False) == ast.dump(target, include_attributes=False)
    return {"schema": "e1c2-contrast-evidence-v1", "identical_action_AST": identical,
            "control_independence_proven": False, "target_preservation_proven": False,
            "recommendation": "require_distinct_supported_control" if identical else "independence_still_unproven",
            "provider_calls": 0, "code_executed": False, "semantic_alignment_proven": False}


def truth_guard_evidence(predicate):
    """A bare guard invokes Python truth testing; absence of raise proves nothing.

    Only a bare Name is supported. No runtime type is inferred and no input
    conversion is suggested. More complex expressions remain explicitly unknown.
    """
    node = ast.parse(predicate, mode="eval").body
    supported = isinstance(node, ast.Name)
    return {"schema": "e1c2-truth-guard-evidence-v1", "supported": supported,
            "name": node.id if supported else None,
            "operation": "python_truth_testing" if supported else "unknown",
            "possible_protocols": ["__bool__", "__len__"] if supported else [],
            "explicit_raise_not_required": supported,
            "runtime_type": "unknown", "exception_observed": False,
            "hypothesis_not_report_fact": True, "provider_calls": 0, "code_executed": False}
