import io
import subprocess
import tarfile

import pytest

from evals import e1c_evaluation_2_version_witness as witness


def test_old_version_only_from_unambiguous_public_success_constraint():
    assert witness.quoted_success_version('works in <=3.0.0rc8, fails in >=3.0.0rc9') == '3.0.0rc8'
    assert witness.quoted_success_version('marshmallow==2.19.3 and earlier works') == '2.19.3'
    assert witness.quoted_success_version('<=1.0.0 or <=2.0.0') is None
    assert witness.quoted_success_version('try an older version') is None


def test_declared_version_does_not_execute_module_code():
    assert witness.declared_version(b"__version__ = '1.0.0'\nraise RuntimeError('do not run')\n") == '1.0.0'
    assert witness.declared_version(b'__version__ = calculate()\n') is None


def test_local_ancestor_history_and_production_materialization_without_tags(tmp_path):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(tmp_path), '-c', 'user.name=Synthetic', '-c', 'user.email=synthetic@invalid',
                                        '-c', 'core.hooksPath=' + str(tmp_path / 'no-hooks'), *args])
    git('init')
    (tmp_path / 'pkg').mkdir()
    (tmp_path / 'pkg/__init__.py').write_text("__version__ = '1.0.0'\n", encoding='utf-8')
    git('add', '--', 'pkg/__init__.py')
    git('commit', '-m', 'old')
    old = git('rev-parse', 'HEAD').decode().strip()
    (tmp_path / 'pkg/__init__.py').write_text("__version__ = '1.0.1'\n", encoding='utf-8')
    git('add', '--', 'pkg/__init__.py')
    git('commit', '-m', 'new')
    base = git('rev-parse', 'HEAD').decode().strip()
    snapshot = witness.local_snapshot(tmp_path, base, 'pkg', '1.0.0')
    assert snapshot['commit'] == old
    files = witness.materialize(tmp_path, snapshot, tmp_path / 'snapshot')
    assert len(files) == 1 and (tmp_path / 'snapshot/pkg/__init__.py').read_text() == "__version__ = '1.0.0'\n"
    assert (tmp_path / 'pkg/__init__.py').read_text() == "__version__ = '1.0.1'\n"
    with pytest.raises(FileExistsError):
        witness.materialize(tmp_path, snapshot, tmp_path / 'snapshot')


@pytest.mark.parametrize('name,symlink', [('pkg/escape.py', True), ('pkg/tests/answer.py', False), ('../escape.py', False)])
def test_archive_links_protected_paths_or_escape_rejected_before_write(tmp_path, monkeypatch, name, symlink):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode='w') as tar:
        info = tarfile.TarInfo(name)
        if symlink:
            info.type = tarfile.SYMTYPE
            info.linkname = '../outside.py'
            tar.addfile(info)
        else:
            info.size = 5
            tar.addfile(info, io.BytesIO(b'pass\n'))
    monkeypatch.setattr(witness.subprocess, 'check_output', lambda *args, **kwargs: data.getvalue())
    with pytest.raises((ValueError, RuntimeError)):
        witness.materialize(tmp_path, {'commit': 'a' * 40, 'package': 'pkg'}, tmp_path / 'snapshot')
    assert not (tmp_path / 'snapshot').exists()
