from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from evals.v2_dataset import validate_records
from evals.v2_offline_collector import collect_deterministic_record


def _runtime_state(episode: dict) -> dict:
    candidates = episode.get("candidates") or []
    first_features = candidates[0].get("features", {}) if candidates else {}
    allowed = {
        "round", "actions_tried", "tokens_spent", "cost_spent",
        "artifact_files", "artifact_symbols", "artifact_tests", "artifact_callers",
    }
    state = {key: first_features[key] for key in allowed if key in first_features}
    state.update({
        "split": episode.get("split"),
        "cluster": episode.get("cluster"),
        "source_commit": episode.get("source_commit"),
        "source": "v1_decision_episodes",
    })
    return state


def convert_v1_episode(episode: dict):
    actions = [candidate["action"] for candidate in episode.get("candidates", [])]
    chosen = episode.get("oracle_best_action") or "stop"
    if chosen == "stop" and "stop" not in actions:
        actions.append("stop")
    scores = {candidate["action"]: float(candidate["features"].get("candidate_cost", 0.0)) * -1 for candidate in episode.get("candidates", [])}
    if "stop" in actions:
        scores.setdefault("stop", 0.0)
    return collect_deterministic_record(
        task_id=episode["instance_id"],
        step=int(episode["decision"]),
        state=_runtime_state(episode),
        actions=actions,
        chosen_action=chosen,
        policy_scores=scores,
    )


def convert_file(source: Path, output: Path, manifest: Path) -> dict:
    episodes = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = [convert_v1_episode(episode).to_dict() for episode in episodes]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in records) + "\n", encoding="utf-8")
    validation = validate_records(records)
    summary = {
        **validation,
        "source": str(source).replace("\\", "/"),
        "output": str(output).replace("\\", "/"),
        "source_episodes": len(episodes),
        "split_records": dict(sorted(Counter(row["state"].get("split") for row in records).items())),
        "clusters": sorted({row["state"].get("cluster") for row in records if row["state"].get("cluster")}),
        "source_commits": sorted({row["state"].get("source_commit") for row in records if row["state"].get("source_commit")}),
        "provenance": "derived_from_existing_v1_offline_episodes_no_new_model_calls",
    }
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main():
    source = Path("evals/results/v1_decision_episodes.jsonl")
    output = Path("evals/results/v2_seed_decisions_from_v1.jsonl")
    manifest = Path("evals/results/v2_seed_decisions_manifest.json")
    print(json.dumps(convert_file(source, output, manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
