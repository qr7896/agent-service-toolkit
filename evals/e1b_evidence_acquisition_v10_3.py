import hashlib
import json
from dataclasses import asdict, dataclass

SCHEMA_VERSION = "e1b-evidence-acquisition-v1"
MAX_ACQUISITION_COST = 8

@dataclass(frozen=True)
class AcquisitionAction:
    name: str
    cost: int
    capabilities: tuple[str, ...]
    structural: bool = False

ACTIONS = (
    AcquisitionAction("lexical", 1, ("identity", "change")),
    AcquisitionAction("coverage_check", 1, ("coverage",)),
    AcquisitionAction("direct_ast", 2, ("identity", "change")),
    AcquisitionAction("helper_summary", 3, ("identity", "change")),
    AcquisitionAction("structural_escalation", 4, ("coverage", "identity", "change"), True),
)


def canonical(value):
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def choose_action(obligations, verification, attempted, cumulative_cost):
    by_id = {row["obligation_id"]: row["disposition"] for row in verification["dispositions"]}
    unresolved = [row for row in obligations if by_id.get(row.obligation_id) != "satisfied"]
    dispositions = {by_id.get(row.obligation_id, "unsupported") for row in unresolved}
    if "contradicted" in dispositions:
        return {"action": "BYPASS_BLOCK", "cost": 0, "reason": "contradiction_bypasses_acquisition", "obligation_ids": sorted(row.obligation_id for row in unresolved)}
    kinds = {row.kind for row in unresolved}
    candidates = [
        row for row in ACTIONS
        if row.name not in attempted and kinds.intersection(row.capabilities)
    ]
    if "ambiguous" in dispositions:
        candidates = [row for row in candidates if row.structural]
    else:
        candidates = [row for row in candidates if not row.structural]
    if not candidates:
        return {"action": "EXHAUSTED", "cost": 0, "reason": "no_compatible_untried_action", "obligation_ids": sorted(row.obligation_id for row in unresolved)}
    chosen = min(candidates, key=lambda row: (row.cost, row.name))
    if cumulative_cost + chosen.cost > MAX_ACQUISITION_COST:
        return {"action": "BUDGET_EXHAUSTED", "cost": 0, "reason": "acquisition_cost_budget_exhausted", "obligation_ids": sorted(row.obligation_id for row in unresolved)}
    return {"action": chosen.name, "cost": chosen.cost, "reason": "cheapest_compatible_untried_action", "obligation_ids": sorted(row.obligation_id for row in unresolved)}
