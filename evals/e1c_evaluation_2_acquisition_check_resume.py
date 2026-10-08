"""Compose SHA-bound cached compiler artifacts; continue unstarted zero checks."""

from __future__ import annotations

import json
import shutil
from unittest.mock import patch

from evals import e1c_evaluation_2_acquisition_check as check
from evals.e1c_evaluation_2_dev_pilot import ROOT, _save, _sha

OUT = ROOT / '.codex/e1c/evaluation_2/acquisition-context-zero-resume-v1'
PROTOCOL = ROOT / 'docs/research/E1C2_ACQUISITION_CHECK_RESUME_PROTOCOL_2026-10-08.md'


def compose(source, original, destination, original_hashes):
    seal = json.loads((source / 'generation-seal.json').read_bytes())
    for name, digest in seal['files'].items():
        file = source / name
        target = destination / name
        if not file.resolve().is_relative_to(source.resolve()) or not target.resolve().is_relative_to(destination.resolve()):
            raise ValueError('artifact path escaped generation scope')
        if file.is_symlink() or _sha(file) != digest:
            raise ValueError('sealed generation source changed')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
    shutil.copyfile(source / 'generation-seal.json', destination / 'generation-seal.json')
    additions = {}
    for replay in sorted(destination.glob('*/turn-*/prefix-replay.json')):
        relative = replay.parent.relative_to(destination)
        for name in ('compiler.json', 'contract.json', 'execution.json'):
            target, old = replay.parent / name, original / relative / name
            if target.exists():
                continue
            key = (relative / name).as_posix()
            if key not in original_hashes or old.is_symlink() or _sha(old) != original_hashes[key]:
                raise ValueError('cached compiler artifact not bound to original prefix')
            shutil.copyfile(old, target)
            additions[key] = _sha(target)
    return additions


def run():
    if OUT.exists():
        raise FileExistsError('zero-check continuation started; no retry')
    failed = json.loads((check.OUT / 'freeze.json').read_bytes())
    if any(_sha(ROOT / name) != digest for name, digest in failed['method_sha256'].items()):
        raise ValueError('failed zero-check method changed')
    previous = check.previous
    if _sha(previous.OUT / 'generation-seal.json') != failed['old_generation_seal_sha256']:
        raise ValueError('original sealed generation identity changed')
    original = previous.ORIGINAL
    prefix = json.loads((previous.OUT / 'freeze.json').read_bytes())['resume_plan']['original_files']
    _save(OUT / 'provenance-freeze.json', {'driver_sha256': _sha(ROOT / 'evals/e1c_evaluation_2_acquisition_check_resume.py'),
                                        'protocol_sha256': _sha(PROTOCOL), 'failed_check_freeze_sha256': _sha(check.OUT / 'freeze.json'),
                                        'previous_seal_sha256': _sha(previous.OUT / 'generation-seal.json'), 'provider_calls': 0})
    view = OUT / 'generation-view'
    additions = compose(previous.OUT, original, view, prefix)
    _save(OUT / 'cached-additions.json', additions)
    with patch.object(check, 'OUT', OUT / 'check'), patch.object(check, 'PROTOCOL', PROTOCOL), patch.object(previous, 'OUT', view):
        result = check.run()
    _save(OUT / 'result.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False), flush=True)
