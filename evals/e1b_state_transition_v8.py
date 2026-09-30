import re

VERSION = re.compile(r"version\s*(\d+)", re.IGNORECASE)
WORD_STATE = re.compile(r"\b(pending|completed|failed|approved|error|ok|false|true)\b", re.IGNORECASE)
SCHEMA_VERSION = "e1b-state-transition-v1"
EXPLICIT_COMPARE = re.compile(r"(?:==|!=|\bin\b|\bis\b|\bcase\b)", re.IGNORECASE)
TRUTHINESS_GUARD = re.compile(r"\b(?:if|elif)\s+(?:not\s+)?[A-Za-z_][A-Za-z0-9_.]*\s*:", re.IGNORECASE)


def _canonical(value):
    raw = value.strip().strip("'\"").lower()
    match = VERSION.fullmatch(raw)
    return f"version:{match.group(1)}" if match else raw


def build_transition_contract(behavioral_contract):
    targets = [_canonical(value) for value in behavioral_contract.get("named_target_values", [])]
    preserved = [_canonical(value) for value in behavioral_contract.get("named_preserved_values", [])]
    return {
        "schema_version": SCHEMA_VERSION,
        "target_obligations": [{"state": value, "mode": "change"} for value in targets],
        "preservation_obligations": [{"state": value, "mode": "identity"} for value in preserved],
        "default_transition": behavioral_contract.get("default_transition", "identity"),
        "provenance": "public-problem-statement deterministic extraction",
    }


def _state_patterns(state):
    if state.startswith("version:"):
        number = re.escape(state.split(":", 1)[1])
        return [
            re.compile(rf"\bversion\s*(?:==|!=|<=|>=|<|>)\s*{number}\b", re.IGNORECASE),
            re.compile(rf"\bversion\s*{number}\b", re.IGNORECASE),
        ]
    token = re.escape(state)
    return [
        re.compile(rf"['\"]{token}['\"]", re.IGNORECASE),
        re.compile(rf"\b{token}\b", re.IGNORECASE),
    ]


def _state_hits(corpus, state):
    hits = []
    for pattern in _state_patterns(state):
        hits.extend(match.start() for match in pattern.finditer(corpus))
    return sorted(set(hits))


def _guarded(corpus, position, radius=96):
    start = max(0, position - radius)
    end = min(len(corpus), position + radius)
    return bool(EXPLICIT_COMPARE.search(corpus[start:end]))


def audit_state_transition_contract(transition_contract, patch):
    corpus = "\n".join(str(content) for _, content in sorted(patch.items()))
    obligations = [
        *transition_contract.get("target_obligations", []),
        *transition_contract.get("preservation_obligations", []),
    ]
    rows = []
    for obligation in obligations:
        state = obligation["state"]
        hits = _state_hits(corpus, state)
        guarded = any(_guarded(corpus, hit) for hit in hits)
        rows.append(
            {
                **obligation,
                "witness_count": len(hits),
                "guarded_witness": guarded,
                "satisfied": bool(hits) and guarded,
            }
        )
    missing = [row for row in rows if not row["satisfied"]]
    truthiness_guards = sorted(set(match.group(0).strip() for match in TRUTHINESS_GUARD.finditer(corpus)))
    return {
        "schema_version": SCHEMA_VERSION,
        "obligations": rows,
        "missing_obligations": missing,
        "truthiness_guards": truthiness_guards,
        "transition_witness_complete": not missing and not truthiness_guards,
        "scope": (
            "static guarded-state witness only; necessary condition for explicit state/version "
            "transitions, not semantic equivalence or correctness proof"
        ),
    }


def require_state_transition_contract(transition_contract, patch):
    report = audit_state_transition_contract(transition_contract, patch)
    if not report["transition_witness_complete"]:
        problems = [f"{row['mode']}:{row['state']}" for row in report["missing_obligations"]]
        problems.extend(f"truthiness:{guard}" for guard in report["truthiness_guards"])
        raise ValueError(f"state-transition witness incomplete: {', '.join(problems)}")
    return report
