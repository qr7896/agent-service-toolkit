from __future__ import annotations

import json

from scripts.wave_b_verification_ledger import append_result, next_candidate


def test_next_candidate_resumes_after_checkpoint(tmp_path) -> None:
    queue = tmp_path / "queue.json"
    ledger = tmp_path / "ledger.jsonl"
    queue.write_text(
        json.dumps({"eligible_for_verification": [{"commit": "aaa"}, {"commit": "bbb"}]}),
        encoding="utf-8",
    )
    assert next_candidate(queue, ledger) == {"commit": "aaa"}
    append_result(ledger, {"commit": "aaa", "gold_exit": 0, "base_exit": 1})
    assert next_candidate(queue, ledger) == {"commit": "bbb"}
    append_result(ledger, {"commit": "bbb", "gold_exit": 0, "base_exit": 1})
    assert next_candidate(queue, ledger) is None
