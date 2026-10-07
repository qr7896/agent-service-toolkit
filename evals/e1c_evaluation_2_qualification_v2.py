"""Fresh audit identity: absent source evidence is unknown, not byte mismatch."""

from __future__ import annotations

import ast
from unittest.mock import patch

from evals import e1c_evaluation_2_qualification as base

_inspect, _qualify, _resolve = base.inspect_program, base.qualify, base.resolve_symbol


def inspect_program(payload, frozen, workspace):
    absent = []
    exposed = {row["path"] for row in frozen["windows"]}

    def resolve(workspace, module, symbol):
        record = _resolve(workspace, module, symbol)
        if record and record["path"].relative_to(workspace).as_posix() not in exposed:
            absent.append({"module": module, "symbol": symbol,
                           "path": record["path"].relative_to(workspace).as_posix()})
            return None
        return record

    with patch.object(base, "resolve_symbol", resolve):
        result = _inspect(payload, frozen, workspace)
    if absent:
        result["unknown"] = sorted(set([*result["unknown"], "unexposed_dependency_source_provenance_unknown"]))
    result["unexposed_dependency_bindings"] = absent
    tree = ast.parse(payload["setup_source"] + "\n" + payload["target_action"])
    if any(isinstance(n, (ast.AugAssign, ast.Delete, ast.NamedExpr)) for n in ast.walk(tree)):
        result["unknown"] = sorted(set([*result["unknown"], "noncanonical_binding_mutation_unproven"]))
    return result


def qualify(*args, **kwargs):
    with patch.object(base, "inspect_program", inspect_program):
        result = _qualify(*args, **kwargs)
    return {**result, "schema": "e1c2-bounded-qualification-v2",
            "absence_of_provenance_not_source_mismatch": True}
