"""Replay unchanged public-derived probes against a sealed model patch, no scorer inputs."""

from __future__ import annotations

import json
import subprocess

from evals import e1c_evaluation_2_three_arm_decode_audit as audit
from evals import e1c_evaluation_2_three_arm_dev as repair
from evals.e1c_evaluation_2_container_health import require_engine
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha
from evals.e1c_evaluation_2_probe import docker_command

OUT = ROOT / '.codex/e1c/evaluation_2/three-arm-public-patch-probe-zero-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_PUBLIC_PATCH_PROBE_ZERO_2026-10-08.md'


def patch_command(candidate, image, base, probe, candidate_patch, blocker):
    command = docker_command(candidate, image, base, probe, blocked_import_dir=blocker)
    command.remove('--read-only')  # Only the disposable container layer is writable for git apply.
    index = command.index(image)
    command[index:index] = ['--mount', f'type=bind,source={candidate_patch.resolve()},target=/candidate.patch,readonly']
    script_index = command.index('-c') + 1
    script = command[script_index]
    before, after = script.split('cd /testbed;', 1)
    command[script_index] = before + ('cd /testbed; git apply --check /candidate.patch && git apply /candidate.patch '
        '|| exit 91; echo E1C2_PUBLIC_PATCH_APPLIED; ' + after)
    return command


def run():
    if OUT.exists():
        raise FileExistsError('public patch probe audit already started; no retry')
    frozen = repair._read(repair.OUT / 'freeze.json')
    if frozen != repair.preflight():
        raise ValueError('original method identity differs')
    repair.verify_seal(repair.OUT)
    repair.verify_seal(audit.OUT)
    eligible = [arm for arm in repair.ARMS if repair._read(audit.OUT / arm / 'generation.json')['status'] == 'candidate']
    if len(eligible) != 1:
        raise ValueError('diagnostic requires the sole compiled sealed candidate')
    candidate_patch = audit.OUT / eligible[0] / 'candidate.patch'
    task = next(t for t in repair._read(repair.source.PARENT / 'freeze.json')['tasks'] if t['instance_id'] == frozen['instance_id'])
    origin = repair.source.OUT / frozen['instance_id']
    missing = task['environment']['missing_optional_import']
    blocker = origin / 'execution/optional_missing' if missing else None
    bindings = {p.relative_to(ROOT).as_posix(): _sha(p) for p in (
        repair.OUT / 'generation-seal.json', audit.OUT / 'generation-seal.json', candidate_patch,
        origin / 'candidate.json', origin / 'control_candidate.json',
        ROOT / 'evals/e1c_evaluation_2_patch_probe_zero.py', PROTOCOL)}
    if missing:
        if (blocker / (missing + '.py')).read_bytes() != f"raise ModuleNotFoundError(\"No module named '{missing}'\")\n".encode():
            raise ValueError('original dependency blocker differs')
        bindings[(blocker / (missing + '.py')).relative_to(ROOT).as_posix()] = _sha(blocker / (missing + '.py'))
    require_engine((frozen['image_id'],))
    _save(OUT / 'freeze.json', {'provider_calls': 0, 'new_generation': False, 'bindings': bindings,
                              'same_image_base_optional_condition': True, 'arm': eligible[0]})
    rows = []
    for phase in ('control', 'target'):
        candidate = repair._read(origin / ('control_candidate.json' if phase == 'control' else 'candidate.json'))
        if candidate['safe_static_check'] is not True:
            raise ValueError('validated public-derived probe required')
        path = OUT / (phase + '.py')
        with path.open('xb') as handle:
            handle.write(candidate['source'].encode())
        for n in (1, 2):
            command = patch_command(candidate, frozen['image_id'], frozen['base_commit'], path, candidate_patch, blocker)
            log_path = OUT / f'{phase}-{n}.log'
            with log_path.open('xb') as log:
                try:
                    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=90, check=False)
                except subprocess.TimeoutExpired:
                    subprocess.run(['docker', 'rm', '-f', command[command.index('--name') + 1]], capture_output=True, timeout=30, check=False)
                    _save(OUT / 'failure.json', {'status': 'infra_timeout', 'provider_calls': 0, 'no_retry': True})
                    raise
            text = log_path.read_text(encoding='utf-8', errors='replace')
            row = {'phase': phase, 'repeat': n, 'returncode': result.returncode,
                   'patch_applied': 'E1C2_PUBLIC_PATCH_APPLIED' in text,
                   'probe_sha256': candidate['probe_sha256'], 'log_sha256': _sha(log_path), 'provider_calls': 0}
            _save(OUT / f'{phase}-{n}.json', row)
            rows.append(row)
            print(json.dumps(row), flush=True)
    value = {'rows': rows, 'provider_calls': 0, 'new_generation': False,
             'unchanged_public_control_completed': all(r['returncode'] == 0 and r['patch_applied'] for r in rows if r['phase'] == 'control'),
             'unchanged_public_target_completed': all(r['returncode'] == 0 and r['patch_applied'] for r in rows if r['phase'] == 'target'),
             'official_test_or_Gold_content_read': False, 'full_issue_trusted': False, 'original_scores_unchanged': True}
    for name, digest in bindings.items():
        if _sha(ROOT / name) != digest:
            raise ValueError('sealed parent source changed')
    _save(OUT / 'result.json', value)
    return value


if __name__ == '__main__':
    print(json.dumps(run()), flush=True)
