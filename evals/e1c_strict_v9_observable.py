"""Generic issue-to-observable contracts for strict-v9 development only."""

from __future__ import annotations

import hashlib
import json
import re

from evals.e1c_strict_v5_boundary import audit_repair_visible_payload

_BEHAVIOR = re.compile(
    r"(?i)\b(?P<subject>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\b.{0,100}?"
    r"\b(?:should|must|needs? to|is expected to)\s+"
    r"(?P<verb>clear|reset|invalidate|remove|preserve|allow|succeed|work|point|refer)\b"
    r"(?P<object>[^.\n]{0,100})"
)
_FAILURE = re.compile(
    r"(?i)\b(?P<action>exclude|filter|create|instantiate|render|build|link|access|introspect)"
    r"(?:\(\))?\b.{0,100}?\b(?P<failure>crash(?:es|ed)?|fail(?:s|ed)?|raises?|errors?)\b"
)
_EXPECTED_NOT = re.compile(
    r"(?i)(?:expected behavior.{0,120}?|\b(?:should|must)\b.{0,80}?)"
    r"\b(?:not|no longer|without)\b.{0,30}?\b(?P<subject>link|point|refer|raise|require)\w*\b"
    r"(?P<object>[^.\n]{0,100})"
)
_ATTRIBUTE = re.compile(
    r"(?i)\b(?P<attribute>[A-Za-z_]\w*)\s+attribute\b.{0,100}?"
    r"(?:doesn't|does not|should|must).{0,60}?\b(?P<verb>point|refer|belong|identify|find)\w*\b"
    r"(?P<object>[^.\n]{0,100})"
)
_ALLOW = re.compile(
    r"(?i)\b(?:suggest|expect|should|must|need)\w*\b.{0,100}?\b(?:let|allow)\b"
    r"(?P<object>[^.\n]{1,100}?)(?:\b(?:succeed|work|without|even if)\b|$)"
)


def _production_rows(localization: dict) -> list[dict]:
    return [r for r in localization.get("candidates", []) if isinstance(r, dict) and isinstance(r.get("path"), str) and r["path"].endswith(".py")]


def _choose_path(localization: dict, symbol: str | None) -> str | None:
    rows = _production_rows(localization)
    if symbol:
        exact = [r for r in rows if r.get("symbol") == symbol or symbol in str(r.get("text", ""))]
        paths = list(dict.fromkeys(r["path"] for r in exact))
        if len(paths) == 1:
            return paths[0]
    paths = list(dict.fromkeys(r["path"] for r in rows))
    return paths[0] if len(paths) == 1 else None

def _unique_path(localization: dict) -> str | None:
    paths=list(dict.fromkeys(r["path"] for r in _production_rows(localization)))
    return paths[0] if len(paths)==1 else None


def observable_contracts(projected_issue: str, localization: dict) -> list[dict]:
    rows: list[dict] = []
    for match in _BEHAVIOR.finditer(projected_issue):
        subject = match.group("subject").split(".")[-1]
        path = _choose_path(localization, subject)
        if path is None:
            continue
        rows.append({"kind":"semantic_postcondition","subject":subject,"verb":match.group("verb").lower(),"object":match.group("object").strip().lower(),"candidate_path":path,"execution_ready":True,"origin":"generic_behavior_clause"})
    for match in _FAILURE.finditer(projected_issue):
        action = match.group("action").lower()
        path = _choose_path(localization, action)
        if path is None:
            continue
        rows.append({"kind":"nonfailure_postcondition","subject":action,"verb":"not_fail","object":match.group("failure").lower(),"candidate_path":path,"execution_ready":True,"origin":"generic_failure_clause"})
    for match in _EXPECTED_NOT.finditer(projected_issue):
        path=_unique_path(localization)
        if path is not None:
            rows.append({"kind":"semantic_postcondition","subject":match.group("subject").lower(),"verb":"not_occur","object":match.group("object").strip().lower(),"candidate_path":path,"execution_ready":True,"origin":"generic_expected_negative_clause"})
    for match in _ATTRIBUTE.finditer(projected_issue):
        path=_choose_path(localization,match.group("attribute")) or _unique_path(localization)
        if path is not None:
            rows.append({"kind":"semantic_postcondition","subject":match.group("attribute"),"verb":match.group("verb").lower(),"object":match.group("object").strip().lower(),"candidate_path":path,"execution_ready":True,"origin":"generic_attribute_relation"})
    for match in _ALLOW.finditer(projected_issue):
        path=_unique_path(localization)
        if path is not None:
            rows.append({"kind":"nonfailure_postcondition","subject":"operation","verb":"allow","object":match.group("object").strip().lower(),"candidate_path":path,"execution_ready":True,"origin":"generic_allow_clause"})
    out=[]; seen=set()
    for row in rows:
        value={"schema":"e1c-strict-v9-observable-contract-v1","provenance":"projected_issue_plus_production_localization","benchmark_assertion_used":False,"task_id_used":False,**row}
        audit_repair_visible_payload(value)
        key=json.dumps(value,sort_keys=True,separators=(",",":"))
        if key in seen: continue
        seen.add(key); value["witness_sha256"]=hashlib.sha256(key.encode()).hexdigest(); out.append(value)
    return out
