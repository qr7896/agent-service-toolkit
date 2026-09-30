from evals.e1c_blind_postb4_selector import (
    B4_IDS,
    HISTORICAL_SOLVED_IDS,
    canary_rows,
    eligible_unresolved_rows,
    frozen_selector_identity,
)


def test_postb4_selector_excludes_b4_and_historical_solved() -> None:
    rows = eligible_unresolved_rows()
    ids = {row["instance_id"] for row in rows}
    assert not ids.intersection(B4_IDS)
    assert not ids.intersection(HISTORICAL_SOLVED_IDS)
    assert len(rows) == 15


def test_postb4_selector_is_repo_stratified_and_frozen() -> None:
    rows = canary_rows()
    assert [row["instance_id"] for row in rows] == [
        "sympy__sympy-18211",
        "sphinx-doc__sphinx-9230",
        "astropy__astropy-7671",
        "django__django-15563",
        "matplotlib__matplotlib-24570",
        "sympy__sympy-14711",
    ]
    identity = frozen_selector_identity()
    assert identity["selector_sha256"]
    assert [row["instance_id"] for row in identity["tasks"]] == [
        row["instance_id"] for row in rows
    ]
