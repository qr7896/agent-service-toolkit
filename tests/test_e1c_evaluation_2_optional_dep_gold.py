import json

import pytest

from evals import e1c_evaluation_2_optional_dep_gold as gold


def test_gold_discriminator_requires_repeatable_isolated_base_failure(tmp_path, monkeypatch):
    instance_id = gold.TASKS[0]
    path = tmp_path / instance_id
    path.mkdir()
    (path / "result.json").write_text(json.dumps({
        "schema": "e1c2-optional-dep-dev-diagnostic-v2",
        "provider_calls": 0,
        "execution": {"network_none": True, "pull_never": True,
                      "repeatable_nonsetup_failure": False, "runs": []},
    }), encoding="utf-8")
    monkeypatch.setattr(gold, "BASE", tmp_path)
    with pytest.raises(ValueError, match="repeatable, isolated base failure"):
        gold.run(instance_id)
