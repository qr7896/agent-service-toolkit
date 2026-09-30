import csv
import json

from evals.e1c_strict_v5_metadata_import import audit_source, freeze_source


def _row(instance_id: str, digit: str) -> dict:
    return {
        "instance_id": instance_id,
        "repo": "owner/repo",
        "base_commit": digit * 40,
        "image": f"swebench/{instance_id}:latest",
    }


def test_jsonl_and_csv_metadata_sources_are_supported(tmp_path) -> None:
    rows = [_row("unseen-a", "a"), _row("unseen-b", "b"), _row("unseen-c", "c")]
    jsonl = tmp_path / "pool.jsonl"
    jsonl.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    assert audit_source(jsonl, source_revision="rev")["eligible_count"] == 3

    csv_path = tmp_path / "pool.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert audit_source(csv_path, source_revision="rev")["eligible_count"] == 3


def test_freeze_source_writes_audit_and_manifest(tmp_path) -> None:
    rows = [_row("new-a", "a"), _row("new-b", "b"), _row("new-c", "c"), _row("new-d", "d")]
    source = tmp_path / "pool.json"
    source.write_text(json.dumps(rows), encoding="utf-8")
    audit = tmp_path / "audit.json"
    manifest = tmp_path / "manifest.json"
    result = freeze_source(
        source,
        source_revision="immutable-rev",
        output=manifest,
        audit_output=audit,
    )
    assert audit.is_file()
    assert manifest.is_file()
    assert result["task_count"] == 3
    assert result["provider_calls"] == 0
