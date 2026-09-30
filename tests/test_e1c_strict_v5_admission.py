from evals.e1c_strict_v5_admission import AdmissionRow, evaluate


def _row(instance_id: str, trusted: bool = True) -> AdmissionRow:
    return AdmissionRow(
        instance_id=instance_id,
        identity_frozen=True,
        projection_status="projected",
        source_commit_matches=True,
        image_present=True,
        base_fail=True,
        gold_pass=True,
        trusted_reproducer=trusted,
        leakage_free=True,
        infrastructure_ok=True,
    )


def test_admission_requires_two_of_three_trusted_reproducers() -> None:
    assert evaluate([_row("a"), _row("b"), _row("c", False)])["ready"] is True
    result = evaluate([_row("a"), _row("b", False), _row("c", False)])
    assert result["ready"] is False
    assert result["checks"]["trusted_reproducer_minimum"] is False


def test_admission_fails_closed_on_any_identity_or_leakage_issue() -> None:
    bad = AdmissionRow(**{**_row("c").as_dict(), "leakage_free": False})
    result = evaluate([_row("a"), _row("b"), bad])
    assert result["ready"] is False
    assert result["checks"]["leakage_free"] is False
