import hashlib
import json

import pytest

from evals import e1c_evaluation_2_acquisition_check_resume as resume


def fixture(tmp_path):
    source, old, destination = (tmp_path / n for n in ('source', 'old', 'destination'))
    folder = source / 'task/turn-1'
    folder.mkdir(parents=True)
    (folder / 'prefix-replay.json').write_text('{}', encoding='utf-8')
    hashes = {}
    for name in ('compiler.json', 'contract.json', 'execution.json'):
        path = old / 'task/turn-1' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"original":true}', encoding='utf-8')
        hashes['task/turn-1/' + name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (source / 'generation-seal.json').write_text(json.dumps({'files': {'task/turn-1/prefix-replay.json': hashlib.sha256(b'{}').hexdigest()}}), encoding='utf-8')
    return source, old, destination, hashes


def test_compose_adds_only_original_sha_bound_cached_artifacts(tmp_path):
    source, old, destination, hashes = fixture(tmp_path)
    assert resume.compose(source, old, destination, hashes) == hashes
    assert (destination / 'task/turn-1/compiler.json').read_bytes() == (old / 'task/turn-1/compiler.json').read_bytes()
    assert (source / 'task/turn-1/prefix-replay.json').read_bytes() == b'{}'


def test_unbound_or_changed_cached_artifact_rejected(tmp_path):
    source, old, destination, hashes = fixture(tmp_path)
    hashes['task/turn-1/compiler.json'] = '0' * 64
    with pytest.raises(ValueError, match='not bound'):
        resume.compose(source, old, destination, hashes)
