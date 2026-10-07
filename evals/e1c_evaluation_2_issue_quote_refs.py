"""Lossless public-issue catalogue and exact quote references; no fuzzy repair."""

from __future__ import annotations

import hashlib

from evals.e1c_evaluation_2_contract_method import CONTRACT_KEYS
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

REF_KEYS = (CONTRACT_KEYS - {"issue_quote", "expected_quote"}) | {"issue_quote_ref", "expected_quote_ref"}


def catalogue(issue):
    if not isinstance(issue, str):
        raise ValueError("public issue string required")
    audit_repair_visible_payload({"issue": issue})
    rows, offset = [], 0
    for line in issue.splitlines(keepends=True):
        for start in range(0, len(line), 1400):
            text = line[start:start + 1400]
            rows.append({"id": len(rows), "start": offset + start, "end": offset + start + len(text), "text": text,
                         "quote_eligible": 8 <= len(text) <= 1500})
        offset += len(line)
    if "".join(r["text"] for r in rows) != issue:
        raise ValueError("catalogue changed the public issue")
    return {"schema": "e1c2-public-issue-quote-catalogue-v1", "issue_sha256": hashlib.sha256(issue.encode()).hexdigest(), "spans": rows}


def resolve(payload, issue):
    if set(payload) != REF_KEYS or any(not isinstance(payload[k], str) for k in REF_KEYS if not k.endswith("_ref")):
        raise ValueError("reference_contract_fields_mismatch")
    spans = catalogue(issue)["spans"]
    canonical = {k: v for k, v in payload.items() if not k.endswith("_ref")}
    proof = {"issue_sha256": hashlib.sha256(issue.encode()).hexdigest(), "references": {},
             "quote_text_invented": False, "semantic_alignment_proven": False}
    for name in ("issue_quote", "expected_quote"):
        index = payload[name + "_ref"]
        if type(index) is not int or not 0 <= index < len(spans) or not spans[index]["quote_eligible"]:
            raise ValueError("invalid_public_issue_quote_reference")
        row = spans[index]
        canonical[name] = issue[row["start"]:row["end"]]
        if canonical[name] != row["text"]:
            raise ValueError("reference does not match exact public issue")
        proof["references"][name] = {k: row[k] for k in ("id", "start", "end")}
    return canonical, proof
