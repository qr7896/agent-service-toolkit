"""Public-anchor temporal boundary mutations; compare base, retained patch and public release."""

from __future__ import annotations

import ast
import copy
import json
import re
import subprocess

from evals import e1c_evaluation_2_patch_probe_zero as probes
from evals import e1c_evaluation_2_three_arm_decode_audit as audit
from evals import e1c_evaluation_2_three_arm_dev as repair
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import docker_command
from evals.e1c_evaluation_2_release_witness import OUT as RELEASE

OUT = ROOT / '.codex/e1c/evaluation_2/public-temporal-boundary-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_PUBLIC_BOUNDARY_SWEEP_ZERO_2026-10-08.md'
ISO_LITERAL = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?Z$')


def variants(source, issue):
    tree = ast.parse(source)
    anchors = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
               and ISO_LITERAL.fullmatch(n.value) and n.value in issue}
    if len(anchors) != 1:
        raise ValueError('one ISO literal explicitly present in public issue required')
    anchor = anchors.pop()
    prefix, fraction = ISO_LITERAL.fullmatch(anchor).groups()
    digits = ((fraction or '0') * 6)[:6]
    result = []
    for precision in range(7):
        for zone in ('Z', '+00:00', '-04:30'):
            value = prefix + ('.' + digits[:precision] if precision else '') + zone
            changed = copy.deepcopy(tree)
            for node in ast.walk(changed):
                if isinstance(node, ast.Constant) and node.value == anchor:
                    node.value = value
            result.append({'id': f'p{precision}-z{len(result) % 3}', 'precision': precision, 'zone': zone,
                           'source': ast.unparse(changed) + '\n', 'synthetic_variant_not_reported_literal': value != anchor})
    return anchor, result


def release_identity(frozen, result, receipt):
    if (frozen['wheel_sha256'] != receipt['wheel_sha256'] or result['version'] != receipt['version']
            or not all(s['path'].startswith(receipt['module'] + '/') for s in frozen['sources'])):
        raise ValueError('public release identities disagree')
    return {**frozen, 'module': receipt['module'], 'version': result['version']}


DRIVER = '''import hashlib, importlib, json, subprocess, sys
for item in DATA['sources']:
    if hashlib.sha256(open('/old_release/' + item['path'], 'rb').read()).hexdigest() != item['sha256']:
        raise RuntimeError('public release source differs')
module = importlib.import_module(DATA['module'])
if not module.__file__.startswith(DATA['expected_module_prefix']):
    raise RuntimeError('actual module import path differs')
if DATA['version'] and module.__version__ != DATA['version']:
    raise RuntimeError('actual release version differs')
if DATA['missing_optional_import']:
    try:
        importlib.import_module(DATA['missing_optional_import'])
    except ModuleNotFoundError:
        pass
    else:
        raise RuntimeError('enforced optional import failure absent')
for item in DATA['variants']:
    path = '/public_variants/' + item['id'] + '.py'
    if hashlib.sha256(open(path, 'rb').read()).hexdigest() != item['sha256']:
        raise RuntimeError('public variant source differs')
    run = subprocess.run([sys.executable, '-X', 'utf8', path], capture_output=True, timeout=10)
    print('E1C2_PUBLIC_VARIANT=' + json.dumps({'id': item['id'], 'returncode': run.returncode,
        'stderr': run.stderr.decode('utf-8', errors='replace')[-4000:], 'actual_module_path_verified': True,
        'actual_release_version_verified': bool(DATA['version'])}), flush=True)
'''


def run():
    if OUT.exists():
        raise FileExistsError('public temporal sweep started; no retry')
    frozen = repair._read(repair.OUT / 'freeze.json')
    if frozen != repair.preflight():
        raise ValueError('original method changed')
    repair.verify_seal(repair.OUT)
    repair.verify_seal(audit.OUT)
    if not repair._read(probes.OUT / 'result.json')['unchanged_public_target_completed']:
        raise ValueError('completed public patch target witness required')
    cells = [a for a in repair.ARMS if repair._read(audit.OUT / a / 'generation.json')['status'] == 'candidate']
    if len(cells) != 1:
        raise ValueError('one sealed patch required')
    candidate_patch = audit.OUT / cells[0] / 'candidate.patch'
    origin = repair.source.OUT / frozen['instance_id']
    candidate = repair._read(origin / 'candidate.json')
    body = repair._read(repair.OUT / cells[0] / 'input.json')
    anchor, rows = variants(candidate['source'], body['issue'])
    roots = {w['path'].removeprefix('src/').split('/')[0] for w in body['production_windows']}
    release = release_identity(repair._read(RELEASE / 'freeze.json'), repair._read(RELEASE / 'result.json'),
                               repair._read(ROOT / 'data/e1c_evaluation_2_release_witness_results.json'))
    if len(roots) != 1 or roots != {release['module']}:
        raise ValueError('one package with bound public release required')
    missing = next(t for t in repair._read(repair.source.PARENT / 'freeze.json')['tasks']
                   if t['instance_id'] == frozen['instance_id'])['environment']['missing_optional_import']
    blocker = origin / 'execution/optional_missing' if missing else None
    require_engine((frozen['image_id'],))
    for source in release['sources']:
        if _sha(RELEASE / 'source' / source['path']) != source['sha256']:
            raise ValueError('public release source changed')
    bindings = {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
        candidate_patch, origin / 'candidate.json', RELEASE / 'freeze.json', RELEASE / 'result.json',
        probes.OUT / 'result.json', ROOT / 'evals/e1c_evaluation_2_public_precision_sweep.py', PROTOCOL)}
    if missing:
        stub = blocker / (missing + '.py')
        if stub.read_bytes() != f"raise ModuleNotFoundError(\"No module named '{missing}'\")\n".encode():
            raise ValueError('dependency blocker changed')
        bindings[stub.relative_to(ROOT).as_posix()] = _sha(stub)
    _save(OUT / 'freeze.json', {'bindings': bindings, 'provider_calls': 0, 'new_model_generation': False,
        'anchor': anchor, 'operator': 'public-ISO-literal-fraction-0-to-6-and-source-temporal-offset-family',
        'variant_count': 21, 'synthetic_not_independent_tasks': True, 'status_not_full_value_equivalence': True})
    directory = OUT / 'variants'
    directory.mkdir()
    for row in rows:
        with (directory / (row['id'] + '.py')).open('xb') as handle:
            handle.write(row['source'].encode())
    phase_rows = {}
    for phase in ('base', 'patch', 'release'):
        data = {'variants': [{'id': row['id'], 'sha256': _sha(directory / (row['id'] + '.py'))} for row in rows],
                'module': release['module'], 'version': release['version'] if phase == 'release' else None,
                'sources': release['sources'] if phase == 'release' else [], 'missing_optional_import': missing,
                'expected_module_prefix': '/old_release/' if phase == 'release' else '/testbed/'}
        driver = OUT / (phase + '-driver.py')
        with driver.open('xb') as handle:
            handle.write(('import json\nDATA = json.loads(' + repr(json.dumps(data)) + ')\n' + DRIVER).encode())
        descriptor = {'probe_sha256': _sha(driver)}
        command = (probes.patch_command(descriptor, frozen['image_id'], frozen['base_commit'], driver, candidate_patch, blocker)
                   if phase == 'patch' else docker_command(descriptor, frozen['image_id'], frozen['base_commit'], driver,
                                                         blocked_import_dir=blocker))
        index = command.index(frozen['image_id'])
        command[index:index] = ['--mount', f'type=bind,source={directory.resolve()},target=/public_variants,readonly']
        if phase == 'release':
            index = command.index(frozen['image_id'])
            command[index:index] = ['--mount', f'type=bind,source={(RELEASE / "source").resolve()},target=/old_release,readonly']
            position = next(n for n, value in enumerate(command) if value.startswith('PYTHONPATH='))
            command[position] = 'PYTHONPATH=' + ('/e1c2_optional_missing:' if blocker else '') + '/old_release:/testbed/src:/testbed'
        log_path = OUT / (phase + '.log')
        with log_path.open('xb') as log:
            try:
                rc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False).returncode
            except subprocess.TimeoutExpired:
                subprocess.run(['docker', 'rm', '-f', command[command.index('--name') + 1]], capture_output=True, timeout=30, check=False)
                _save(OUT / 'failure.json', {'phase': phase, 'status': 'timeout_no_retry', 'provider_calls': 0})
                raise
        marker = 'E1C2_PUBLIC_VARIANT='
        observed = [json.loads(line[len(marker):]) for line in log_path.read_text(encoding='utf-8', errors='replace').splitlines()
                    if line.startswith(marker)]
        if rc != 0 or [r['id'] for r in observed] != [r['id'] for r in rows]:
            raise ValueError('valid complete public sweep execution required')
        _save(OUT / (phase + '.json'), {'rows': observed, 'log_sha256': _sha(log_path), 'provider_calls': 0})
        phase_rows[phase] = observed
        print(json.dumps({'phase': phase, 'completed': sum(r['returncode'] == 0 for r in observed), 'total': len(observed)}), flush=True)
    gaps = [row['id'] for row, old in zip(phase_rows['patch'], phase_rows['release'], strict=True)
            if old['returncode'] == 0 and row['returncode'] != 0]
    value = {'provider_calls': 0, 'variant_count': 21, 'phase_completed': {
        p: sum(r['returncode'] == 0 for r in values) for p, values in phase_rows.items()},
        'patch_fails_where_public_release_completes': gaps, 'new_model_generation': False,
        'official_test_or_Gold_read': False, 'synthetic_not_new_tasks': True, 'full_issue_trusted': False}
    for name, digest in bindings.items():
        if _sha(ROOT / name) != digest:
            raise ValueError('sealed parent binding changed')
    _save(OUT / 'result.json', value)
    return value


if __name__ == '__main__':
    print(json.dumps(run()), flush=True)
