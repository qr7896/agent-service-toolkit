"""Production attribute dependencies and bounded scope/exception evidence in Controller."""

from __future__ import annotations

import ast
import hashlib
import json
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from unittest.mock import patch

from evals import e1c_evaluation_2_module_retrieval_dev as previous
from evals import e1c_evaluation_2_qualification as syntax
from evals import e1c_evaluation_2_qualification_v2 as bounded
from evals import e1c_evaluation_2_reference_scope as scopes
from evals.e1c_evaluation_2_dev_pilot import _save
from evals.e1c_evaluation_2_export_chain import export_chain
from evals.e1c_evaluation_2_object_observer_v2 import constructor_bindings
from evals.e1c_evaluation_2_object_observer_v2 import observe as observe_objects
from evals.e1c_evaluation_2_public_api_windows import resolve_symbol

adapter = previous.previous.previous.stage.pilot.previous.adapter
qualified = adapter.qualified
_strict, _observe = bounded.inspect_program, qualified.observe
_current = ContextVar('source_evidence_controller_current', default=None)


def checked_source(frozen, workspace, name):
    name = qualified.assert_production_relative_path(name)
    path = qualified.assert_agent_path(workspace / name, workspace=workspace)
    exposed = [w['source_sha256'] for w in frozen['windows'] if w['path'] == name]
    if not exposed:
        return None
    if path.stat().st_size > 1_000_000:
        raise ValueError('source evidence file budget exceeded')
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if any(h != digest for h in exposed) or raw.replace(b'\r\n', b'\n') != qualified.git_blob(workspace, frozen['base_commit'], name):
        raise ValueError('exposed qualified dependency source differs from base')
    return digest


def inspect_program(payload, frozen, workspace):
    _current.set((frozen, workspace))
    result = _strict(payload, frozen, workspace)
    tree = ast.parse(payload['setup_source'] + '\n' + payload['target_action'])
    aliases = syntax.imports(tree)
    roots = {w['path'].removeprefix('src/').split('/')[0].removesuffix('.py') for w in frozen['windows']}
    seen = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        try:
            reference = syntax.canonical(syntax.expression(node.func), aliases)
        except ValueError:
            continue
        if reference.get('kind') != 'qualified_reference' or reference['name'] in seen:
            continue
        if reference['name'].split('.')[0] not in roots:
            continue  # Existing validator owns external helper rules; do not invent missing production evidence.
        seen.add(reference['name'])
        if len(seen) > 4:
            result['unknown'].append('qualified_attribute_dependency_budget_exhausted')
            break
        module, symbol = reference['name'].rsplit('.', 1)
        record = resolve_symbol(workspace, module, symbol)
        if record is None:
            result['unknown'].append('qualified_attribute_definition_unknown')
            continue
        name = record['path'].relative_to(workspace).as_posix()
        digest = checked_source(frozen, workspace, name)
        if digest is None:
            result['unexposed_dependency_bindings'].append({'module': module, 'symbol': symbol, 'path': name})
            result['unknown'].append('unexposed_dependency_source_provenance_unknown')
            continue
        item = {'alias': reference['name'], 'symbol': symbol, 'path': name, 'source_sha256': digest,
                'relation_type': 'qualified_call_dependency', 'origin': 'generated_production_call', 'depth': 1}
        if not any(b['path'] == name and b['symbol'] == symbol for b in result['production_bindings']):
            result['production_bindings'].append(item)
    result['unknown'] = sorted(set(result['unknown']))
    return result  # Existing rejections and public-scope unknowns are never cleared.


def ranked_sites(frozen, workspace, program):
    # Agent-requested production definitions first, then qualified call dependencies.
    # This changes selection, not the two-file observation cap or public-message test.
    ranked = []
    for row in frozen['windows']:
        if row.get('origin') in {'agent_module_name_hint', 'agent_requested_production'}:
            ranked.append((0, row['path']))
    for row in program['production_bindings']:
        ranked.append((1 if row.get('relation_type') == 'qualified_call_dependency' else 2, row['path']))
    sites = []
    for _, name in sorted(set(ranked)):
        if any(s['path'] == name for s in sites):
            continue
        digest = checked_source(frozen, workspace, name)
        if digest is not None:
            sites.append({'path': name, 'line': 1, 'variable': 'exception', 'source_sha256': digest})
        if len(sites) == 2:
            break
    return sites


def observe(candidate, probe, sites, image, base_commit, root, **kwargs):
    frozen, workspace = _current.get()
    payload = json.loads((root.parent / 'compiler.json').read_bytes())['canonical_contract']
    selected = ranked_sites(frozen, workspace, inspect_program(payload, frozen, workspace))
    if not selected:
        raise ValueError('no source-bound exception observation sites')
    projected, proof = qualified.project_sites(workspace, selected)
    _save(root.parent / 'source-site-selection.json', {'sites': selected, 'proofs': proof, 'cap': 2,
                                                      'manual_task_file_selection': False})
    return _observe(candidate, probe, projected, image, base_commit, root, **kwargs)


def scope_evidence(payload, frozen, workspace):
    scope = scopes.inspect_scope(payload, frozen, workspace)
    chains = [export_chain(workspace, row['conditional_binding'], frozen['base_commit']) for row in scope['scope_assumptions']][:2]
    return scope, chains


def enrich_result(result, payload, frozen, workspace, image, root, environment):
    feedback, oracle, candidate, execution = result
    selection = root / 'source-site-selection.json'
    if selection.is_file() and 'controller_verdict' in feedback:
        verdict = {**feedback['controller_verdict'], 'source_projection': json.loads(selection.read_bytes())['proofs'],
                   'diagnostic_scope': 'ranked_requested_and_qualified_call_source_files'}
        feedback = {**feedback, 'controller_verdict': verdict}
    scope, chains = scope_evidence(payload, frozen, workspace)
    _save(root / 'fixture-scope-evidence.json', {'scope': scope, 'export_chains': chains, 'old_qualification_changed': False})
    runtime = None
    if execution is not None and chains and all(row['status'] == 'static_chain_supported' for row in chains):
        bindings, sources, unknown = constructor_bindings(chains, workspace)
        if bindings and not unknown:
            actual = json.loads((root / 'candidate.json').read_bytes())
            probe = root / 'execution' / (actual['probe_sha256'] + '.py')
            blocker = root / 'execution/optional_missing' if environment['missing_optional_import'] else None
            runtime = observe_objects(actual, probe, bindings, sources, image, frozen['base_commit'],
                                      root / 'fixture-object-observation', blocked_import_dir=blocker)
    summary = {'schema': 'e1c2-controller-source-evidence-v1', 'public_scope_status': scope['status'],
               'conditional_bindings': len(scope['scope_assumptions']),
               'runtime_relationships_observed': sum(bool(r['declared_class_in_instance_mro']) for r in runtime['records']) if runtime else 0,
               'public_namespace_intent_proven': False, 'semantic_alignment_proven': False, 'trusted_reproducer': False}
    _save(root / 'controller-source-evidence-feedback.json', {**feedback, 'source_evidence': summary})
    return {**feedback, 'source_evidence': summary}, oracle, candidate, execution


@contextmanager
def configured():
    token = _current.set(None)
    try:
        with ExitStack() as stack:
            stack.enter_context(patch.object(qualified, 'inspect_program', inspect_program))
            stack.enter_context(patch.object(bounded, 'inspect_program', inspect_program))
            stack.enter_context(patch.object(qualified, 'observe', observe))
            compiled = stack.enter_context(previous.configured())
            original = compiled.configured

            @contextmanager
            def evidence_hooks():
                with original():
                    execute = compiled.base.loop.execute_probe

                    def with_evidence(payload, frozen, workspace, image, root, environment, locked=None):
                        visible = adapter.effective(frozen)
                        result = execute(payload, frozen, workspace, image, root, environment, locked)
                        return enrich_result(result, payload, visible, workspace, image, root, environment)

                    with patch.object(compiled.base.loop, 'execute_probe', with_evidence):
                        yield

            stack.enter_context(patch.object(compiled, 'configured', evidence_hooks))
            yield compiled
    finally:
        _current.reset(token)
