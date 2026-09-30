import hashlib
import json
from dataclasses import asdict, dataclass

from evals.e1b_evidence_acquisition_v10_3 import ACTIONS, MAX_ACQUISITION_COST, choose_action

SCHEMA_VERSION = "e1b-acquisition-policy-interface-v1"
FORBIDDEN_FEATURE_TOKENS = ("gold", "grader", "resolved", "expected_patch", "outcome", "test_result")


@dataclass(frozen=True)
class PolicyContext:
    attempted: tuple[str, ...]
    cumulative_cost: int


def canonical(value):
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def runtime_features(obligations, verification, context):
    dispositions = {row["obligation_id"]: row["disposition"] for row in verification["dispositions"]}
    unresolved = [row for row in obligations if dispositions.get(row.obligation_id) != "satisfied"]
    mix = {name: 0 for name in ("unsupported", "ambiguous", "contradicted")}
    for row in unresolved:
        state = dispositions.get(row.obligation_id, "unsupported")
        if state in mix:
            mix[state] += 1
    features = []
    kinds = {row.kind for row in unresolved}
    for action in ACTIONS:
        features.append({
            "action": action.name,
            "compatible": bool(kinds.intersection(action.capabilities)),
            "prior_attempt": action.name in context.attempted,
            "structural": action.structural,
            "protocol_cost": action.cost,
            "unsupported_count": mix["unsupported"],
            "ambiguous_count": mix["ambiguous"],
            "contradicted_count": mix["contradicted"],
            "remaining_acquisition_budget": MAX_ACQUISITION_COST - context.cumulative_cost,
        })
    audit_feature_leakage(features)
    return features


def audit_feature_leakage(features):
    violations = []

    def walk(value, path="root"):
        if isinstance(value, dict):
            for key, nested in value.items():
                lowered = str(key).lower().replace("-", "_")
                if any(token in lowered for token in FORBIDDEN_FEATURE_TOKENS):
                    violations.append(f"{path}.{key}")
                if lowered in {"provenance", "source_label", "data_source"} and isinstance(nested, str):
                    label = nested.lower().replace("-", "_")
                    if any(token in label for token in FORBIDDEN_FEATURE_TOKENS):
                        violations.append(f"{path}.{key}={nested}")
                walk(nested, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, nested in enumerate(value):
                walk(nested, f"{path}[{index}]")

    walk(features)
    if violations:
        raise ValueError(f"forbidden runtime feature fields: {sorted(set(violations))}")
    return {"runtime_gold_leakage": []}


class DeterministicBaselinePolicy:
    policy_id = "deterministic-v10.3"

    def select(self, obligations, verification, context):
        return choose_action(
            obligations,
            verification,
            list(context.attempted),
            context.cumulative_cost,
        )


def action_set_manifest():
    return sha256([asdict(action) for action in ACTIONS])


def dominance_report():
    rows = []
    for candidate in ACTIONS:
        for other in ACTIONS:
            if candidate.name == other.name:
                continue
            if (
                set(candidate.capabilities) == set(other.capabilities)
                and candidate.structural == other.structural
                and candidate.cost > other.cost
            ):
                rows.append({"dominated": candidate.name, "by": other.name, "cost_delta": candidate.cost - other.cost})
    return sorted(rows, key=lambda row: (row["dominated"], row["by"]))
