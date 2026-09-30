from evals.e1c_strict_v6_probe import candidate_witnesses, freeze_witness_plan


def _localization():
    return {
        "candidates": [{
            "path": "pkg/engine.py",
            "symbol": "normalize",
            "source_sha256": "a" * 64,
            "text": "def normalize(value):\n    return value\n",
        }]
    }


def test_v6_accepts_return_instead_of_relation() -> None:
    rows = candidate_witnesses(
        "normalize(3) currently returns 3 instead of 4.",
        _localization(),
    )
    assert rows[0]["relation"] == "return_equals"
    assert rows[0]["expected"] == "4"


def test_v6_accepts_equality_relation() -> None:
    rows = candidate_witnesses("normalize(3) == 4 is the desired behavior.", _localization())
    assert rows[0]["expected"] == "4"


def test_v6_accepts_contains_and_not_contains() -> None:
    yes = candidate_witnesses("normalize('x') should contain 'x'.", _localization())
    no = candidate_witnesses("normalize('x') should not contain 'bad'.", _localization())
    assert yes[0]["relation"] == "contains"
    assert no[0]["relation"] == "not_contains"


def test_v6_accepts_raise_instead_of_relation() -> None:
    rows = candidate_witnesses(
        "normalize(3) raises TypeError instead of ValueError.",
        _localization(),
    )
    assert rows[0]["relation"] == "raises"
    assert rows[0]["expected"] == "ValueError"


def test_v6_rejects_dynamic_calls_and_abstains() -> None:
    plan = freeze_witness_plan("normalize(other()) should return 4.", _localization())
    assert plan["status"] == "no_reproducer"
    assert plan["trusted_reproducer"] is False
