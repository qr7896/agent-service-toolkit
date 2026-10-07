"""Local public-version source counterfactuals, never Gold or old test inputs."""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import subprocess
import tarfile
import time
from pathlib import Path
from uuid import uuid4

from evals.e1c_blind_boundary import assert_agent_path
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import docker_command
from evals.e1c_strict_v5_boundary import assert_production_relative_path

VERSION = r'\d+\.\d+\.\d+(?:rc\d+)?'


def quoted_success_version(quote):
    versions = set(re.findall(r'(?:<=|==)\s*(' + VERSION + r')\b', quote))
    return next(iter(versions)) if len(versions) == 1 else None


def declared_version(raw):
    values = [n.value.value for n in ast.parse(raw).body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == '__version__' for t in n.targets)
              and isinstance(n.value, ast.Constant) and type(n.value.value) is str]
    return values[0] if len(values) == 1 else None


def local_snapshot(workspace, base_commit, package, version):
    init = assert_production_relative_path(package + '/__init__.py')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(workspace), *args], timeout=15)
    tags = git('tag', '--list').decode().splitlines()
    refs = [t for t in tags if t.removeprefix('v') == version]
    commits = [git('rev-parse', ref + '^{commit}').decode().strip() for ref in refs]
    if not commits:
        commits = git('log', '-n', '80', '--format=%H', base_commit, '--', init).decode().splitlines()
    deadline = time.monotonic() + 90
    for commit in dict.fromkeys(commits):
        if time.monotonic() > deadline:
            return None
        try:
            raw = git('show', commit + ':' + init)
        except subprocess.CalledProcessError:
            continue  # A historical rename/delete is unavailable source, not a probe failure.
        if declared_version(raw) != version:
            continue
        ancestor = subprocess.run(['git', '-C', str(workspace), 'merge-base', '--is-ancestor', commit, base_commit],
                                  capture_output=True, timeout=15, check=False)
        if ancestor.returncode == 0:
            return {'commit': commit, 'version': version, 'package': package, 'init_sha256': hashlib.sha256(raw).hexdigest()}
    return None


def materialize(workspace, snapshot, destination):
    if destination.exists():
        raise FileExistsError('historical production snapshot already exists')
    archive = subprocess.check_output(['git', '-C', str(workspace), '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
                                       'archive', '--format=tar', snapshot['commit'], snapshot['package']], timeout=30)
    if len(archive) > 4_000_000:
        raise ValueError('bounded pure production archive required')
    files = []
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            if not member.name.endswith('.py'):
                continue
            name = assert_production_relative_path(member.name)
            if not member.isfile() or member.size > 1_000_000 or not name.startswith(snapshot['package'] + '/'):
                raise ValueError('regular bounded production Python sources required')
            path = assert_agent_path(destination / name, workspace=destination)
            raw = tar.extractfile(member).read()
            canonical = subprocess.check_output(['git', '-C', str(workspace), 'show', snapshot['commit'] + ':' + name], timeout=15)
            if raw != canonical:
                raise ValueError('historical archive bytes differ from canonical Git blob')
            files.append((path, raw, {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}))
    if not 1 <= len(files) <= 64 or sum(len(raw) for _, raw, _ in files) > 2_000_000:
        raise ValueError('bounded historical package source inventory required')
    for path, raw, _ in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return [proof for _, _, proof in files]


def audit_dev():
    from evals.e1c_evaluation_2_container_health import require_engine
    from evals.e1c_evaluation_2_issue_input import SOURCE
    from evals.e1c_evaluation_2_issue_quote_refs import resolve

    out = ROOT / '.codex/e1c/evaluation_2/version-witness-zero-v1'
    if out.exists():
        raise FileExistsError('version witness already started; no replay')
    old = ROOT / '.codex/e1c/evaluation_2/report-anchor-reference-dev-v1'
    seal = json.loads((old / 'generation-seal.json').read_bytes())
    if _sha(old / 'generation-seal.json') != '5997675327f8f246b179413f0c2df5efd2b66fd2edacc2f6db430796588ea86f':
        raise ValueError('original producer seal changed')
    for name, digest in seal['files'].items():
        if _sha(assert_agent_path(old / name, workspace=old)) != digest:
            raise ValueError('original producer artifact changed')
    selected = {r['instance_id']: r['selected_turn'] for r in json.loads((old / 'state.json').read_bytes())['rows']}
    behavior = ROOT / '.codex/e1c/evaluation_2/behavior-gate-zero-v1/result.json'
    kinds = {r['instance_id']: r['expectation_origin'] for r in json.loads(behavior.read_bytes())['rows']}
    _save(out / 'freeze.json', {'provider_calls': 0, 'Gold_read': False, 'module_sha256': _sha(Path(__file__)),
                              'behavior_result_sha256': _sha(behavior), 'original_seal_sha256': _sha(old / 'generation-seal.json'),
                              'protocol_sha256': _sha(ROOT / 'docs/research/E1C2_VERSION_WITNESS_V1_PROTOCOL_2026-10-08.md')})
    rows = []
    for task in json.loads((old / 'freeze.json').read_bytes())['tasks']:
        iid = task['instance_id']
        if kinds[iid] != 'regression_report':
            rows.append({'instance_id': iid, 'status': 'not_applicable'})
            continue
        turn = old / iid / f"turn-{selected[iid]}"
        frozen = json.loads((turn / 'input.json').read_bytes())
        payload = json.loads(json.loads((turn / 'response.json').read_bytes())['raw'])['probe']
        if 'expected_quote_ref' in payload:
            payload, _ = resolve(payload, frozen['issue'])
        version = quoted_success_version(payload['expected_quote'])
        packages = {r['path'].removeprefix('src/').split('/')[0] for r in frozen['windows'] if '/' in r['path']}
        if not version or len(packages) != 1:
            rows.append({'instance_id': iid, 'status': 'unknown_version_or_package'})
            continue
        module = packages.pop()
        package = ('src/' if (SOURCE / iid / 'src' / module / '__init__.py').is_file() else '') + module
        snapshot = local_snapshot(SOURCE / iid, frozen['base_commit'], package, version)
        if not snapshot:
            rows.append({'instance_id': iid, 'status': 'local_old_source_unavailable', 'version': version})
            continue
        root = out / iid
        sources = materialize(SOURCE / iid, snapshot, root / 'source')
        candidate = json.loads((old / iid / 'candidate.json').read_bytes())
        probe = old / iid / 'execution' / (candidate['probe_sha256'] + '.py')
        if _sha(probe) != candidate['probe_sha256']:
            raise ValueError('original probe changed')
        require_engine((task['image_id'],))
        marker = 'E1C2_VERSION_' + uuid4().hex + '='
        parent = package.rsplit('/', 1)[0] if '/' in package else ''
        old_prefix = '/e1c2_old' + ('/' + parent if parent else '')
        data = {'files': sources, 'probe_sha256': candidate['probe_sha256'], 'module': module, 'version': version, 'marker': marker}
        driver = "import hashlib, importlib, json, runpy\nDATA = json.loads(" + repr(json.dumps(data)) + ")\n" + '''for source in DATA['files']:
    if hashlib.sha256(open('/e1c2_old/' + source['path'], 'rb').read()).hexdigest() != source['sha256']:
        raise RuntimeError('historical production source changed')
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
        driver_path = root / 'driver.py'
        driver_path.write_bytes(driver.encode())
        missing = task['environment']['missing_optional_import']
        blocker = old / iid / 'execution/optional_missing' if missing else None
        if missing and (blocker / (missing + '.py')).read_bytes() != f"raise ModuleNotFoundError(\"No module named '{missing}'\")\n".encode():
            raise ValueError('original optional dependency blocker changed')
        command = docker_command({'probe_sha256': _sha(driver_path), 'input_sha256': candidate['input_sha256']}, task['image_id'], frozen['base_commit'], driver_path,
                                 blocked_import_dir=blocker)
        index = command.index(task['image_id'])
        command[index:index] = ['--mount', f'type=bind,source={(root / "source").resolve()},target=/e1c2_old,readonly',
                                '--mount', f'type=bind,source={probe.resolve()},target=/e1c2_model_probe.py,readonly']
        position = next(i for i, value in enumerate(command) if value.startswith('PYTHONPATH='))
        command[position] = 'PYTHONPATH=' + ('/e1c2_optional_missing:' if missing else '') + old_prefix + ':/testbed/src:/testbed'
        _save(root / 'freeze.json', {'snapshot': snapshot, 'sources': sources, 'original_probe_sha256': candidate['probe_sha256'],
                                   'image': task['image_id'], 'base_commit': frozen['base_commit'], 'driver_sha256': _sha(driver_path), 'provider_calls': 0})
        with (root / 'run.log').open('xb') as log:
            try:
                run = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False)
            except subprocess.TimeoutExpired:
                subprocess.run(['docker', 'rm', '-f', command[command.index('--name') + 1]], capture_output=True, timeout=30, check=False)
                raise RuntimeError('old-version diagnostic timeout; no retry') from None
        lines = [line[len(marker):] for line in (root / 'run.log').read_text(encoding='utf-8', errors='replace').splitlines() if line.startswith(marker)]
        verified = len(lines) == 1 and json.loads(lines[0]).get('old_library_version_verified') is True
        status = ('infra_blocked' if run.returncode in {90, 125, 126, 127} else
                  'version_or_import_preflight_invalid' if not verified else
                  'old_version_same_probe_completed' if run.returncode == 0 else 'old_version_probe_failed')
        rows.append({'instance_id': iid, 'status': status,
                     'version': version, 'snapshot_commit': snapshot['commit'], 'returncode': run.returncode, 'version_checked': verified,
                     'log_sha256': _sha(root / 'run.log'), 'source_file_count': len(sources), 'source_bytes': sum((root / 'source' / s['path']).stat().st_size for s in sources),
                     'original_probe_sha256': candidate['probe_sha256'], 'trusted_reproducer': False})
    value = {'rows': rows, 'provider_calls': 0, 'provider_tokens': 0, 'Gold_read': False, 'machine_trusted': 0,
             'no_downloads': True, 'cached_reference_denominator': len(rows), 'fixed_DEV_denominator': 12, 'old_qualification_changed': False}
    _save(out / 'result.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('audit-dev',))
    parser.parse_args()
    print(json.dumps(audit_dev(), ensure_ascii=False), flush=True)
