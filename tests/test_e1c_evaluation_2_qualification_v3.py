import copy
import hashlib
import json

import pytest

from evals import e1c_evaluation_2_qualification_v3 as auditor

SCOPE = {"instance_id": "synthetic", "image": "sha256:" + "a" * 64, "base_commit": "b" * 40}


def context(tmp_path, monkeypatch):
    raw = b"class Api:\r\n    pass\r\n"
    (tmp_path / "core.py").write_bytes(raw)
    canonical = raw.replace(b"\r\n", b"\n")
    digest = hashlib.sha256(canonical).hexdigest()
    monkeypatch.setattr(auditor, "git_blob", lambda *args: canonical)
    row = {"instance_id": "synthetic", "base_commit": SCOPE["base_commit"], "immutable_image": SCOPE["image"],
           "path": "core.py", "host_bytes_sha256": hashlib.sha256(raw).hexdigest(), "effective_LF_sha256": digest,
           "canonical_base_blob_sha256": digest, "runtime_source_identity": {
               "live_equals_git_blob": True, "live_sha256": digest, "canonical_git_sha256": digest}}
    return {"base_commit": SCOPE["base_commit"], "windows": []}, {"rows": [row]}


def test_overlay_identity_verified_but_original_model_inputs_not_edited(tmp_path, monkeypatch):
    frozen, authority = context(tmp_path, monkeypatch)
    before = copy.deepcopy(frozen)
    augmented, proofs = auditor.authority_overlay(frozen, tmp_path, SCOPE, authority)
    assert frozen == before and len(augmented["windows"]) == 1
    assert not proofs[0]["original_model_exposure"]


@pytest.mark.parametrize("change", [
    {"base_commit": "c" * 40}, {"immutable_image": "sha256:" + "d" * 64},
    {"effective_LF_sha256": "e" * 64}, {"path": "tests/answer.py"},
])
def test_wrong_base_image_digest_or_protected_path_rejected(tmp_path, monkeypatch, change):
    frozen, authority = context(tmp_path, monkeypatch)
    authority["rows"][0].update(change)
    with pytest.raises(Exception):
        auditor.authority_overlay(frozen, tmp_path, SCOPE, authority)


def test_modified_host_source_not_normalized_away(tmp_path, monkeypatch):
    frozen, authority = context(tmp_path, monkeypatch)
    (tmp_path / "core.py").write_bytes(b"class Api:\n    changed = True\n")
    with pytest.raises(ValueError, match="identity differs"):
        auditor.authority_overlay(frozen, tmp_path, SCOPE, authority)


def test_receipt_digest_mismatch_rejected(tmp_path):
    path = tmp_path / "authority.json"
    path.write_bytes(json.dumps({"provider_calls": 0, "Gold_read": False, "rows": []}).encode())
    with pytest.raises(ValueError, match="digest differs"):
        auditor.load_authority(path, "a" * 64)


def test_wrong_local_canonical_git_blob_rejected(tmp_path, monkeypatch):
    frozen, authority = context(tmp_path, monkeypatch)
    monkeypatch.setattr(auditor, "git_blob", lambda *args: b"another base source")
    with pytest.raises(ValueError, match="identity differs"):
        auditor.authority_overlay(frozen, tmp_path, SCOPE, authority)
