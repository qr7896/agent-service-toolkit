"""Keep an accepted call-completion contract authoritative across fallback generation."""

from __future__ import annotations

import ast

from evals.e1c_evaluation_2_contract_method import CONTRACT_KEYS
from evals.e1c_strict_v5_boundary import audit_repair_visible_payload


def compile_fallback(source, contract, frozen):
    if set(contract) != CONTRACT_KEYS or contract.get("oracle") != "call_completes":
        return source, {"compiled": False}
    if any(not isinstance(contract[key], str) or not 8 <= len(contract[key]) <= 1500 or contract[key] not in frozen["issue"]
           for key in ("issue_quote", "expected_quote")):
        return source, {"compiled": False, "reason": "contract_quote_not_grounded"}
    tree = ast.parse(source)
    assertions = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    if len(assertions) != 1 or tree.body[-1] is not assertions[0] or any(isinstance(node, (ast.Try, ast.TryStar)) for node in ast.walk(tree)):
        return source, {"compiled": False, "reason": "unsupported_fallback_shape"}
    def name(call):
        return call.func.id if isinstance(call.func, ast.Name) else call.func.attr if isinstance(call.func, ast.Attribute) else None
    target_calls = {name(node) for node in ast.walk(ast.parse(contract["target_action"])) if isinstance(node, ast.Call)}
    previous = tree.body[-2] if len(tree.body) > 1 else None
    if not isinstance(previous, (ast.Assign, ast.Expr)) or not isinstance(previous.value, ast.Call) or name(previous.value) not in target_calls:
        return source, {"compiled": False, "reason": "no_matching_final_api_call"}
    if any(isinstance(node, ast.Name) and node.id.startswith("_e1c_fallback_") for node in ast.walk(tree)):
        raise ValueError("reserved fallback compiler name")
    prefix = "\n".join(source.splitlines()[:assertions[0].lineno - 1])
    compiled = prefix + "\n_e1c_fallback_done = True\nassert _e1c_fallback_done\n"
    actual = ast.parse(compiled)
    if ast.dump(ast.Module(body=tree.body[:-1], type_ignores=[])) != ast.dump(ast.Module(body=actual.body[:-2], type_ignores=[])):
        raise ValueError("oracle compilation changed the API program")
    proof = {"compiled": True, "oracle": "call_completes", "api_program_changed": False,
             "locked_contract_sha256": audit_repair_visible_payload({key: contract[key] for key in ("issue_quote", "expected_quote", "oracle")})}
    return compiled, proof
