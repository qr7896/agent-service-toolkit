"""Audit public expectation roles and observed sites, never certify semantics."""

from __future__ import annotations

import ast
import re


def expectation_role(quote):
    lines = [line.strip() for line in quote.splitlines() if line.strip()]
    if lines and all(re.match(r'^(?:File ["\'].*?, line \d+|Traceback \(|[\w.]+(?:Error|Exception):)', line) for line in lines):
        return "runtime_trace_not_desired_behavior"
    try:
        ast.parse(quote.strip())
    except SyntaxError:
        return "unclassified_requires_semantic_evidence"
    return "code_or_literal_not_desired_behavior" if lines else "empty"


def audit(payload, guard_sites, execution):
    run_sites = [set((p, int(line)) for p, line in re.findall(
        r'File "/testbed/([^"\n]+)", line (\d+)', run.get("log_tail", ""),
    )) for run in execution.get("runs", [])]
    guards = []
    for site in guard_sites:
        present = [(site["path"], site["line"]) in frames for frames in run_sites]
        guards.append({**{k: site[k] for k in ("path", "line", "source_sha256")},
                       "observed_in_each_run": present,
                       "status": "observed" if present and all(present) else "not_observed" if present else "unknown_no_runs"})
    return {"schema": "e1c2-witness-grounding-audit-v1", "expectation_role": expectation_role(payload["expected_quote"]),
            "public_failure_guard_sites": guards, "semantic_alignment_proven": False,
            "trusted_reproducer": False, "Gold_used": False, "provider_calls": 0,
            "controller_modified_probe": False, "absence_is_not_global_unreachability_proof": True}
