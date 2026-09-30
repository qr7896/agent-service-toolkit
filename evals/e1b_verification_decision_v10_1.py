import hashlib
import json
from collections import Counter

SCHEMA_VERSION = "e1b-verification-decision-v1"
MAX_ESCALATIONS = 2
PRIORITY = ("contradicted", "ambiguous", "unsupported", "satisfied")

ACTIONS = {
    "contradicted": "BLOCK_PATCH",
    "ambiguous": "STRUCTURAL_ESCALATION",
    "unsupported": "REQUEST_MORE_EVIDENCE",
    "satisfied": "ALLOW_VERIFICATION",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def manifest_sha256(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sufficiency(obligations, verification):
    by_id = {row["obligation_id"]: row["disposition"] for row in verification["dispositions"]}
    counts = Counter(by_id.get(row.obligation_id, "unsupported") for row in obligations)
    kinds = {}
    for obligation in obligations:
        bucket = kinds.setdefault(obligation.kind, {"required": 0, "satisfied": 0})
        bucket["required"] += 1
        bucket["satisfied"] += int(by_id.get(obligation.obligation_id) == "satisfied")
    return {
        "required": len(obligations),
        "satisfied": counts["satisfied"],
        "unsupported": counts["unsupported"],
        "ambiguous": counts["ambiguous"],
        "contradicted": counts["contradicted"],
        "by_kind": dict(sorted(kinds.items())),
    }


def decide(obligations, verification, escalations_used=0):
    stats = sufficiency(obligations, verification)
    present = {row["disposition"] for row in verification["dispositions"]}
    dominant = next((state for state in PRIORITY if state in present), "unsupported")

    if dominant == "contradicted":
        action = ACTIONS[dominant]
        next_used = escalations_used
        reason = "contradiction_blocks_immediately"
    elif dominant in {"ambiguous", "unsupported"}:
        if escalations_used >= MAX_ESCALATIONS:
            action = "BLOCK_PATCH"
            next_used = escalations_used
            reason = "escalation_budget_exhausted"
        else:
            action = ACTIONS[dominant]
            next_used = escalations_used + 1
            reason = "bounded_escalation"
    else:
        action = ACTIONS["satisfied"]
        next_used = escalations_used
        reason = "all_obligations_satisfied_for_verification_only"

    result = {
        "schema_version": SCHEMA_VERSION,
        "priority": list(PRIORITY),
        "max_escalations": MAX_ESCALATIONS,
        "escalations_used_before": escalations_used,
        "escalations_used_after": next_used,
        "dominant_disposition": dominant,
        "action": action,
        "reason": reason,
        "sufficiency": stats,
        "claim_boundary": "ALLOW_VERIFICATION permits downstream verification only; it is not PASS or repair success",
    }
    result["audit_manifest_sha256"] = manifest_sha256(result)
    return result
