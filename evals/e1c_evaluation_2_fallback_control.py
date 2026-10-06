"""DEV diagnostic: derive one literal-representation control for A fallback.

Unknown fixtures remain unknown. This is not a semantic correctness proof or a
new reproducer score; the original target, oracle and frozen records are intact.
"""

from __future__ import annotations

import ast
import copy
import hashlib

from evals.e1c_evaluation_2_counterfactual_contract import compile_pair
from evals.e1c_evaluation_2_probe import validate_candidate
from evals.e1c_evaluation_2_source_contract import source_trees


def derive_control(candidate, frozen, workspace):
    source = candidate["source"]
    proof = {"schema": "e1c2-fallback-control-v1", "compiled": False,
             "status": "unsupported_or_unproven", "target_changed": False,
             "oracle_changed": False, "semantic_equivalence_proven": False,
             "trusted_reproducer": False,
             "target_sha256": hashlib.sha256(source.encode()).hexdigest()}
    tree = ast.parse(source)
    # Even nested/invoked constant asserts are not an observable behavior check.
    if any(isinstance(n, ast.Assert) and isinstance(n.test, ast.Constant) for n in ast.walk(tree)):
        return None, {**proof, "status": "constant_oracle_rejected"}
    if any(not isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign, ast.Expr, ast.Assert)) for n in tree.body):
        return None, proof
    if any(isinstance(n, (ast.Try, ast.TryStar, ast.Raise, ast.NamedExpr, ast.Lambda,
                          ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) for n in ast.walk(tree)):
        return None, proof
    positions = [i for i, n in enumerate(tree.body)
                 if isinstance(n, (ast.Expr, ast.Assign)) and isinstance(n.value, ast.Call)]
    if not positions:
        return None, proof
    frontier = positions[-1]
    if not any(isinstance(n, ast.Assert) for n in tree.body[frontier + 1:]):
        return None, proof
    # No subsequent computation/side effect may influence the extracted call.
    if any(not isinstance(n, ast.Assert) and not (
        isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
        and all(isinstance(t, ast.Name) for t in n.targets)
    ) for n in tree.body[frontier + 1:]):
        return None, proof
    if any(isinstance(n, ast.Assert) for n in tree.body[:frontier]):
        return None, proof
    call = tree.body[frontier].value
    name = call.func.id if isinstance(call.func, ast.Name) else call.func.attr if isinstance(call.func, ast.Attribute) else None
    if not any(isinstance(n, ast.FunctionDef) and n.name == name
               for _, t in source_trees(frozen, workspace) for n in ast.walk(t)):
        return None, {**proof, "status": "call_not_in_selected_production"}
    setup = ast.unparse(ast.Module(body=tree.body[:frontier], type_ignores=[]))
    root = call.func
    while isinstance(root, ast.Attribute):
        root = root.value
    if not isinstance(root, ast.Name) or any(
        isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id == root.id
        for statement in tree.body[:frontier] for n in ast.walk(statement)
    ):
        return None, {**proof, "status": "callee_binding_unproven"}
    target = ast.unparse(tree.body[frontier])
    supported = []
    # Ask the existing conservative compiler about each possible contrast; do
    # not resolve runtime values, infer dimensions, or patch the original probe.
    for index in range(len(call.args) + len(call.keywords)):
        control_node = copy.deepcopy(tree.body[frontier])
        control_call = control_node.value
        replacement = ast.List(elts=[], ctx=ast.Load())
        if index < len(call.args):
            control_call.args[index] = replacement
        else:
            control_call.keywords[index - len(call.args)].value = replacement
        payload = {"setup_source": setup, "control_action": ast.unparse(control_node),
                   "target_action": target, "assertion": ""}
        compiled, contrast = compile_pair(payload, frozen, workspace)
        if contrast["compiled"]:
            supported.append((compiled, contrast))
    if len(supported) != 1:
        return None, {**proof, "status": "ambiguous_contrast" if supported else "unsupported_or_unproven"}
    compiled, contrast = supported[0]
    control_source = (setup + "\n" + compiled["control_action"]
                      + "\n_e1c_control_done = True\nassert _e1c_control_done\n")
    control = validate_candidate(control_source, candidate["issue_quote"], frozen, workspace=workspace)
    return control, {**proof, "compiled": True, "status": "requires_two_base_control_passes",
                     "contrast": contrast, "control_sha256": control["probe_sha256"],
                     "preconditions_verified": False}
