"""Pinned public-release source counterfactual; no installation or provider calls."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import stat
import subprocess
import zipfile
from pathlib import PurePosixPath
from uuid import uuid4

from evals import e1c_evaluation_2_source_evidence_zero as previous
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import docker_command
from evals.e1c_evaluation_2_version_witness import declared_version, quoted_success_version
from evals.e1c_strict_v5_boundary import assert_production_relative_path

MODULE, VERSION = 'marshmallow', '2.19.3'
WHEEL_SHA = 'cb1e88b8b098ee6d0fb984e40762cb94e200c067426e43496e55b82b563feabf'
WHEEL_BYTES = 49981
WHEEL = ROOT / '.codex/e1c/evaluation_2/public-version-source/marshmallow-2.19.3/marshmallow-2.19.3-py2.py3-none-any.whl'
OUT = ROOT / '.codex/e1c/evaluation_2/public-release-witness-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_RELEASE_WITNESS_ZERO_2026-10-08.md'


def production_sources(raw, module=MODULE, version=VERSION):
    if len(raw) > 1_000_000:
        raise ValueError('archive byte budget exceeded')
    output, seen, total = {}, set(), 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for item in archive.infolist():
            name = item.orig_filename  # ZipInfo normalizes Windows backslashes; validate the raw archive spelling.
            path = PurePosixPath(name)
            if ('\\' in name or ':' in name or path.is_absolute() or '..' in path.parts or not path.parts
                    or name.rstrip('/') != path.as_posix()):
                raise ValueError('unsafe archive path')
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError('archive symlink rejected')
            if item.is_dir() or not name.startswith(module + '/') or not name.endswith('.py'):
                continue  # Metadata and outside-package entries are not read or executed.
            assert_production_relative_path(name)  # Test paths inside the package are rejected.
            if name.casefold() in seen:
                raise ValueError('duplicate archive path')
            seen.add(name.casefold())
            total += item.file_size
            if len(seen) > 64 or item.file_size > 1_000_000 or total > 2_000_000:
                raise ValueError('production source budget exceeded')
            output[name] = archive.read(item)
    if not output or declared_version(output.get(module + '/__init__.py', b'')) != version:
        raise ValueError('archive production version differs')
    return output


DRIVER = '''import hashlib, importlib, json, runpy
for source in DATA['sources']:
    if hashlib.sha256(open('/e1c2_release/' + source['path'], 'rb').read()).hexdigest() != source['sha256']:
        raise RuntimeError('public release source differs')
if hashlib.sha256(open('/e1c2_model_probe.py', 'rb').read()).hexdigest() != DATA['probe_sha256']:
    raise RuntimeError('sealed probe differs')
module = importlib.import_module(DATA['module'])
if module.__dict__.get('__version__') != DATA['version'] or not module.__dict__.get('__file__', '').startswith('/e1c2_release/' + DATA['module'] + '/'):
    raise RuntimeError('release version/path preflight differs')
if DATA['missing_optional_import']:
    try:
        importlib.import_module(DATA['missing_optional_import'])
    except ModuleNotFoundError:
        pass
    else:
        raise RuntimeError('enforced import failure absent')
print(DATA['marker'] + json.dumps({'release_version_path_verified': True, 'probe_source_unchanged': True,
    'same_enforced_optional_condition': True}), flush=True)
runpy.run_path('/e1c2_model_probe.py', run_name='__main__')
'''


def classify(returncode, log, marker):
    reports = [json.loads(line[len(marker):]) for line in log.splitlines() if line.startswith(marker)]
    verified = len(reports) == 1 and all(reports[0].get(k) is True for k in
        ('release_version_path_verified', 'probe_source_unchanged', 'same_enforced_optional_condition'))
    status = ('infra_blocked' if returncode in (90, 125, 126, 127) else 'invalid_release_preflight' if not verified else
              'same_probe_completed' if returncode == 0 else 'same_probe_failed')
    return {'status': status, 'returncode': returncode, 'release_preflight_verified': verified}


def execute(candidate, probe, task, frozen, sources, source_root, blocker, root):
    if candidate.get('safe_static_check') is not True or _sha(probe) != candidate['probe_sha256']:
        raise ValueError('sealed validated probe required')
    require_engine((task['image_id'],))
    data = {'module': MODULE, 'version': VERSION, 'sources': sources, 'probe_sha256': candidate['probe_sha256'],
            'missing_optional_import': task['environment']['missing_optional_import'], 'marker': 'E1C2_RELEASE_' + uuid4().hex + '='}
    driver = 'import json\nDATA = json.loads(' + repr(json.dumps(data)) + ')\n' + DRIVER
    ast.parse(driver)
    _save(root / 'freeze.json', {'data': data, 'driver_sha256': hashlib.sha256(driver.encode()).hexdigest(),
                               'image': task['image_id'], 'base_commit': frozen['base_commit'], 'provider_calls': 0})
    path = root / 'driver.py'
    path.write_bytes(driver.encode())
    command = docker_command({'probe_sha256': _sha(path), 'input_sha256': candidate['input_sha256']},
                             task['image_id'], frozen['base_commit'], path, blocked_import_dir=blocker)
    index = command.index(task['image_id'])
    command[index:index] = ['--mount', f'type=bind,source={source_root.resolve()},target=/e1c2_release,readonly',
                            '--mount', f'type=bind,source={probe.resolve()},target=/e1c2_model_probe.py,readonly']
    position = next(i for i, value in enumerate(command) if value.startswith('PYTHONPATH='))
    command[position] = 'PYTHONPATH=' + ('/e1c2_optional_missing:' if blocker else '') + '/e1c2_release:/testbed/src:/testbed'
    with (root / 'run.log').open('xb') as log:
        try:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', command[command.index('--name') + 1]], capture_output=True, timeout=30, check=False)
            raise RuntimeError('release witness timeout; no retry') from None
    value = {**classify(completed.returncode, (root / 'run.log').read_text(encoding='utf-8', errors='replace'), data['marker']),
             'log_sha256': _sha(root / 'run.log'), 'provider_calls': 0, 'network_none': True, 'read_only': True,
             'probe_sha256': candidate['probe_sha256']}
    _save(root / 'result.json', value)
    print(json.dumps({'run': root.name, **value}), flush=True)
    return value


def run():
    if OUT.exists():
        raise FileExistsError('release witness started; no retry')
    if WHEEL.stat().st_size != WHEEL_BYTES or _sha(WHEEL) != WHEEL_SHA:
        raise ValueError('downloaded public wheel identity differs')
    inventory = production_sources(WHEEL.read_bytes())  # No import/setup/installation on host.
    receipt = json.loads((ROOT / 'data/e1c_evaluation_2_source_evidence_results.json').read_bytes())
    if any(_sha(ROOT / '.codex/e1c/evaluation_2' / name) != digest for name, digest in receipt['source_records'].items()):
        raise ValueError('parent zero evidence changed')
    parent = json.loads((previous.OUT / 'freeze.json').read_bytes())
    if any(_sha(ROOT / name) != digest for name, digest in parent['modules'].items()):
        raise ValueError('parent zero method differs')
    source_parent = previous.PARENT
    seal = json.loads((source_parent / 'generation-seal.json').read_bytes())
    if any(_sha(source_parent / name) != digest for name, digest in seal['files'].items()):
        raise ValueError('original generated source changed')
    tasks = json.loads((source_parent / 'freeze.json').read_bytes())['tasks']
    selected = []
    for task in tasks:
        folder = previous.OUT / task['instance_id']
        payload = json.loads((folder / 'compiler.json').read_bytes())['canonical_contract']
        if quoted_success_version(payload['expected_quote']) == VERSION:
            frozen = json.loads((folder / 'effective-input.json').read_bytes())
            roots = {w['path'].removeprefix('src/').split('/')[0] for w in frozen['windows']}
            if roots == {MODULE}:
                selected.append((task, folder, frozen))
    if len(selected) != 1:
        raise ValueError('one source with exact publicly quoted success version/package required')
    task, folder, frozen = selected[0]
    original_turn = sorted((source_parent / task['instance_id']).glob('turn-*/compiler.json'))[-1].parent
    for name in ('candidate.json', 'control_candidate.json'):
        if json.loads((folder / name).read_bytes())['probe_sha256'] != json.loads((original_turn / name).read_bytes())['probe_sha256']:
            raise ValueError('counterfactual probe differs from sealed generation')
    baseline = [json.loads((folder / f'control-{n}.json').read_bytes()) for n in (1, 2)]
    target_baseline = json.loads((folder / 'execution.json').read_bytes())
    if (any(len(c['runs']) != 1 or c['runs'][0]['returncode'] != 0 or c['runs'][0]['timed_out'] for c in baseline)
            or len(target_baseline['runs']) != 2
            or any(r['returncode'] != 1 or r['timed_out'] for r in target_baseline['runs'])):
        raise ValueError('two valid cached normal passes and target failures required')
    missing = task['environment']['missing_optional_import']
    blocker = folder / 'execution/optional_missing' if missing else None
    if missing and (blocker / (missing + '.py')).read_bytes() != f"raise ModuleNotFoundError(\"No module named '{missing}'\")\n".encode():
        raise ValueError('original dependency blocker differs')
    files = [{'path': name, 'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in sorted(inventory.items())]
    _save(OUT / 'freeze.json', {'module_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_release_witness.py'),
                              'protocol_sha256': _sha(PROTOCOL), 'wheel_sha256': WHEEL_SHA, 'sources': files,
                              'parent_zero_result_sha256': _sha(previous.OUT / 'result.json'),
                              'original_generation_seal_sha256': _sha(source_parent / 'generation-seal.json'),
                              'cached_baseline_sha256': {name: _sha(folder / name) for name in ('control-1.json', 'control-2.json', 'execution.json')},
                              'selected_task': task['instance_id'], 'provider_calls': 0, 'Gold_read': False})
    source_root = OUT / 'source'
    for name, raw in inventory.items():
        path = source_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    rows = []
    try:
        for phase in ('control', 'target'):
            candidate = json.loads((folder / ('control_candidate.json' if phase == 'control' else 'candidate.json')).read_bytes())
            directory = 'control-1' if phase == 'control' else 'execution'
            probe = folder / directory / (candidate['probe_sha256'] + '.py')
            for n in (1, 2):
                result = execute(candidate, probe, task, frozen, files, source_root, blocker, OUT / f'{phase}-{n}')
                if not result['release_preflight_verified'] or result['status'] == 'infra_blocked':
                    raise RuntimeError('release witness infrastructure/preflight invalid; no retry')
                rows.append({'phase': phase, **result})
    except Exception as exc:
        _save(OUT / 'failure.json', {'error_type': type(exc).__name__, 'provider_calls': 0, 'no_retry': True})
        raise
    value = {'schema': 'e1c2-public-release-counterfactual-v1', 'version': VERSION, 'rows': rows,
             'old_version_same_probe_completed': all(r['returncode'] == 0 for r in rows),
             'cached_base_normal_returncodes': [0, 0], 'cached_base_target_returncodes': [1, 1],
             'provider_calls': 0, 'Gold_read': False, 'new_model_generation': False, 'wheel_installed_on_host': False,
             'canonical_git_snapshot_claimed': False, 'full_issue_trusted': False, 'public_namespace_intent_proven': False}
    _save(OUT / 'result.json', value)
    return value


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False), flush=True)
