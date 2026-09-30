"""Grader-only discrimination of the sealed unified DEV v3 output."""

from __future__ import annotations

import json

from evals import e1c_evaluation_2_unified_dev_v2_gold as gold
from evals import e1c_evaluation_2_unified_dev_v3 as v3

gold.OUT = gold.GRADER / "unified-dev-v3-discrimination"
assert gold.base.preflight is v3.preflight


if __name__ == "__main__":
    print(json.dumps(gold.run(), ensure_ascii=False))
