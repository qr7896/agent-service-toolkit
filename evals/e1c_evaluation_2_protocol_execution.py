"""Guard compiler-induced control binding loss before any container execution."""

from __future__ import annotations

import ast

from evals.e1c_evaluation_2_source_contract import rephase_setup


def bindings(statements):
    result = set()
    for node in statements:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            result.update(child.id for target in targets for child in ast.walk(target)
                          if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            result.update(alias.asname or alias.name.split('.')[0] for alias in node.names)
    return result


def validate_frontier(payload, frozen, workspace):
    shifted, proof = rephase_setup(payload, frozen, workspace)
    if proof['moved_from_line'] is None:
        return {'compiler_removed_control_bindings': [], 'changed_probe': False}
    removed = bindings(ast.parse(payload['setup_source']).body) - bindings(ast.parse(shifted['setup_source']).body)
    for statement in ast.parse(payload['control_action']).body:
        # Deliberately conservative: complex control flow does not earn binding proof.
        used = {node.id for node in ast.walk(statement) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
        missing = sorted(used & removed)
        if missing:
            raise ValueError('compiler_frontier_removes_control_binding:' + ','.join(missing)
                             + '; shared setup must use base-supported APIs; construct target-only unsupported '
                             'configuration inside target_action and an independent supported receiver in control_action')
        removed -= bindings([statement])
    return {'compiler_removed_control_bindings': sorted(removed), 'changed_probe': False}
