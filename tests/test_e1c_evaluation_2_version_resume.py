import ast
import hashlib

import pytest

from evals import e1c_evaluation_2_version_resume as resume


def preparation(tmp_path):
    raw = b"__version__ = '1.0.0'\n"
    path = tmp_path / 'synthetic/source/pkg/__init__.py'
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    return {'status': 'INFRA_BLOCKED', 'phase': 'after_materialization_before_engine_admission', 'instance_id': 'synthetic',
            'diagnostic_containers_started': 0, 'driver_created': False, 'task_freeze_created': False,
            'source_files': [{'path': 'pkg/__init__.py', 'sha256': hashlib.sha256(raw).hexdigest()}]}


def test_only_unstarted_interruption_reuses_unchanged_prepared_source(tmp_path):
    failure = preparation(tmp_path)
    assert resume.require_unstarted(tmp_path, failure) == tmp_path / 'synthetic/source'


@pytest.mark.parametrize('field,value', [('driver_created', True), ('task_freeze_created', True), ('diagnostic_containers_started', 1),
                                       ('diagnostic_containers_started', False), ('phase', 'executed')])
def test_started_or_wrong_phase_cannot_replay(tmp_path, field, value):
    failure = preparation(tmp_path)
    failure[field] = value
    with pytest.raises(ValueError):
        resume.require_unstarted(tmp_path, failure)


def test_actual_runtime_artifact_or_changed_source_blocks_resume(tmp_path):
    failure = preparation(tmp_path)
    (tmp_path / 'synthetic/driver.py').write_text('pass\n')
    with pytest.raises(ValueError, match='runtime artifact'):
        resume.require_unstarted(tmp_path, failure)


def test_extra_source_file_or_wrong_digest_not_reused(tmp_path):
    failure = preparation(tmp_path)
    failure['source_files'][0]['sha256'] = 'a' * 64
    with pytest.raises(ValueError, match='bytes differ'):
        resume.require_unstarted(tmp_path, failure)
    (tmp_path / 'synthetic/source/pkg/extra.py').write_text('pass\n')
    with pytest.raises(ValueError, match='inventory differs'):
        resume.require_unstarted(tmp_path, failure)


def test_driver_binds_old_version_path_original_probe_and_sources():
    source = resume.build_driver('a' * 64, [{'path': 'pkg/__init__.py', 'sha256': 'b' * 64}], 'pkg', '1.0.0', 'E1C2_VERSION_' + 'c' * 32 + '=')
    ast.parse(source)
    assert 'original model probe changed' in source and 'actual historical library version/path differs' in source
    assert 'runpy.run_path' in source and 'e1c2_old' in source
