import json

from evals.e1b_contract_extractor_v6 import extract_contract

SYSTEM = 'You are an autonomous code editor in an evaluation sandbox. Return JSON only, exactly {"patch": {"relative/path.py": "complete replacement content"}}. Use only the public task, supplied bounded evidence, and the deterministic contract attached to the request. Never use tests, grader outcomes, or gold answers. Treat preservation constraints and the default passthrough rule as hard requirements. Implement the smallest complete patch across all visible participants.'


def enrich_payload(payload):
    enriched = dict(payload)
    enriched["deterministic_contract"] = extract_contract(payload["problem_statement"])
    return enriched


def build_proposal_messages(payload):
    return [("system", SYSTEM), ("human", json.dumps(enrich_payload(payload), ensure_ascii=False))]


def build_review_messages(payload, candidate_patch):
    body = {
        "task": enrich_payload(payload),
        "candidate_patch": candidate_patch,
        "review_rule": "Reject any patch that changes a state/value outside target_changes without an explicit task requirement.",
    }
    return [("system", SYSTEM), ("human", json.dumps(body, ensure_ascii=False))]
