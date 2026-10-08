import io
import json
import stat
import zipfile

import pytest

from evals import e1c_evaluation_2_release_witness as witness


def archive(extra=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as zipped:
        zipped.writestr('marshmallow/__init__.py', "__version__ = '2.19.3'\n")
        if extra:
            name, content = extra
            if isinstance(name, str):
                item = zipfile.ZipInfo(name)
                item.filename = name  # Preserve the raw spelling rather than Windows ZipInfo normalization.
                item.orig_filename = name
            else:
                item = name
            zipped.writestr(item, content)
    return output.getvalue()


def test_only_production_sources_are_loaded_without_install_or_execution():
    raw = archive(('marshmallow-2.19.3.dist-info/METADATA', 'ignored metadata'))
    assert list(witness.production_sources(raw)) == ['marshmallow/__init__.py']


@pytest.mark.parametrize('name', ['../escape.py', '/absolute.py', 'marshmallow\\escape.py', 'C:/escape.py',
                                  'marshmallow/./escape.py', 'marshmallow//escape.py'])
def test_archive_escape_paths_rejected(name):
    with pytest.raises(ValueError, match='unsafe archive path'):
        witness.production_sources(archive((name, 'x=1')))


def test_archive_symlink_and_duplicate_rejected():
    info = zipfile.ZipInfo('marshmallow/link.py')
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(ValueError, match='symlink'):
        witness.production_sources(archive((info, 'outside.py')))
    with pytest.warns(UserWarning), pytest.raises(ValueError, match='duplicate'):
        witness.production_sources(archive(('marshmallow/__init__.py', "__version__='wrong'\n")))


def test_missing_or_wrong_version_and_source_budget_rejected():
    with pytest.raises(ValueError, match='version differs'):
        witness.production_sources(archive(), version='2.19.4')
    with pytest.raises(ValueError, match='budget exceeded'):
        witness.production_sources(b'x' * 1_000_001)


@pytest.mark.parametrize('returncode,marker_report,expected', [
    (0, True, 'same_probe_completed'), (1, True, 'same_probe_failed'),
    (0, False, 'invalid_release_preflight'), (125, True, 'infra_blocked')])
def test_success_requires_actual_version_path_probe_and_condition(returncode, marker_report, expected):
    marker = 'OWN='
    fields = {'release_version_path_verified': marker_report, 'probe_source_unchanged': True,
              'same_enforced_optional_condition': True}
    assert witness.classify(returncode, marker + json.dumps(fields), marker)['status'] == expected
