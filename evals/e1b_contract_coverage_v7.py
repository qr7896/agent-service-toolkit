def build_coverage_contract(payload, behavioral_contract):
    participants = list(dict.fromkeys(payload.get("setup_files", [])))
    clauses = [
        *behavioral_contract.get("target_changes", []),
        *behavioral_contract.get("preservation_constraints", []),
    ]
    return {
        "required_participants": participants,
        "required_behavior_clauses": clauses,
        "coverage_rule": "Every required participant must be represented in the final patch unless the task explicitly marks it read-only.",
        "preservation_rule": "The final patch must preserve every named/default identity state while implementing every target change.",
    }


def audit_patch_coverage(coverage_contract, patch):
    required = coverage_contract["required_participants"]
    written = list(patch)
    missing = [path for path in required if path not in patch]
    unexpected = [path for path in written if path not in required]
    return {
        "required_participants": required,
        "written_participants": written,
        "missing_required_participants": missing,
        "unexpected_participants": unexpected,
        "participant_coverage_complete": not missing,
    }


def require_patch_coverage(coverage_contract, patch):
    report = audit_patch_coverage(coverage_contract, patch)
    if not report["participant_coverage_complete"]:
        missing = ", ".join(report["missing_required_participants"])
        raise ValueError(f"contract coverage incomplete: missing required participants: {missing}")
    return report
