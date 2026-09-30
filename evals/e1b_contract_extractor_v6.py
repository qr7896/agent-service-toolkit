import re

BOUNDARY = re.compile(r"并保持|且保持|同时保持|保持|不能|不得|but preserve|while preserving", re.IGNORECASE)
STATE_VALUE = re.compile(r"(?:version\s*\d+|['\"][^'\"]+['\"]|\b(?:pending|completed|failed|approved|error|ok|false|true)\b)", re.IGNORECASE)


def _values(text):
    return list(dict.fromkeys(match.group(0) for match in STATE_VALUE.finditer(text)))


def extract_contract(problem_statement):
    text = problem_statement.strip()
    segments = []
    cursor = 0
    for match in BOUNDARY.finditer(text):
        before = text[cursor:match.start()].strip(" ，。;；")
        if before:
            segments.append(("change", before))
        cursor = match.end()
        tail_end = len(text)
        for separator in ("，", "。", ";", "；"):
            pos = text.find(separator, cursor)
            if pos >= 0:
                tail_end = min(tail_end, pos)
        preserved = text[cursor:tail_end].strip(" ，。;；")
        if preserved:
            segments.append(("preserve", preserved))
        cursor = tail_end + (tail_end < len(text))
    remainder = text[cursor:].strip(" ，。;；")
    if remainder:
        segments.append(("change", remainder))
    if not segments:
        segments = [("change", text)]

    target_changes = [clause for kind, clause in segments if kind == "change"]
    preservation_constraints = [clause for kind, clause in segments if kind == "preserve"]
    return {
        "target_changes": target_changes,
        "preservation_constraints": preservation_constraints,
        "named_target_values": _values(" ".join(target_changes)),
        "named_preserved_values": _values(" ".join(preservation_constraints)),
        "default_transition": "identity",
        "default_rule": "Preserve any state/value not explicitly required to change.",
        "implementation_rules": [
            "Use explicit equality/membership checks for named states instead of truthiness.",
            "Use identity/default passthrough for unrecognized or already-current states.",
            "Apply migrations only to the explicitly named legacy version/state.",
        ],
    }
