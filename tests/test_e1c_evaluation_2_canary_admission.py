import base64
import hashlib
import io
import json

from evals import e1c_evaluation_2_admission as admission
from evals import e1c_evaluation_2_canary_admission as canary


def test_canary_admission_reuses_official_runner_and_restores_dev_bindings(monkeypatch):
    before = {name: getattr(admission, name) for name in ("IDENTITY", "METADATA", "OUT", "TREE", "verified_local_image")}
    monkeypatch.setattr(canary, "rows", lambda: [{"instance_id": "demo__demo-1"}])

    def fake_run(instance_id, phase, *, timeout):
        assert admission.IDENTITY == canary.IDENTITY
        assert admission.OUT == canary.GRADER
        assert admission.verified_local_image is canary.verified_image
        return {"instance_id": instance_id, "phase": phase, "timeout": timeout}

    monkeypatch.setattr(admission, "run_phase", fake_run)
    assert canary.run_phase("demo__demo-1", "base", timeout=12) == {
        "instance_id": "demo__demo-1", "phase": "base", "timeout": 12,
    }
    assert all(getattr(admission, name) is value for name, value in before.items())


def test_grader_contents_api_still_requires_frozen_blob(monkeypatch):
    raw = b"offline grader fixture"
    digest = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    path = "tasks/demo__demo-1/gold.patch"
    payload = {"path": path, "sha": digest, "encoding": "base64", "content": base64.b64encode(raw).decode()}

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()

    monkeypatch.setattr(admission.urllib.request, "urlopen", lambda request, timeout: Response(json.dumps(payload).encode()))
    assert admission._official_file("a" * 40, path, digest) == raw
    payload["sha"] = "b" * 40
    try:
        admission._official_file("a" * 40, path, digest)
    except ValueError:
        pass
    else:
        raise AssertionError("changed official blob must be refused")
