from types import SimpleNamespace

from evals import e1c_evaluation_2_canary_v2_proxy_live as live


def test_live_binding_preserves_prompt_and_budget_in_new_directory(tmp_path, monkeypatch):
    def verified(iid):
        return "sha256:" + "a" * 64

    stage = SimpleNamespace(GRADER=tmp_path / "grader", PUBLIC=tmp_path / "public", SOURCE=tmp_path / "source",
                            materialize=SimpleNamespace(verified_image=verified))
    runtime = SimpleNamespace()
    adapter = SimpleNamespace(flash=SimpleNamespace(prompt=object()), _admitted_inputs=object())
    monkeypatch.setattr(live, "base", runtime)
    monkeypatch.setattr(live, "original", adapter)
    monkeypatch.setattr(live.infrastructure, "OUT", tmp_path)
    monkeypatch.setattr(live.infrastructure, "bind_stage", lambda: stage)
    live.configure()
    assert runtime.RUN_ID == live.RUN_ID
    assert runtime.OUT == tmp_path / "live"
    assert runtime.prompt is live.original.flash.prompt
    assert (runtime.MODEL, runtime.TASK_TOKEN_CAP, runtime.BATCH_TOKEN_CAP, runtime.MAX_OUTPUT_TOKENS) == (
        "deepseek-flash", 14000, 42000, 2600,
    )
    assert runtime.verified_local_image is verified
    assert runtime.preflight is live.preflight


def test_preflight_binds_transport_and_each_admission_without_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "configure", lambda: None)
    monkeypatch.setattr(live, "_original_preflight", lambda: {"cohort": [{"instance_id": "example"}], "provider_calls": 0})
    monkeypatch.setattr(live, "original", SimpleNamespace(GRADER=tmp_path / "grader"))
    monkeypatch.setattr(live, "_sha", lambda path: path.name)
    value = live.preflight()
    assert value["run_id"] == live.RUN_ID
    assert value["transport_amendment_sha256"] == live.infrastructure.FREEZE.name
    assert value["image_transport_sha256"] == live.infrastructure.TRANSPORT.name
    assert value["official_admission_sha256"] == {"example": {"base": "base.json", "gold": "gold.json"}}
    assert value["provider_calls"] == 0
