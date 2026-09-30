from evals.e1c_blind_repro_v3_selector import (
    EXCLUDED_IDS,
    canary_rows,
    eligible_final_rows,
    frozen_selector_identity,
)


def test_v3_final_selector_is_non_overlapping_and_pre_statement_frozen() -> None:
    rows = canary_rows()
    ids = [row["instance_id"] for row in rows]
    assert ids == [
        "django__django-15957",
        "django__django-12754",
        "django__django-15280",
    ]
    assert not set(ids).intersection(EXCLUDED_IDS)
    assert len(eligible_final_rows()) == 3
    identity = frozen_selector_identity()
    assert identity["statement_content_inspected_before_freeze"] is False
    assert identity["selector_sha256"]
