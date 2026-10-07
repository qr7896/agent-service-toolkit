"""Zero-provider diagnostic only; derived programs are NOT Agent outputs."""

from __future__ import annotations

import ast
import copy

from evals.e1c_evaluation_2_expectation_dev import contrast_binding, public_contrast


def derive(payload, frozen, workspace):
    pair = public_contrast(frozen["issue"])
    if pair is None or payload["oracle"] != "call_completes":
        return None
    setup = ast.parse(payload["setup_source"])
    target = ast.parse(payload["target_action"])
    if len(target.body) != 1 or not isinstance(target.body[0], (ast.Expr, ast.Assign)) or not isinstance(target.body[0].value, ast.Call):
        return None
    call = target.body[0].value
    imports = {a.asname or a.name: (n.module, a.name) for n in setup.body if isinstance(n, ast.ImportFrom)
               and n.module and not n.level for a in n.names}
    if not isinstance(call.func, ast.Name) or call.func.id not in imports:
        return None
    module, symbol = imports[call.func.id]
    if symbol != pair[1].func.attr:
        return None
    normal = pair[0].func.attr
    writes = {n.id for n in ast.walk(setup) if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))}
    writes.update(n.name for n in ast.walk(setup) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    if normal in writes or normal in imports and imports[normal] != (module, normal):
        return None
    if normal not in imports:
        setup.body.insert(0, ast.ImportFrom(module=module, names=[ast.alias(name=normal)], level=0))
    normal_call = copy.deepcopy(call)
    normal_call.func = ast.Name(id=normal, ctx=ast.Load())
    present = {k.arg for k in normal_call.keywords}
    for keyword in pair[0].keywords:
        if keyword.arg not in present:
            if not isinstance(keyword.value, ast.Constant):
                return None
            normal_call.keywords.append(copy.deepcopy(keyword))
    derived = {**payload, "setup_source": ast.unparse(ast.fix_missing_locations(setup)),
               "control_action": ast.unparse(ast.fix_missing_locations(ast.Expr(value=normal_call)))}
    binding = contrast_binding(derived, frozen, workspace)
    if binding["status"] != "explicit_contrast_exercised_syntactically":
        return None
    return derived, {"schema": "e1c2-derived-public-normal-diagnostic-v1", "binding": binding,
                     "model_generated": False, "live_integrated": False, "target_action_changed": False,
                     "oracle_changed": False, "derived_program_is_not_Agent_score": True,
                     "semantic_alignment_proven": False, "provider_calls": 0}
