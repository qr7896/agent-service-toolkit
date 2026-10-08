"""Resume only a source-prepared probe that never reached engine admission."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import docker_command
from evals.e1c_strict_v5_boundary import assert_production_relative_path


def require_unstarted(root, failure):
    if failure.get('status') != 'INFRA_BLOCKED' or failure.get('phase') != 'after_materialization_before_engine_admission':
        raise ValueError('only pre-engine infrastructure interruption can resume')
    if (type(failure.get('diagnostic_containers_started')) is not int or failure['diagnostic_containers_started'] != 0
            or failure.get('driver_created') is not False or failure.get('task_freeze_created') is not False):
        raise ValueError('a started probe cannot resume')
    task = assert_agent_path(root / failure['instance_id'], workspace=root)
    if any((task / name).exists() for name in ('driver.py', 'freeze.json', 'run.log', 'result.json')):
        raise ValueError('runtime artifact exists; continuation would replay a probe')
    source = task / 'source'
    expected = {r['path']: r['sha256'] for r in failure['source_files']}
    if not 1 <= len(expected) <= 64 or len(expected) != len(failure['source_files']):
        raise ValueError('bounded unique source inventory required')
    actual = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
    if actual != set(expected):
        raise ValueError('prepared source inventory differs')
    for name, digest in expected.items():
        assert_production_relative_path(name)
        if _sha(assert_agent_path(source / name, workspace=source)) != digest:
            raise ValueError('prepared source bytes differ')
    return source


def build_driver(probe_sha, files, module, version, marker):
    if not re.fullmatch(r'[0-9a-f]{64}', probe_sha) or not re.fullmatch(r'[A-Za-z_]\w{0,99}', module):
        raise ValueError('bounded original probe/module identity required')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:rc\d+)?', version) or not re.fullmatch(r'E1C2_VERSION_[0-9a-f]{32}=', marker):
        raise ValueError('bounded public version/nonce required')
    data = {'probe_sha256': probe_sha, 'files': files, 'module': module, 'version': version, 'marker': marker}
    return "import hashlib, importlib, json, runpy\nDATA = json.loads(" + repr(json.dumps(data)) + ")\n" + '''for source in DATA['files']:
    if hashlib.sha256(open('/e1c2_old/' + source['path'], 'rb').read()).hexdigest() != source['sha256']:
        raise RuntimeError('prepared historical production source changed')
if hashlib.sha256(open('/e1c2_model_probe.py', 'rb').read()).hexdigest() != DATA['probe_sha256']:
    raise RuntimeError('original model probe changed')
module = importlib.import_module(DATA['module'])
if module.__dict__.get('__version__') != DATA['version'] or not module.__dict__.get('__file__', '').startswith('/e1c2_old/'):
    raise RuntimeError('actual historical library version/path differs')
try:
    runpy.run_path('/e1c2_model_probe.py', run_name='__main__')
finally:
    print(DATA['marker'] + json.dumps({'old_library_version_verified': True, 'probe_source_unchanged': True}))
'''


def run():
    out = ROOT / '.codex/e1c/evaluation_2/version-witness-resume-zero-v1'
    if out.exists():
        raise FileExistsError('resume identity already started; no replay')
    interrupted = ROOT / '.codex/e1c/evaluation_2/version-witness-zero-v1'
    receipt = json.loads((ROOT / 'data/e1c_evaluation_2_behavior_version_results.json').read_bytes())
    for kind in ('freeze', 'failure'):
        if _sha(interrupted / (kind + '.json')) != receipt['source_records']['version-witness-zero-v1'][kind + '_sha256']:
            raise ValueError('original interruption receipt differs')
    failure = json.loads((interrupted / 'failure.json').read_bytes())
    old_sources = require_unstarted(interrupted, failure)
    old = ROOT / '.codex/e1c/evaluation_2/report-anchor-reference-dev-v1'
    seal = json.loads((old / 'generation-seal.json').read_bytes())
    if _sha(old / 'generation-seal.json') != json.loads((interrupted / 'freeze.json').read_bytes())['original_seal_sha256']:
        raise ValueError('original producer seal changed')
    for name, digest in seal['files'].items():
        if _sha(assert_agent_path(old / name, workspace=old)) != digest:
            raise ValueError('original producer artifact changed')
    iid = failure['instance_id']
    tasks = json.loads((old / 'freeze.json').read_bytes())['tasks']
    task = next(t for t in tasks if t['instance_id'] == iid)
    selected = next(r['selected_turn'] for r in json.loads((old / 'state.json').read_bytes())['rows'] if r['instance_id'] == iid)
    frozen = json.loads((old / iid / f'turn-{selected}' / 'input.json').read_bytes())
    candidate = json.loads((old / iid / 'candidate.json').read_bytes())
    probe = old / iid / 'execution' / (candidate['probe_sha256'] + '.py')
    if _sha(probe) != candidate['probe_sha256']:
        raise ValueError('original probe bytes differ')
    packages = {r['path'].removeprefix('src/').split('/')[0] for r in failure['source_files']}
    if len(packages) != 1:
        raise ValueError('unique prepared package required')
    module = packages.pop()
    prefix = '/e1c2_old/src' if (old_sources / 'src' / module / '__init__.py').is_file() else '/e1c2_old'
    require_engine((task['image_id'],))
    _save(out / 'freeze.json', {'module_sha256': _sha(Path(__file__)), 'provider_calls': 0, 'Gold_read': False,
                              'protocol_sha256': _sha(ROOT / 'docs/research/E1C2_VERSION_RESUME_V1_PROTOCOL_2026-10-08.md'),
                              'original_failure_sha256': _sha(interrupted / 'failure.json'), 'original_freeze_sha256': _sha(interrupted / 'freeze.json'),
                              'instance_id': iid, 'sources': failure['source_files'], 'probe_sha256': candidate['probe_sha256'],
                              'image': task['image_id'], 'base_commit': frozen['base_commit'], 'old_version': failure['public_old_version']})
    marker = 'E1C2_VERSION_' + uuid4().hex + '='
    driver = out / 'driver.py'
    driver.write_bytes(build_driver(candidate['probe_sha256'], failure['source_files'], module, failure['public_old_version'], marker).encode())
    missing = task['environment']['missing_optional_import']
    blocker = old / iid / 'execution/optional_missing' if missing else None
    if missing and (blocker / (missing + '.py')).read_bytes() != f"raise ModuleNotFoundError(\"No module named '{missing}'\")\n".encode():
        raise ValueError('original optional blocker changed')
    command = docker_command({'probe_sha256': _sha(driver), 'input_sha256': candidate['input_sha256']}, task['image_id'], frozen['base_commit'], driver,
                             blocked_import_dir=blocker)
    index = command.index(task['image_id'])
    command[index:index] = ['--mount', f'type=bind,source={old_sources.resolve()},target=/e1c2_old,readonly',
                            '--mount', f'type=bind,source={probe.resolve()},target=/e1c2_model_probe.py,readonly']
    position = next(i for i, value in enumerate(command) if value.startswith('PYTHONPATH='))
    command[position] = 'PYTHONPATH=' + ('/e1c2_optional_missing:' if missing else '') + prefix + ':/testbed/src:/testbed'
    _save(out / 'started.json', {'driver_sha256': _sha(driver), 'container_name': command[command.index('--name') + 1], 'provider_calls': 0})
    with (out / 'run.log').open('xb') as log:
        try:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'rm', '-f', command[command.index('--name') + 1]], capture_output=True, timeout=30, check=False)
            _save(out / 'failure.json', {'status': 'TIMEOUT', 'provider_calls': 0, 'no_retry': True})
            raise RuntimeError('resumed diagnostic timeout; no retry') from None
    lines = [line[len(marker):] for line in (out / 'run.log').read_text(encoding='utf-8', errors='replace').splitlines() if line.startswith(marker)]
    verified = len(lines) == 1 and json.loads(lines[0]).get('old_library_version_verified') is True
    status = ('INFRA_BLOCKED' if completed.returncode in {90, 125, 126, 127} else 'VERSION_PREFLIGHT_INVALID' if not verified else
              'old_version_same_probe_completed' if completed.returncode == 0 else 'old_version_probe_failed')
    result = {'status': status, 'instance_id': iid, 'returncode': completed.returncode, 'old_version_checked': verified,
              'old_version': failure['public_old_version'], 'log_sha256': _sha(out / 'run.log'), 'freeze_sha256': _sha(out / 'freeze.json'),
              'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'machine_trusted': 0, 'new_probes_generated': 0,
              'cached_reference_denominator': len(tasks), 'fixed_DEV_denominator': 12, 'original_interruption_modified': False,
              'old_scores_or_qualification_changed': False, 'no_source_rematerialization': True, 'network_none': True, 'pull_never': True}
    _save(out / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('run',))
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False), flush=True)
