import hashlib
import json
from dataclasses import asdict, dataclass, replace

from evals.e1b_semantic_evidence_ir_v10 import verify
from evals.e1b_verification_decision_v10_1 import MAX_ESCALATIONS, decide

SCHEMA_VERSION = "e1b-verification-control-runtime-v1"
MAX_STEPS = 5
TERMINAL_ACTIONS = {"BLOCK_PATCH", "ALLOW_VERIFICATION"}


@dataclass(frozen=True)
class RuntimeState:
    step: int = 0
    escalations_used: int = 0
    evidence_ids: tuple[str, ...] = ()
    evidence_manifest_sha256: str = ""
    terminal_action: str | None = None


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def evidence_manifest(evidence):
    rows = [asdict(row) for row in sorted(evidence, key=lambda row: row.evidence_id)]
    return sha256(rows)


def _deduplicate(evidence):
    by_id = {}
    collisions = []
    for row in evidence:
        previous = by_id.get(row.evidence_id)
        if previous is not None and previous != row:
            collisions.append(row.evidence_id)
        else:
            by_id[row.evidence_id] = row
    return list(by_id.values()), sorted(set(collisions))


def run_control_runtime(obligations, acquisition_rounds, max_steps=MAX_STEPS):
    state = RuntimeState()
    evidence = []
    trace = []

    for _ in range(max_steps):
        before_manifest = evidence_manifest(evidence)
        round_index = state.escalations_used
        acquired = list(acquisition_rounds[round_index]) if round_index < len(acquisition_rounds) else []
        evidence, collisions = _deduplicate([*evidence, *acquired])

        if collisions:
            verification = {
                "schema_version": "runtime-collision",
                "dispositions": [
                    {"obligation_id": row.obligation_id, "disposition": "ambiguous"}
                    for row in obligations
                ],
            }
        else:
            verification = verify(obligations, evidence)

        policy = decide(obligations, verification, state.escalations_used)
        after_manifest = evidence_manifest(evidence)
        transition = {
            "step": state.step,
            "action": policy["action"],
            "reason": "evidence_id_collision" if collisions else policy["reason"],
            "dominant_disposition": policy["dominant_disposition"],
            "evidence_ids": sorted(row.evidence_id for row in evidence),
            "evidence_collisions": collisions,
            "before_evidence_manifest_sha256": before_manifest,
            "after_evidence_manifest_sha256": after_manifest,
            "escalations_used_before": state.escalations_used,
            "escalations_used_after": policy["escalations_used_after"],
        }
        trace.append(transition)
        state = replace(
            state,
            step=state.step + 1,
            escalations_used=policy["escalations_used_after"],
            evidence_ids=tuple(transition["evidence_ids"]),
            evidence_manifest_sha256=after_manifest,
            terminal_action=policy["action"] if policy["action"] in TERMINAL_ACTIONS else None,
        )
        if state.terminal_action:
            break
    else:
        state = replace(state, terminal_action="BLOCK_PATCH")
        trace.append({
            "step": state.step,
            "action": "BLOCK_PATCH",
            "reason": "max_steps_exhausted",
            "dominant_disposition": "unsupported",
            "evidence_ids": list(state.evidence_ids),
            "evidence_collisions": [],
            "before_evidence_manifest_sha256": state.evidence_manifest_sha256,
            "after_evidence_manifest_sha256": state.evidence_manifest_sha256,
            "escalations_used_before": state.escalations_used,
            "escalations_used_after": state.escalations_used,
        })

    result = {
        "schema_version": SCHEMA_VERSION,
        "max_steps": max_steps,
        "max_escalations": MAX_ESCALATIONS,
        "terminal_action": state.terminal_action,
        "final_state": asdict(state),
        "trace": trace,
        "claim_boundary": "synthetic control-plane validation only; no repair success or efficacy claim",
    }
    result["trace_sha256"] = sha256(trace)
    return result
