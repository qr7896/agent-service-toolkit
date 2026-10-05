"""Bind the unchanged v4 canary generator to its frozen transport amendment."""

from __future__ import annotations

from pathlib import Path

from evals import e1c_evaluation_2_canary_v2_metadata_proxy as infrastructure
from evals.e1c_evaluation_2_dev_pilot import _sha

base = None
original = None
RUN_ID = "e1c2-independent-canary-v2-metadata-proxy-v1-flash"
PROTOCOL = infrastructure.ROOT / "docs/research/E1C2_CANARY_V2_PROXY_LIVE_PROTOCOL_2026-10-05.md"
_original_preflight = None


def configure() -> None:
    global base, original, _original_preflight
    if original is None:
        from evals import e1c_evaluation_2_canary_v2_live as adapter

        original, base = adapter, adapter.base
        _original_preflight = adapter.preflight
    stage = infrastructure.bind_stage()
    original.OUT = infrastructure.OUT
    original.GRADER, original.PUBLIC, original.SOURCE = stage.GRADER, stage.PUBLIC, stage.SOURCE
    base.RUN_ID, base.OUT = RUN_ID, infrastructure.OUT / "live"
    base.FREEZE, base.LEDGER = base.OUT / "freeze.json", base.OUT / "provider_calls.jsonl"
    base.IDENTITY, base.ADMISSION = infrastructure.IDENTITY, stage.GRADER
    base.ISSUE, base.SOURCE = stage.PUBLIC, stage.SOURCE
    base.MODEL, base.MAX_OUTPUT_TOKENS = "deepseek-flash", 2600
    base.TASK_TOKEN_CAP, base.BATCH_TOKEN_CAP = 14_000, 42_000
    base.prompt = original.flash.prompt
    base._admitted_inputs = original._admitted_inputs
    base.verified_local_image = stage.materialize.verified_image
    base.preflight = preflight


def preflight() -> dict:
    configure()
    value = _original_preflight()
    value.update({
        "schema": "e1c2-independent-canary-v2-metadata-proxy-v1-flash-freeze",
        "run_id": RUN_ID,
        "selection": "same_fixed_canary_v2_cohort_with_declared_infrastructure_amendment",
        "adapter_sha256": _sha(Path(__file__)),
        "transport_amendment_sha256": _sha(infrastructure.FREEZE),
        "image_transport_sha256": _sha(infrastructure.TRANSPORT),
        "live_protocol_sha256": _sha(PROTOCOL),
        "gold_adapter_sha256": _sha(infrastructure.ROOT / "evals/e1c_evaluation_2_canary_v2_proxy_gold.py"),
        "official_admission_sha256": {
            task["instance_id"]: {phase: _sha(original.GRADER / task["instance_id"] / f"{phase}.json")
                                  for phase in ("base", "gold")}
            for task in value["cohort"]
        },
    })
    return value


if __name__ == "__main__":
    # Configure before main resolves the destination for its immutable freeze.
    configure()
    base.main()
