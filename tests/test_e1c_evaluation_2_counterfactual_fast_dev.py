import hashlib

import pytest

from evals import e1c_evaluation_2_counterfactual_fast_dev as fast


def test_fast_input_still_checks_clean_head_and_production_sha(tmp_path, monkeypatch):
    code = b"def api(): return 1\n"
    path = tmp_path / "core.py"
    path.write_bytes(code)
    frozen = {"base_commit": "fixture", "candidate_paths": ["core.py"],
              "windows": [{"path": "core.py", "source_sha256": hashlib.sha256(code).hexdigest()}]}
    monkeypatch.setattr(fast.subprocess, "check_output", lambda command, **kwargs: "fixture" if "rev-parse" in command else "")
    fast.verify_workspace(frozen, tmp_path)
    path.write_bytes(b"def api(): return 2\n")
    with pytest.raises(ValueError, match="source changed"):
        fast.verify_workspace(frozen, tmp_path)


def test_fast_input_rejects_dirty_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(fast.subprocess, "check_output", lambda command, **kwargs: "fixture" if "rev-parse" in command else " M core.py")
    with pytest.raises(ValueError, match="clean at base"):
        fast.verify_workspace({"base_commit": "fixture"}, tmp_path)
