import json
from pathlib import Path

from evals.e1c_reproducer_dev_selection import ROOT, _identities, build


def test_nested_exclusions_and_frozen_development_identity():
    assert _identities({"tasks": [{"instance_id": "a__a-1"}], "other": ["ignored"]}) == {"a__a-1"}
    frozen = json.loads((Path(ROOT) / "data/e1c_reproducer_dev12_identity.json").read_text())
    current = build()
    assert current == frozen
    assert len(current["tasks"]) == 12
    assert len({row["instance_id"].split("__")[0] for row in current["tasks"]}) == 4
    assert current["task_content_inspected_at_selection"] is False
