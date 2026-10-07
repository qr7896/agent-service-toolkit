import ast
import hashlib

import pytest

from evals import e1c_evaluation_2_exception_observer_v2 as observer


def test_projection_keeps_original_bytes_and_binds_both_identities(tmp_path):
    raw = b"def api():\r\n    return 1\r\n"
    path = tmp_path / "core.py"
    path.write_bytes(raw)
    sites, proof = observer.project_sites(tmp_path, [{"path": "core.py", "line": 1, "variable": "exception",
        "source_sha256": hashlib.sha256(raw).hexdigest()}])
    assert path.read_bytes() == raw and proof[0]["untouched_exposure_sha256"] == hashlib.sha256(raw).hexdigest()
    assert sites[0]["source_sha256"] == hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def test_changed_source_not_normalized_away(tmp_path):
    (tmp_path / "core.py").write_bytes(b"changed source")
    with pytest.raises(ValueError, match="exposed source changed"):
        observer.project_sites(tmp_path, [{"path": "core.py", "line": 1, "variable": "exception", "source_sha256": "a" * 64}])


def test_driver_checks_canonical_git_blob_and_old_python_compatible_path():
    source, _ = observer.build_driver("a" * 64, [{"path": "core.py", "line": 1, "variable": "exception", "source_sha256": "b" * 64}], "c" * 32, [], [], "d" * 40)
    ast.parse(source)
    assert "subprocess.check_output(['git'" in source and "removeprefix" not in source
    assert "canonical_git_and_effective_file_hash_required': True" in source
    assert "semantic_alignment_proven': False" in source
