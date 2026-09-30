from pathlib import Path

from scripts.wave_b_public_task_discovery import write_probe


def test_write_probe_is_content_neutral(tmp_path: Path) -> None:
    output = tmp_path / "probe.json"
    probe = {
        "transport": "git",
        "url": "https://example.invalid/public.git",
        "reachable": True,
        "head_sha": "a" * 40,
    }

    write_probe(output, probe)

    text = output.read_text(encoding="utf-8")
    assert '"reachable": true' in text
    assert "problem_statement" not in text
    assert '"patch"' not in text
    assert "test_patch" not in text
