import hashlib
import json
from dataclasses import asdict, dataclass

SCHEMA_VERSION = "e1b-semantic-evidence-ir-v1"


def typed(value):
    return {"type": type(value).__name__, "value": value}


@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    kind: str
    source: dict | None = None
    target: dict | None = None
    participant: str | None = None


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    kind: str
    status: str
    source: dict | None = None
    target: dict | None = None
    participant: str | None = None
    effect_risk: bool = False
    path: str | None = None
    function: str | None = None
    construct: str | None = None
    depth: int = 0
    reason: str = ""


def canonical(records):
    payload = [asdict(row) if hasattr(row, "__dataclass_fields__") else row for row in records]
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def manifest_sha256(records):
    return hashlib.sha256(canonical(records).encode()).hexdigest()


def coverage_evidence(audit):
    rows = []
    for path in sorted(audit.get("required_participants", [])):
        written = path in set(audit.get("written_participants", []))
        rows.append(Evidence(
            evidence_id=f"coverage:{path}", kind="coverage",
            status="support" if written else "contradict",
            participant=path, path=path,
            reason="participant_written" if written else "participant_missing",
        ))
    return rows


def dataflow_evidence(audit):
    rows = []
    for index, branch in enumerate(audit.get("branches", [])):
        status = "unsupported" if branch.get("effects") or branch.get("class") == "ambiguous" else "support"
        rows.append(Evidence(
            evidence_id=f"dataflow:{index}:{branch.get('path')}",
            kind=branch.get("class", "unsupported"),
            status=status,
            source={"type": branch["source_value"][0], "value": branch["source_value"][1]},
            target=(
                {"type": branch["value"][0], "value": branch["value"][1]}
                if branch.get("value") is not None else None
            ),
            effect_risk=bool(branch.get("effects")),
            path=branch.get("path"),
            function=branch.get("variable"),
            construct=branch.get("construct"),
            reason=branch.get("reason", ""),
        ))
    return rows


def helper_evidence(audit):
    rows = []
    for index, witness in enumerate(audit.get("call_witnesses", [])):
        rows.append(Evidence(
            evidence_id=f"helper:{index}:{witness.get('path')}:{witness.get('helper')}",
            kind=witness["class"], status="support",
            source={"type": witness["source"][0], "value": witness["source"][1]},
            target=(
                {"type": witness["target"][0], "value": witness["target"][1]}
                if witness.get("target") is not None else None
            ),
            path=witness.get("path"), function=witness.get("helper"),
            construct="helper_summary", depth=int(witness.get("depth", 1)),
            reason="bounded_helper_summary",
        ))
    return rows


def _same(left, right):
    return left == right


def verify(obligations, evidence):
    dispositions = []
    for obligation in sorted(obligations, key=lambda row: row.obligation_id):
        candidates = [
            row for row in evidence
            if (
                (obligation.kind == "coverage" and row.kind == "coverage" and row.participant == obligation.participant)
                or (
                    obligation.kind in {"identity", "change"}
                    and row.kind in {"identity", "change"}
                    and _same(row.source, obligation.source)
                )
            )
        ]
        provenance = [(row.path, row.function, row.construct, row.depth) for row in candidates]
        collision = len(provenance) != len(set(provenance))
        supporting = [
            row for row in candidates
            if row.status == "support"
            and not row.effect_risk
            and (
                obligation.kind == "coverage"
                or (
                    row.kind == obligation.kind
                    and (obligation.target is None or _same(row.target, obligation.target))
                )
            )
        ]
        contradicting = [
            row for row in candidates
            if row.status == "contradict"
            or row.effect_risk
            or (
                obligation.kind in {"identity", "change"}
                and (
                    row.kind != obligation.kind
                    or (obligation.target is not None and row.target is not None and not _same(row.target, obligation.target))
                )
            )
        ]
        unsupported = [row for row in candidates if row.status == "unsupported"]
        if collision or len(supporting) > 1:
            disposition = "ambiguous"
        elif contradicting:
            disposition = "contradicted"
        elif len(supporting) == 1:
            disposition = "satisfied"
        elif unsupported:
            disposition = "unsupported"
        else:
            disposition = "unsupported"
        dispositions.append({
            "obligation_id": obligation.obligation_id,
            "disposition": disposition,
            "candidate_ids": sorted(row.evidence_id for row in candidates),
            "reason": {
                "satisfied": "single_support",
                "ambiguous": "duplicate_or_provenance_collision",
                "contradicted": "explicit_conflict_or_effect_risk",
                "unsupported": "no_supported_evidence",
            }[disposition],
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "dispositions": dispositions,
        "decision": "pass" if dispositions and all(row["disposition"] == "satisfied" for row in dispositions) else "fail_closed",
        "obligation_manifest_sha256": manifest_sha256(sorted(obligations, key=lambda row: row.obligation_id)),
        "evidence_manifest_sha256": manifest_sha256(sorted(evidence, key=lambda row: row.evidence_id)),
    }
