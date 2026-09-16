"""Experience Memory：把一条轨迹沉淀成可审计、可复用的结构化经验（阶段 15）。

经验只从阶段 14 的 trajectory 派生——模型的自述不算证据，带 test_result /
review / approvals 的轨迹才算。第一版落 SQLite 本地文件；向量检索留在阶段 16。
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from agents.code_tools import PROJECT_ROOT
from agents.trajectory import redact, utc_now

DEFAULT_EXPERIENCE_PATH = PROJECT_ROOT / ".codex" / "experience" / "experience.db"

ACCEPTED = "accepted"
REJECTED = "rejected"
FAILURE_APPROVAL_DENIED = "approval_denied"
FAILURE_TEST_FAILED = "test_failed"
FAILURE_REVIEW_REJECTED = "review_rejected"
FAILURE_UNKNOWN = "unknown_failure"

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiences (
    id               TEXT PRIMARY KEY,
    trajectory_id    TEXT NOT NULL UNIQUE,
    created_at       TEXT NOT NULL,
    task             TEXT NOT NULL,
    task_key         TEXT NOT NULL,
    outcome          TEXT NOT NULL,
    failure_type     TEXT NOT NULL DEFAULT '',
    effective_steps  TEXT NOT NULL DEFAULT '[]',
    tools_used       TEXT NOT NULL DEFAULT '[]',
    changed_paths    TEXT NOT NULL DEFAULT '[]',
    attempts         INTEGER NOT NULL DEFAULT 0,
    test_summary     TEXT NOT NULL DEFAULT '',
    review_summary   TEXT NOT NULL DEFAULT '',
    approved         INTEGER,
    model            TEXT NOT NULL DEFAULT '',
    duration_seconds REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_experiences_task_key ON experiences(task_key);
CREATE INDEX IF NOT EXISTS idx_experiences_outcome ON experiences(outcome);
"""


def task_key(task: str, limit: int = 40) -> str:
    """任务特征：小写分词 + 去重，供阶段 16 做相似度检索的确定性基线。"""
    tokens: list[str] = []
    seen: set[str] = set()
    for token in _TOKEN_RE.findall((task or "").lower()):
        if len(token) < 2 or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
        if len(tokens) >= limit:
            break
    return " ".join(tokens)


def _classify(trajectory: dict[str, Any]) -> tuple[str, str]:
    """判定 accepted / rejected 与失败类型；人工拒绝优先于测试失败。"""
    status = str(trajectory.get("status") or "")
    if status == "succeeded":
        return ACCEPTED, ""
    approvals = [a for a in trajectory.get("approvals") or [] if isinstance(a, dict)]
    if any(a.get("approved") is False for a in approvals):
        return REJECTED, FAILURE_APPROVAL_DENIED
    test = trajectory.get("test_result") or {}
    if test and test.get("status") != "passed":
        return REJECTED, FAILURE_TEST_FAILED
    review = trajectory.get("review") or {}
    if review.get("approved") is False:
        return REJECTED, FAILURE_REVIEW_REJECTED
    if status == "failed":
        return REJECTED, FAILURE_UNKNOWN
    return "", ""


@dataclass
class Experience:
    id: str
    trajectory_id: str
    created_at: str
    task: str
    task_key: str
    outcome: str
    failure_type: str = ""
    effective_steps: list[dict[str, Any]] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    changed_paths: list[str] = field(default_factory=list)
    attempts: int = 0
    test_summary: str = ""
    review_summary: str = ""
    approved: bool | None = None
    model: str = ""
    duration_seconds: float = 0.0

    def to_row(self) -> tuple:
        return (
            self.id,
            self.trajectory_id,
            self.created_at,
            self.task,
            self.task_key,
            self.outcome,
            self.failure_type,
            json.dumps(self.effective_steps, ensure_ascii=False),
            json.dumps(self.tools_used, ensure_ascii=False),
            json.dumps(self.changed_paths, ensure_ascii=False),
            self.attempts,
            self.test_summary,
            self.review_summary,
            None if self.approved is None else int(self.approved),
            self.model,
            self.duration_seconds,
        )

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Experience":
        data = dict(row)
        for key in ("effective_steps", "tools_used", "changed_paths"):
            try:
                data[key] = json.loads(data.get(key) or "[]")
            except json.JSONDecodeError:
                data[key] = []
        if data.get("approved") is not None:
            data["approved"] = bool(data["approved"])
        return cls(**data)


def build_experiences(trajectory: dict[str, Any]) -> list[Experience]:
    """从一条轨迹派生经验；无可复用信号时返回空列表。"""
    if not isinstance(trajectory, dict):
        return []
    # 只读问答没有代码修复信号，入库会污染后续检索
    if str(trajectory.get("status") or "") == "completed_read_only":
        return []
    outcome, failure_type = _classify(trajectory)
    if not outcome:
        return []

    plan = trajectory.get("plan") or {}
    steps = [
        {
            "order": step.get("order"),
            "action": redact(str(step.get("action") or "")),
            "path": redact(str(step.get("path") or "")),
        }
        for step in (plan.get("steps") or [])
        if isinstance(step, dict)
    ]
    test = trajectory.get("test_result") or {}
    review = trajectory.get("review") or {}
    approvals = [a for a in trajectory.get("approvals") or [] if isinstance(a, dict)]
    approved = next((a.get("approved") for a in approvals if "approved" in a), None)
    task = str(trajectory.get("task") or "")

    return [
        Experience(
            id=str(uuid4()),
            trajectory_id=str(trajectory.get("id") or ""),
            created_at=str(trajectory.get("ended_at") or utc_now()),
            task=redact(task),
            task_key=task_key(task),
            outcome=outcome,
            failure_type=failure_type,
            effective_steps=steps,
            tools_used=sorted((trajectory.get("tool_call_counts") or {}).keys()),
            changed_paths=[redact(p) for p in trajectory.get("changed_paths") or []],
            attempts=int(trajectory.get("attempts") or 0),
            test_summary=redact(str(test.get("summary") or ""))[:500],
            review_summary=redact(str(review.get("summary") or ""))[:500],
            approved=approved if isinstance(approved, bool) else None,
            model=str(trajectory.get("model") or ""),
            duration_seconds=float(trajectory.get("duration_seconds") or 0.0),
        )
    ]


class ExperienceStore:
    """SQLite 经验库。同一 trajectory_id 重复写入会原地更新，不会产生重复经验。"""

    def __init__(self, path: Path | str = DEFAULT_EXPERIENCE_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), timeout=10)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def record(self, experience: Experience) -> str:
        placeholders = ", ".join("?" * 16)
        self._conn.execute(
            f"INSERT INTO experiences VALUES ({placeholders}) "
            "ON CONFLICT(trajectory_id) DO UPDATE SET "
            "created_at=excluded.created_at, task=excluded.task, task_key=excluded.task_key, "
            "outcome=excluded.outcome, failure_type=excluded.failure_type, "
            "effective_steps=excluded.effective_steps, tools_used=excluded.tools_used, "
            "changed_paths=excluded.changed_paths, attempts=excluded.attempts, "
            "test_summary=excluded.test_summary, review_summary=excluded.review_summary, "
            "approved=excluded.approved, model=excluded.model, "
            "duration_seconds=excluded.duration_seconds",
            experience.to_row(),
        )
        self._conn.commit()
        return experience.id

    def record_trajectory(self, trajectory: dict[str, Any]) -> list[str]:
        return [self.record(exp) for exp in build_experiences(trajectory)]

    def recall(self, task: str, limit: int = 3) -> list[Experience]:
        """确定性关键词召回：空库 / 无重叠时返回空列表（阶段 16 换成向量检索）。"""
        query = set(task_key(task).split())
        if not query:
            return []
        scored: list[tuple[int, str, Experience]] = []
        for row in self._conn.execute("SELECT * FROM experiences"):
            experience = Experience.from_row(row)
            overlap = len(query & set(experience.task_key.split()))
            if overlap:
                scored.append((overlap, experience.created_at, experience))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [item[2] for item in scored[:limit]]

    def all(self) -> list[Experience]:
        """按写入时间读出全部经验，供阶段 16 建向量索引。"""
        return [
            Experience.from_row(row)
            for row in self._conn.execute("SELECT * FROM experiences ORDER BY created_at")
        ]

    def stats(self) -> dict[str, Any]:
        total = self._conn.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]
        outcomes = {
            row["outcome"]: row["n"]
            for row in self._conn.execute(
                "SELECT outcome, COUNT(*) AS n FROM experiences GROUP BY outcome"
            )
        }
        failures = {
            row["failure_type"]: row["n"]
            for row in self._conn.execute(
                "SELECT failure_type, COUNT(*) AS n FROM experiences "
                "WHERE failure_type <> '' GROUP BY failure_type"
            )
        }
        return {"total": total, "outcomes": outcomes, "failure_types": failures}

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ExperienceStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def experience_path(config: dict[str, Any]) -> Path:
    configured = (config.get("configurable") or {}).get("experience_path")
    return Path(str(configured)).expanduser() if configured else DEFAULT_EXPERIENCE_PATH


def record_trajectory(trajectory: dict[str, Any], config: dict[str, Any]) -> list[str]:
    """把一条轨迹写进经验库，返回经验 id 列表。"""
    with ExperienceStore(experience_path(config)) as store:
        return store.record_trajectory(trajectory)


__all__ = [
    "DEFAULT_EXPERIENCE_PATH",
    "Experience",
    "ExperienceStore",
    "asdict",
    "build_experiences",
    "experience_path",
    "record_trajectory",
    "task_key",
]
