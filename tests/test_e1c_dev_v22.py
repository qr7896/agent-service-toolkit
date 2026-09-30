from evals import e1c_dev_v22 as dev


def test_frozen_outcome_driven_dev_subset():
    rows = dev._cohort()
    assert len(rows) == 18
    assert tuple(row["instance_id"] for row in rows) == dev.COHORT_IDS
    assert dev.RUN_ID != "e1c-dev-v21-n30-7d8e6569"


def test_primary_evidence_gets_more_context_without_expanding_secondary():
    value = {"excerpts": [{"path": "a.py", "text": "a" * 2000},
                          {"path": "b.py", "text": "b" * 2000}]}
    first = dev._first_payload(value)
    assert len(first["excerpts"][0]["text"]) == 1800
    assert len(first["excerpts"][1]["text"]) == 700
    assert len(value["excerpts"][0]["text"]) == 2000
