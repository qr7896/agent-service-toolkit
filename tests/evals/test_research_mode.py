from pathlib import Path

from agents.code_semantic import semantic_search
from agents.context_packer import ContextItem, pack_context
from agents.evidence import EvidenceState, audit_plan
from agents.retrieval_actions import extract_artifacts
from agents.retrieval_policy import choose
from agents.trajectory import build_trajectory
from evals.adaptive_retrieval_benchmark import _merge, adaptive
from evals.retrieval_metrics import task_metrics
from evals.swe_tasks import load_tasks


def test_research_seed_metadata() -> None:
    tasks = load_tasks(Path("evals/tasks/research_v0.jsonl"))
    assert len(tasks) == 20
    assert {task.task_type for task in tasks} == {f"T{i}" for i in range(1, 11)}
    assert [sum(task.split == split for task in tasks) for split in ("train", "dev", "test")] == [
        12,
        4,
        4,
    ]
    assert all(
        task.gold_verified
        and task.gold_files
        and task.gold_symbols
        and task.gold_callers
        and task.gold_tests
        and task.gold_context
        for task in tasks
    )


def test_evidence_trace_records_decision_episode(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    plan = {
        "task": "修改 add",
        "steps": [{"order": 1, "path": "mod.py", "reason": "修改 add"}],
        "verification": [],
    }
    _decision, _cards, trace = audit_plan(plan, root=tmp_path)
    assert trace
    assert {
        "round",
        "evidence_state",
        "action",
        "observation",
        "gain",
        "cost",
        "artifacts",
    } <= trace[0].keys()
    assert {"before", "after"} == trace[0]["evidence_state"].keys()


def test_trajectory_has_episode_summary() -> None:
    state = {
        "messages": [],
        "test_result": {"status": "passed"},
        "review": {"approved": True},
        "experience_hits": [{"trajectory_id": "old-1"}],
        "evidence_cards": [{"target_symbols": ["add"], "related_tests": ["test_add"]}],
        "evidence_trace": [{"filled": "impact"}],
    }
    record = build_trajectory(state, {"configurable": {}})
    assert record["experience_ids"] == ["old-1"]
    assert record["evidence_types"] == ["episodic", "impact", "target", "verification"]
    assert record["final_success"] is True


def test_context_packer_obeys_budget() -> None:
    packed = pack_context(
        [ContextItem("recon", "a" * 40, 1.0), ContextItem("experience", "b" * 80, 0.1)],
        10,
    )
    assert packed.tokens <= 10
    assert packed.text("recon") == "a" * 40
    assert packed.dropped == 1


def test_semantic_code_search_with_injected_embedding(tmp_path: Path) -> None:
    (tmp_path / "alpha.py").write_text(
        "def add_invoice():\n    return 'invoice'\n", encoding="utf-8"
    )
    (tmp_path / "beta.py").write_text("def delete_user():\n    return 'user'\n", encoding="utf-8")

    class Embedding:
        @staticmethod
        def vector(text: str) -> list[float]:
            return [float("invoice" in text), float("user" in text)]

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [self.vector(text) for text in texts]

        def embed_query(self, text: str) -> list[float]:
            return self.vector(text)

    result = semantic_search("invoice", tmp_path, limit=1, embedding_function=Embedding())
    assert result.startswith("alpha.py:1 semantic add_invoice")


def test_experience_prior_changes_action_choice() -> None:
    plan = choose(
        EvidenceState(),
        experience_hits=[{"action_prior": {"semantic_search": 1.0}, "compatibility": 1.0}],
    )
    assert plan.action == "semantic_search"


def test_semantic_artifact_parser_ignores_score() -> None:
    artifacts = extract_artifacts("src/a.py:7 semantic do_work score=0.9000\ncaller api\n")
    assert artifacts["symbols"] == ["api", "do_work"]
    assert artifacts["callers"] == ["api"]


def test_adaptive_and_experience_prior_stop_earlier() -> None:
    outputs = {
        "files": "src/a.py",
        "lexical": "src/a.py:1 lexical do_work",
        "semantic": "src/a.py:1 semantic do_work score=1.0",
        "structural": "src/a.py:1 function do_work\ncaller api\ntest_a.py::test_fix",
    }
    assert adaptive(outputs) == ["lexical", "structural"]
    assert adaptive(outputs, preferred="structural") == ["structural"]
    assert _merge(outputs, adaptive(outputs), 2000).tool_calls == 2


def test_caller_recall_is_measured() -> None:
    row = task_metrics(
        {"retrieval_trace": [{"artifacts": {"callers": ["api"]}}]},
        {"gold_callers": ["api", "cli"]},
    )
    assert row["gold_caller_recall"] == 0.5
