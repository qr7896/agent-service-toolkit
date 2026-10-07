import hashlib

import pytest

from evals.e1c_evaluation_2_lossless_context import compact_data_message, encode_windows, restore
from evals.e1c_evaluation_2_probe import input_json


def fixture(tmp_path):
    lines = [f"value_{n} = '{'x' * 55}'" for n in range(80)]
    source = "\n".join(lines)
    (tmp_path / "core.py").write_bytes(source.encode())
    sha = hashlib.sha256(source.encode()).hexdigest()
    rows = [{"path": "core.py", "source_sha256": sha, "start_line": start + 1,
             "end_line": end, "origin": origin, "symbol": "function", "text": "\n".join(lines[start:end])}
            for start, end, origin in [(0, 45, "initial"), (15, 60, "retrieve"), (30, 75, "read")]]
    return {"issue": "Public requirement is preserved exactly.", "windows": rows,
            "public_fixture_facts": [{"literal": 3}], "last_feedback": {"status": "known"}, "previous_probe": None}


def test_overlaps_merge_without_adding_any_source_or_losing_provenance(tmp_path):
    original = fixture(tmp_path)
    encoded, proof = encode_windows(original, tmp_path)
    assert len(encoded["source_segments"]) == 1 and restore(encoded) == original
    assert proof["rehydrated_equal"] and not proof["source_content_added"] and not proof["metadata_dropped"]
    assert proof["encoded_chars"] < proof["original_chars"]
    assert [r["origin"] for r in encoded["windows"]] == ["initial", "retrieve", "read"]


def test_disjoint_source_ranges_never_reveal_the_gap(tmp_path):
    original = fixture(tmp_path)
    original["windows"] = [original["windows"][0], {**original["windows"][2], "start_line": 76,
                              "text": "\n".join((tmp_path / "core.py").read_text().splitlines()[75:80])}]
    encoded, _ = encode_windows(original, tmp_path)
    assert len(encoded["source_segments"]) == 2 and restore(encoded) == original
    assert "value_55" not in input_json(encoded)


def test_hash_or_slice_mismatch_rejected(tmp_path):
    original = fixture(tmp_path)
    original["windows"][0]["text"] = "invented source"
    with pytest.raises(ValueError, match="exact_source_slice"):
        encode_windows(original, tmp_path)
    original = fixture(tmp_path)
    (tmp_path / "core.py").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source_hash_changed"):
        encode_windows(original, tmp_path)


def test_small_payload_with_no_gain_keeps_original_wire_content(tmp_path):
    original = fixture(tmp_path)
    original["windows"] = [{**original["windows"][0], "text": "value_0 = '" + "x" * 55 + "'"}]
    raw = input_json(original)
    wire, proof = compact_data_message(raw, tmp_path)
    assert wire == raw and not proof["applied"]
