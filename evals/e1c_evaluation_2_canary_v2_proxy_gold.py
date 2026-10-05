"""Grader-only Gold discrimination for the amended, one-shot second canary."""

from __future__ import annotations

import json

from evals import e1c_evaluation_2_canary_v2_proxy_live as live


def run() -> dict:
    from evals import e1c_evaluation_2_unified_dev_v2_gold as gold

    live.configure()
    stage = live.infrastructure.bind_stage()
    gold.GRADER = stage.GRADER
    gold.OUT = stage.GRADER / "canary-v2-proxy-discrimination"
    gold.materialize = stage.admission.materialize
    gold.verified_local_image = stage.materialize.verified_image
    return gold.run()


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
