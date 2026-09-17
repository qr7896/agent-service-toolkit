"""Experience Memory：把一条轨迹沉淀成可审计、可复用的结构化经验（阶段 15）。

经验只从阶段 14 的 trajectory 派生——模型的自述不算证据，带 test_result /
review / approvals 的轨迹才算。第一版落 SQLite 本地文件；向量检索留在阶段 16。
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
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
    duration_seconds REAL NOT NULL DEFAULT 0,
    extra            TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_experiences_task_key ON experiences(task_key);
CREATE INDEX IF NOT EXISTS idx_experiences_outcome ON experiences(outcome);
"""

# 深化用的附加字段都塞进一列 JSON：本地单进程够用，也避免每次加字段都改表结构
EXTRA_COLUMNS: dict[str, str] = {
    "task_signature": "dict[str, str]",
    "reuse_constraints": "dict[str, list[str]]",
    "repo_commit": "str",
    "likely_effective": "bool | None",
    "retrieval_count": "int",
    "used_count": "int",
    "helped_count": "int",
    "harmful_count": "int",
}

DOMAIN_HINTS = {
    "fastapi": ("fastapi", "route", "endpoint", "uvicorn", "http"),
    "agent": ("agent", "langgraph", "planner", "tool_call", "prompt"),
    "memory": ("experience", "trajectory", "embedding", "chroma", "retrieval"),
    "deploy": ("docker", "compose", "container", "镜像"),
    "data": ("pandas", "csv", "dataframe", "统计"),
}


def repo_commit() -> str:
    """记录经验对应的代码版本：代码变了，经验可能就过期了（doc 02 §11）。"""
    try:
        out = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def task_signature(task: str, changed_paths: list[str] | None = None) -> dict[str, str]:
    """任务签名：用确定性规则抽取 domain / issue_type / language，供兼容性判断。"""
    text = (task or "").lower()
    paths = [p.lower() for p in (changed_paths or [])]
    blob = f"{text} {' '.join(paths)}"
    domain = "general"
    for name, hints in DOMAIN_HINTS.items():
        if any(hint in blob for hint in hints):
            domain = name
            break
    if any(word in text for word in ("修复", "报错", "bug", "失败", "fix")):
        issue = "bug_fix"
    elif any(word in text for word in ("新增", "添加", "支持", "add", "feat")):
        issue = "feature"
    elif any(word in text for word in ("重构", "整理", "简化", "refactor")):
        issue = "refactor"
    elif any(word in text for word in ("测试", "test", "验证")):
        issue = "test"
    else:
        issue = "other"
    if paths:
        suffix = paths[0].rsplit(".", 1)[-1]
        language = {"py": "python", "js": "javascript", "ts": "typescript", "go": "go"}.get(suffix, suffix)
    else:
        language = "python" if "python" in blob or ".py" in blob else "unknown"
    return {"domain": domain, "issue_type": issue, "language": language}


def reuse_constraints(
    task: str, changed_paths: list[str], outcome: str, failure_type: str
) -> dict[str, list[str]]:
    """适用 / 不适用条件（doc 02 §6）：让经验带上边界，而不是"以后照做"。"""
    signature = task_signature(task, changed_paths)
    applicable = [f"domain={signature['domain']}", f"language={signature['language']}"]
    not_applicable: list[str] = []
    if outcome == ACCEPTED:
        applicable.append(f"issue_type={signature['issue_type']}")
        not_applicable.append("目标文件与当时不同（先确认结构仍相似）")
    else:
        not_applicable.append(f"重复这条路径：当时失败类型是 {failure_type or 'unknown'}")
    return {"applicable_when": applicable, "not_applicable_when": not_applicable}


def compatibility(experience: "Experience", context: dict[str, str]) -> tuple[float, list[str]]:
    """第二层检索：语义相似之外的证据兼容性（doc 02 §8）。

    返回 (0~1 兼容分, 不兼容原因)。任一"硬冲突"会让分数归零，由调用方决定是否弃权。
    """
    extra = experience.extra or {}
    signature = extra.get("task_signature") or {}
    reasons: list[str] = []
    score = 1.0
    if signature.get("language") and context.get("language") not in (None, "", "unknown"):
        if signature["language"] != context["language"]:
            score = 0.0
            reasons.append(f"语言不兼容（{signature['language']} vs {context['language']}）")
    if signature.get("domain") and context.get("domain"):
        if signature["domain"] != context["domain"] and "general" not in (
            signature["domain"], context["domain"],
        ):
            score = min(score, 0.4)
            reasons.append(f"领域不同（{signature['domain']} vs {context['domain']}）")
    recorded_commit = extra.get("repo_commit") or ""
    if recorded_commit and context.get("repo_commit") and recorded_commit != context["repo_commit"]:
        score = min(score, 0.7)
        reasons.append(f"代码版本已变化（{recorded_commit} → {context['repo_commit']}）")
    quality = extra.get("likely_effective")
    if quality is False:
        score = min(score, 0.5)
        reasons.append("该经验对应的动作当时并不有效")
    return round(score, 3), reasons


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
    extra: dict[str, Any] = field(default_factory=dict)

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
            json.dumps(self.extra, ensure_ascii=False, default=str),
        )

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Experience":
        data = dict(row)
        for key in ("effective_steps", "tools_used", "changed_paths"):
            try:
                data[key] = json.loads(data.get(key) or "[]")
            except json.JSONDecodeError:
                data[key] = []
        try:
            data["extra"] = json.loads(data.get("extra") or "{}")
        except json.JSONDecodeError:
            data["extra"] = {}
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
            extra={
                "task_signature": task_signature(task, [redact(p) for p in trajectory.get("changed_paths") or []]),
                "reuse_constraints": reuse_constraints(
                    task,
                    [redact(p) for p in trajectory.get("changed_paths") or []],
                    outcome,
                    failure_type,
                ),
                "repo_commit": repo_commit(),
                # 规则式归因（doc 02 §13）：跑通测试且有实际改动才算"这一步likely有效"
                "likely_effective": (
                    True if outcome == ACCEPTED and (trajectory.get("changed_paths") or []) else
                    False if outcome == REJECTED else None
                ),
                "retrieval_count": 0,
                "used_count": 0,
                "helped_count": 0,
                "harmful_count": 0,
            },
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
        # 轻量迁移：早期版本的库没有 extra 列，补上而不是让老库直接报错
        columns = {row["name"] for row in self._conn.execute("PRAGMA table_info(experiences)")}
        if "extra" not in columns:
            self._conn.execute(
                "ALTER TABLE experiences ADD COLUMN extra TEXT NOT NULL DEFAULT '{}'"
            )
        self._conn.commit()

    def record(self, experience: Experience) -> str:
        placeholders = ", ".join("?" * 17)
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

    def get(self, trajectory_id: str) -> Experience | None:
        row = self._conn.execute(
            "SELECT * FROM experiences WHERE trajectory_id = ?", (trajectory_id,)
        ).fetchone()
        return Experience.from_row(row) if row else None

    def record_usage(self, trajectory_ids: list[str], helped: bool) -> int:
        """记录"这条经验被用过、并且有没有帮上忙"（doc 02 §14 的效用闭环）。

        真实收益统计要用时间切分的留出任务，这里的计数只是原始素材，不是结论。
        """
        touched = 0
        for trajectory_id in trajectory_ids:
            experience = self.get(trajectory_id)
            if experience is None:
                continue
            extra = dict(experience.extra or {})
            extra["retrieval_count"] = int(extra.get("retrieval_count") or 0) + 1
            extra["used_count"] = int(extra.get("used_count") or 0) + 1
            key = "helped_count" if helped else "harmful_count"
            extra[key] = int(extra.get(key) or 0) + 1
            self._conn.execute(
                "UPDATE experiences SET extra = ? WHERE trajectory_id = ?",
                (json.dumps(extra, ensure_ascii=False, default=str), trajectory_id),
            )
            touched += 1
        self._conn.commit()
        return touched

    def utility(self) -> dict[str, dict[str, Any]]:
        """按经验汇总"用了多少次、帮上多少次"。样本少时只作参考。"""
        report: dict[str, dict[str, Any]] = {}
        for row in self._conn.execute("SELECT trajectory_id, task, extra FROM experiences"):
            try:
                extra = json.loads(row["extra"] or "{}")
            except json.JSONDecodeError:
                extra = {}
            used = int(extra.get("used_count") or 0)
            report[row["trajectory_id"]] = {
                "task": row["task"][:60],
                "used": used,
                "helped": int(extra.get("helped_count") or 0),
                "harmful": int(extra.get("harmful_count") or 0),
                "help_rate": round(int(extra.get("helped_count") or 0) / used, 3) if used else None,
            }
        return report

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


def record_usage_for_trajectory(
    trajectory: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    """把"这次任务用过哪些经验、有没有帮上忙"写回经验库（doc 02 §14 的闭环）。

    这是经验唯一能被评价的入口：没有它，`helped_count` 永远是 0，
    "哪条经验真的有用"就只能靠印象说。

    `helped` 的判据用**任务最终状态**，不用模型自述：成功算帮上，失败算有害/无用。
    单条经验的真实效用还需要留出任务与时间切分才能统计（见 benchmark 的 --holdout）。
    """
    hits = trajectory.get("experience_hits") or []
    source_ids = sorted({str(hit.get("trajectory_id") or "") for hit in hits} - {""})
    outcome = {
        "retrieved": len(source_ids),
        "recorded": 0,
        "helped": bool(trajectory.get("status") == "succeeded"),
        "phases": sorted({str(hit.get("phase") or "unknown") for hit in hits}),
    }
    if not source_ids:
        return outcome
    with ExperienceStore(experience_path(config)) as store:
        outcome["recorded"] = store.record_usage(source_ids, helped=outcome["helped"])
    return outcome


__all__ = [
    "DEFAULT_EXPERIENCE_PATH",
    "EXTRA_COLUMNS",
    "Experience",
    "ExperienceStore",
    "asdict",
    "build_experiences",
    "compatibility",
    "experience_path",
    "repo_commit",
    "record_trajectory",
    "reuse_constraints",
    "task_signature",
    "task_key",
]
