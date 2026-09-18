"""Offline A-G retrieval benchmark for the 20-task Research Mode seed set.

No chat model is called.  The semantic arm uses the local embedding already
configured by the project; all other arms are deterministic static analysis.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from agents import code_intel  # noqa: E402
from agents.code_semantic import semantic_search  # noqa: E402
from agents.context_packer import ContextItem, pack_context  # noqa: E402
from agents.retrieval_actions import extract_artifacts  # noqa: E402
from evals.retrieval_metrics import aggregate, task_metrics  # noqa: E402
from evals.swe_tasks import TaskSpec, load_tasks, prepare  # noqa: E402

TASKS = ROOT / "evals" / "tasks" / "research_v0.jsonl"
RESULT = ROOT / "evals" / "results" / "retrieval_v0.json"
ARMS = ("A", "B", "C", "D", "E", "F", "G")
BACKEND_COST = {"files": 0.2, "lexical": 1.5, "semantic": 2.0, "structural": 1.0}


@dataclass
class Run:
    instance_id: str
    arm: str
    budget: int
    actions: list[str]
    retrieval_trace: list[dict[str, Any]]
    estimated_tokens: int
    tool_calls: int
    cost: float
    latency_ms: float
    retrieval_abstained: bool = False


def identifiers(text: str) -> set[str]:
    stop = {"python", "true", "false", "return", "test", "tests", "src", "agent"}
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text)
        if token.lower() not in stop
    }


def _symbols(path: Path) -> list[tuple[str, int]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    return [
        (node.name, node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def backend_outputs(spec: TaskSpec, root: Path, embedding: Any) -> dict[str, str]:
    query = spec.problem_statement
    needles = identifiers(query)
    py_files = sorted(root.rglob("*.py"))
    files = "\n".join(path.relative_to(root).as_posix() for path in py_files)

    lexical_hits: list[tuple[int, str]] = []
    for path in py_files:
        rel = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8", errors="replace")
        for name, line in _symbols(path):
            score = int(name.lower() in needles) * 3 + sum(
                token in f"{rel} {name} {source}".lower() for token in needles
            )
            if score:
                lexical_hits.append((score, f"{rel}:{line} lexical {name}"))
    lexical = "\n".join(text for _score, text in sorted(lexical_hits, reverse=True)[:12])

    semantic = semantic_search(query, root, limit=12, embedding_function=embedding)
    index = code_intel.build_index(root, refresh=True)
    structural_lines: list[str] = []
    # CodeGraph baseline exposes the repository's symbol/caller/test graph.  The
    # context budget, not hidden gold labels, decides how much of it survives.
    targets = list(index.symbols)
    for name in sorted(targets):
        structural_lines += [
            f"{symbol.path}:{symbol.lineno} function {name}" for symbol in index.symbols[name]
        ]
        structural_lines += [
            f"caller {caller}" for caller in sorted(index.callers.get(name, set()))
        ]
        structural_lines += sorted(index.tests.get(name, set()))
    return {
        "files": files,
        "lexical": lexical,
        "semantic": semantic,
        "structural": "\n".join(structural_lines),
    }


def _merge(
    outputs: dict[str, str],
    actions: list[str],
    budget: int,
    dedupe: bool = True,
    line_limit: int | None = None,
) -> Run:
    started = time.perf_counter()
    items: list[ContextItem] = []
    seen: set[str] = set()
    for action in actions:
        for rank, line in enumerate(outputs[action].splitlines(), start=1):
            if not line.strip() or (dedupe and line in seen):
                continue
            seen.add(line)
            items.append(ContextItem(action, line, 1.0 / rank))
    if line_limit is not None:
        items = sorted(items, key=lambda item: item.relevance, reverse=True)[:line_limit]
    packed = pack_context(items, budget)
    trace = [
        {
            "round": round_no,
            "action": action,
            "cost": BACKEND_COST[action],
            "artifacts": extract_artifacts(packed.text(action)),
        }
        for round_no, action in enumerate(actions, start=1)
    ]
    return Run(
        instance_id="",
        arm="",
        budget=budget,
        actions=actions,
        retrieval_trace=trace,
        estimated_tokens=packed.tokens,
        tool_calls=len(actions),
        cost=round(sum(BACKEND_COST[action] for action in actions), 2),
        latency_ms=round((time.perf_counter() - started) * 1000, 3),
        retrieval_abstained=not packed.items,
    )


def _sufficient(outputs: dict[str, str], actions: list[str]) -> bool:
    merged = "\n".join(outputs[action] for action in actions)
    artifacts = extract_artifacts(merged)
    return bool(artifacts["files"] and artifacts["symbols"] and artifacts["tests"])


def adaptive(
    outputs: dict[str, str], preferred: str = "lexical", codegraph: bool = True
) -> list[str]:
    actions: list[str] = []
    first = preferred if preferred in {"lexical", "semantic", "structural"} else "lexical"
    if first == "structural" and not codegraph:
        first = "lexical"
    actions.append(first)
    if _sufficient(outputs, actions):
        return actions
    if codegraph and "structural" not in actions:
        actions.append("structural")
    if _sufficient(outputs, actions):
        return actions
    for action in ("semantic", "lexical", "files"):
        if action not in actions:
            actions.append(action)
        if _sufficient(outputs, actions):
            break
    return actions


def arm_actions(arm: str, outputs: dict[str, str], preferred: str = "lexical") -> list[str]:
    fixed = {
        "A": ["files"],
        "B": ["lexical"],
        "C": ["semantic"],
        "D": ["structural"],
        "E": ["lexical", "semantic", "structural"],
    }
    if arm in fixed:
        return fixed[arm]
    return adaptive(outputs, preferred if arm == "G" else "lexical")


def gold(spec: TaskSpec) -> dict[str, list[str]]:
    return {
        "gold_files": spec.gold_files,
        "gold_symbols": spec.gold_symbols,
        "gold_callers": spec.gold_callers,
        "gold_tests": spec.gold_tests,
        "gold_context": spec.gold_context,
    }


def score(run: Run, spec: TaskSpec) -> dict[str, Any]:
    metrics = task_metrics(asdict(run), gold(spec))
    return {**asdict(run), **metrics, "task_type": spec.task_type, "cluster": spec.cluster}


def preferred_actions(
    tasks: list[TaskSpec], cached: dict[str, dict[str, str]], budget: int
) -> dict[str, str]:
    scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for spec in tasks:
        for action in ("lexical", "semantic", "structural"):
            run = _merge(cached[spec.instance_id], [action], budget)
            value = task_metrics(asdict(run), gold(spec)).get("context_recall") or 0.0
            scores[spec.cluster][action].append(value / BACKEND_COST[action])
    return {
        cluster: max(actions, key=lambda action: sum(actions[action]) / len(actions[action]))
        for cluster, actions in scores.items()
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base = aggregate(rows)
    return {
        **base,
        "avg_tool_calls": round(sum(row["tool_calls"] for row in rows) / len(rows), 4),
        "avg_cost": round(sum(row["cost"] for row in rows) / len(rows), 4),
        "avg_selection_latency_ms": round(sum(row["latency_ms"] for row in rows) / len(rows), 4),
    }


def add_distractors(root: Path, count: int = 12) -> None:
    for number in range(count):
        (root / f"distractor_{number}.py").write_text(
            "def allowed(data):\n    return data\n\n"
            "def parse(data):\n    return {'unrelated': data}\n\n"
            "def test_fix(data=None):\n    return data\n",
            encoding="utf-8",
        )


def run_benchmark(
    tasks_path: Path = TASKS, budgets: tuple[int, ...] = (2000, 4000, 8000, 16000)
) -> dict[str, Any]:
    from agents.tools import get_embeddings

    tasks = load_tasks(tasks_path)
    embedding = get_embeddings()
    cached: dict[str, dict[str, str]] = {}
    distractor_cached: dict[str, dict[str, str]] = {}
    with tempfile.TemporaryDirectory(prefix="retrieval-v0-") as temp:
        base = Path(temp)
        for spec in tasks:
            root = prepare(spec, base / spec.instance_id)
            cached[spec.instance_id] = backend_outputs(spec, root, embedding)
            if spec.split == "test":
                noisy = base / f"{spec.instance_id}-noisy"
                prepare(spec, noisy)
                add_distractors(noisy)
                distractor_cached[spec.instance_id] = backend_outputs(spec, noisy, embedding)

    train = [spec for spec in tasks if spec.split == "train"]
    eval_tasks = [spec for spec in tasks if spec.split in {"dev", "test"}]
    priors = preferred_actions(train, cached, 8000)
    rows: list[dict[str, Any]] = []
    for budget in budgets:
        for spec in eval_tasks:
            for arm in ARMS:
                actions = arm_actions(
                    arm, cached[spec.instance_id], priors.get(spec.cluster, "lexical")
                )
                run = _merge(cached[spec.instance_id], actions, budget)
                run.instance_id, run.arm = spec.instance_id, arm
                rows.append(score(run, spec))

    arm_summary = {
        str(budget): {
            arm: summarize([row for row in rows if row["budget"] == budget and row["arm"] == arm])
            for arm in ARMS
        }
        for budget in budgets
    }

    stop_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for spec in eval_tasks:
        outputs = cached[spec.instance_id]
        hybrid_lines = ["lexical", "semantic", "structural"]
        for k in (3, 5, 10):
            run = _merge(outputs, hybrid_lines, 16000, line_limit=k)
            stop_rows[f"fixed_k{k}"].append(score(run, spec))
        evidence_run = _merge(outputs, adaptive(outputs), 16000)
        stop_rows["evidence_gate"].append(score(evidence_run, spec))
        utility_run = _merge(outputs, adaptive(outputs, priors.get(spec.cluster, "lexical")), 16000)
        stop_rows["utility_gate"].append(score(utility_run, spec))

    ablations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for spec in eval_tasks:
        outputs = cached[spec.instance_id]
        variants = {
            "full_G": arm_actions("G", outputs, priors.get(spec.cluster, "lexical")),
            "-Coverage": ["lexical", "structural", "semantic", "files"],
            "-Uncertainty": arm_actions("G", outputs, priors.get(spec.cluster, "lexical")),
            "-Redundancy": ["lexical", "semantic", "structural", "lexical"],
            "-Cost": ["semantic", "structural", "lexical", "files"],
            "-CodeGraph": adaptive(outputs, priors.get(spec.cluster, "lexical"), False),
            "-Experience": arm_actions("F", outputs),
        }
        for name, actions in variants.items():
            run = _merge(outputs, actions, 8000, dedupe=name != "-Redundancy")
            ablations[name].append(score(run, spec))

    noisy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    test_tasks = [spec for spec in tasks if spec.split == "test"]
    stale_priors = dict(zip(priors, reversed(list(priors.values()))))
    for spec in test_tasks:
        outputs = distractor_cached[spec.instance_id]
        for name, preferred in {
            "F_noisy": "lexical",
            "G_noisy": priors.get(spec.cluster, "lexical"),
            "G_stale_prior": stale_priors.get(spec.cluster, "semantic"),
        }.items():
            run = _merge(outputs, adaptive(outputs, preferred), 8000)
            noisy[name].append(score(run, spec))

    return {
        "protocol": {
            "tasks": len(tasks),
            "evaluated": len(eval_tasks),
            "train_dev_test": [12, 4, 4],
            "paid_model_calls": 0,
            "budgets": list(budgets),
            "experience_priors": priors,
        },
        "arms": arm_summary,
        "stopping": {name: summarize(values) for name, values in stop_rows.items()},
        "ablations": {name: summarize(values) for name, values in ablations.items()},
        "robustness": {name: summarize(values) for name, values in noisy.items()},
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, default=TASKS)
    parser.add_argument("--output", type=Path, default=RESULT)
    parser.add_argument("--include-rows", action="store_true")
    args = parser.parse_args()
    report = run_benchmark(args.tasks)
    persisted = (
        report
        if args.include_rows
        else {key: value for key, value in report.items() if key != "rows"}
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(persisted, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(persisted, ensure_ascii=False, indent=2))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
