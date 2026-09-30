"""Grader-only Gold discrimination for the sealed independent canary run."""

from __future__ import annotations

import json

from evals import e1c_evaluation_2_admission as admission
from evals import (
    e1c_evaluation_2_canary_live as live,  # noqa: F401 - binds frozen method in this process
)
from evals import e1c_evaluation_2_unified_dev_v2_gold as gold
from evals.e1c_evaluation_2_canary_materialize import GRADER, verified_image
from evals.e1c_evaluation_2_canary_metadata import OUT as METADATA
from evals.e1c_evaluation_2_canary_select import IDENTITY


def run() -> dict:
    original_admission = {name: getattr(admission, name) for name in ("IDENTITY", "METADATA", "OUT", "TREE", "verified_local_image")}
    original_gold = {name: getattr(gold, name) for name in ("GRADER", "OUT", "materialize", "verified_local_image")}
    try:
        admission.IDENTITY = IDENTITY
        admission.METADATA = METADATA
        admission.OUT = GRADER
        admission.TREE = GRADER / "frozen-task-blobs.json"
        admission.verified_local_image = verified_image
        gold.GRADER = GRADER
        gold.OUT = GRADER / "canary-v1-discrimination"
        gold.materialize = admission.materialize
        gold.verified_local_image = verified_image
        return gold.run()
    finally:
        for name, value in original_admission.items():
            setattr(admission, name, value)
        for name, value in original_gold.items():
            setattr(gold, name, value)


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
