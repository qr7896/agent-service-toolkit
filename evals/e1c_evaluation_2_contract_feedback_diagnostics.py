"""Zero-call diagnostics for action envelopes and generated oracle readiness.

Not connected to live runners, not a semantic trust classifier or cache score.
"""

from __future__ import annotations

import ast
import hashlib
import re


def unwrap_known_envelope(value):
    proof = {"known_envelope_removed": False, "action_invented": False}
    if isinstance(value, dict) and set(value) == {"type", "content"} and value["type"] == "json_object":
        if not isinstance(value["content"], dict):
            raise ValueError("one dictionary action required inside known envelope")
        value = value["content"]
        if "type" in value or "content" in value:
            raise ValueError("recursive or ambiguous envelope rejected")
        proof["known_envelope_removed"] = True
    # Caller must still apply the strict action/quote/probe/static validators.
    return value, proof


def oracle_readiness(candidate, execution, oracle):
    source = candidate["source"]
    digest = hashlib.sha256(source.encode()).hexdigest()
    if candidate["probe_sha256"] != digest or execution["probe_sha256"] != digest:
        raise ValueError("generated source/execution binding differs")
    tree = ast.parse(source)
    rows = []
    for run in execution.get("runs", []):
        trace = run.get("log_tail", "")
        frames = re.findall(r'File "/e1c2_probe\.py", line (\d+), in <module>', trace)
        line = int(frames[-1]) if frames else None
        node = next((n for n in tree.body if line and n.lineno <= line <= (n.end_lineno or n.lineno)), None)
        exception = re.search(r"^([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*):?[^\n]*$", trace.rstrip().split("\n")[-1])
        kind = exception[1].rsplit(".", 1)[-1] if exception else None
        status = "unknown"
        if oracle == "value_relation" and isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
            if kind == "AssertionError":
                status = "predicate_false_semantics_unverified"
            elif kind and kind.endswith(("Error", "Exception")):
                status = "oracle_evaluation_error_requires_feedback"
        rows.append({"status": status, "generated_line": line, "exception_kind": kind,
                     "returncode": run.get("returncode"), "timed_out": run.get("timed_out", False)})
    return {"schema": "e1c2-oracle-readiness-diagnostic-v1", "rows": rows,
            "semantic_alignment_proven": False, "not_a_trust_certificate": True,
            "untrusted_trace_only": True, "program_changed": False}
