import json

from evals.e1b_contract_coverage_v7 import build_coverage_contract
from evals.e1b_contract_extractor_v6 import extract_contract

PROPOSAL_SYSTEM = 'You are an autonomous code editor in an evaluation sandbox. Return JSON only, exactly {"patch": {"relative/path.py": "complete replacement content"}}. Use only the public task, bounded evidence, behavioral contract, and coverage contract. Never use tests, grader outcomes, or gold answers. Treat every setup-file participant as required unless the public task explicitly says it is read-only. Implement every target behavior while preserving named and default identity states. Return the smallest complete patch that covers every required participant.'
REVIEW_SYSTEM = 'You are a final patch reviewer in an evaluation sandbox. Return JSON only, exactly {"patch": {"relative/path.py": "complete replacement content"}}. Never use tests, grader outcomes, or gold answers. First enforce participant coverage: every required participant must appear in the patch unless explicitly read-only. Then enforce the behavioral contract: target transitions change, named/default preserve states remain identity. Reject incomplete cross-file patches, truthiness-based state collapse, and destructive migrations. Return the smallest complete corrected patch.'


def enrich_payload(payload):
    enriched = dict(payload)
    behavioral = extract_contract(payload["problem_statement"])
    enriched["deterministic_contract"] = behavioral
    enriched["coverage_contract"] = build_coverage_contract(payload, behavioral)
    return enriched


def build_proposal_messages(payload):
    return [("system", PROPOSAL_SYSTEM), ("human", json.dumps(enrich_payload(payload), ensure_ascii=False))]


def build_review_messages(payload, candidate_patch):
    body = {"task": enrich_payload(payload), "candidate_patch": candidate_patch}
    return [("system", REVIEW_SYSTEM), ("human", json.dumps(body, ensure_ascii=False))]
