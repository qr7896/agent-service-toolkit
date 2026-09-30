from evals.e1c_blind_repro_selector import (
    C4_IDS,
    EXCLUDED_IDS,
    canary_rows,
    eligible_reproducer_rows,
    frozen_selector_identity,
)


def test_reproducer_selector_excludes_all_seen_canaries() -> None:
    ids = {row["instance_id"] for row in eligible_reproducer_rows()}
    assert not ids.intersection(EXCLUDED_IDS)
    assert len(ids) == 9
    assert len(C4_IDS) == 6


def test_reproducer_selector_is_frozen_repo_stratified() -> None:
    rows = canary_rows()
    assert [row["instance_id"] for row in rows] == [
        "django__django-16502",
        "sympy__sympy-13877",
        "sphinx-doc__sphinx-8056",
        "django__django-12774",
        "sympy__sympy-15875",
        "sphinx-doc__sphinx-9673",
    ]
    identity = frozen_selector_identity()
    assert identity["selector_sha256"]
    assert [row["instance_id"] for row in identity["tasks"]] == [
        row["instance_id"] for row in rows
    ]
