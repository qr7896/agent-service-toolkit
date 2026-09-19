"""Experience Memory：把一条轨迹沉淀成可审计、可复用的结构化经验（阶段 15）。

经验只从阶段 14 的 trajectory 派生——模型的自述不算证据，带 test_result /
review / approvals 的轨迹才算。第一版落 SQLite 本地文件；向量检索留在阶段 16。
"""

from __future__ import annotations

import hashlib
import inspect
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
    "schema_version": "str",
    "source_repo": "str",
    "event_time": "str",
    "task_signature": "dict[str, str]",
    "reuse_constraints": "dict[str, list[str]]",
    "repo_commit": "str",
    "likely_effective": "bool | None",
    "retrieval_count": "int",
    "used_count": "int",
    "helped_count": "int",
    "harmful_count": "int",
    "validation_strength": "dict[str, Any]",
    "lifecycle_state": "str",
    "lifecycle_reason": "str",
    "lifecycle_event_time": "str",
    "compiler_config_hash": "str",
}

DOMAIN_HINTS = {
    "fastapi": ("fastapi", "route", "endpoint", "uvicorn", "http"),
    "agent": ("agent", "langgraph", "planner", "tool_call", "prompt"),
    "memory": ("experience", "trajectory", "embedding", "chroma", "retrieval"),
    "deploy": ("docker", "compose", "container", "镜像"),
    "data": ("pandas", "csv", "dataframe", "统计"),
}


# 下游命中驱动的降权阈值：样本太少不判（两次没帮上就隔离太激进），样本够了才按命中率判
UTILITY_MIN_SAMPLES = 3
UTILITY_HELP_RATE_FLOOR = 0.34


def _file_digest(path: Path) -> str:
    if not path.is_file():
        return "missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def fingerprint(paths: list[str], root: Path | None = None, rev: str | None = None) -> str:
    """对一组文件取指纹：`rev` 给定时取那个提交的内容，否则取工作区。

    用途是**延迟复评**：记录时留两个指纹——改动后的工作区（change）与提交基线（baseline），
    以后就能判断这次改动是"还在 / 被回退 / 又被改过"。
    """
    base = Path(root or PROJECT_ROOT)
    parts: list[str] = []
    for rel in sorted(set(paths or [])):
        if rev:
            proc = subprocess.run(
                ["git", "-C", str(base), "show", f"{rev}:{rel}"],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            digest = (
                hashlib.sha256((proc.stdout or "").encode("utf-8", "replace")).hexdigest()[:16]
                if proc.returncode == 0
                else "missing"
            )
        else:
            digest = _file_digest(base / rel)
        parts.append(f"{rel}:{digest}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16] if parts else ""


def repo_commit(root: Path | None = None) -> str:
    """记录经验对应的代码版本：代码变了，经验可能就过期了（doc 02 §11）。"""
    try:
        out = subprocess.run(
            ["git", "-C", str(root or PROJECT_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
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
        language = {"py": "python", "js": "javascript", "ts": "typescript", "go": "go"}.get(
            suffix, suffix
        )
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


def compatibility(experience: Experience, context: dict[str, str]) -> tuple[float, list[str]]:
    """第二层检索：语义相似之外的证据兼容性（doc 02 §8）。

    返回 (0~1 兼容分, 不兼容原因)。任一"硬冲突"会让分数归零，由调用方决定是否弃权。
    """
    extra = experience.extra or {}
    signature = extra.get("task_signature") or {}
    reasons: list[str] = []
    # 下游命中驱动的硬冲突：被隔离的、以及改动被回退的经验都不该再被注入
    if extra.get("isolated"):
        return 0.0, [f"已被隔离：{extra.get('isolation_reason') or '下游命中失败率超标'}"]
    if extra.get("survival") == "reverted":
        return 0.0, ["改动之后被回退（延迟复评发现），不能当正面例子"]
    score = 1.0
    if signature.get("language") and context.get("language") not in (None, "", "unknown"):
        if signature["language"] != context["language"]:
            score = 0.0
            reasons.append(f"语言不兼容（{signature['language']} vs {context['language']}）")
    if signature.get("domain") and context.get("domain"):
        if signature["domain"] != context["domain"] and "general" not in (
            signature["domain"],
            context["domain"],
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


def validation_strength(trajectory: dict[str, Any]) -> dict[str, Any]:
    test = trajectory.get("test_result") or {}
    review = trajectory.get("review") or {}
    approvals = [item for item in trajectory.get("approvals") or [] if isinstance(item, dict)]
    return {
        "test_observed": bool(test),
        "test_passed": test.get("status") == "passed" if test else None,
        "review_observed": bool(review),
        "review_approved": review.get("approved")
        if isinstance(review.get("approved"), bool)
        else None,
        "approval_observed": bool(approvals),
        "write_approved": next(
            (item.get("approved") for item in approvals if isinstance(item.get("approved"), bool)),
            None,
        ),
    }


def compiler_config_hash() -> str:
    payload = {
        "schema_version": "v3-experience-v2",
        "classifier": inspect.getsource(_classify),
        "reuse_constraints": inspect.getsource(reuse_constraints),
        "validation_strength": inspect.getsource(validation_strength),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


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
    def from_row(cls, row: sqlite3.Row) -> Experience:
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


def build_experiences(trajectory: dict[str, Any], root: Path | None = None) -> list[Experience]:
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
    paths = [redact(p) for p in trajectory.get("changed_paths") or []]
    source_commit = str(trajectory.get("source_commit_at_execution") or "")
    change_fingerprint = fingerprint(paths, root)
    baseline_fingerprint = fingerprint(paths, root, rev=source_commit) if source_commit else ""
    sign = 1.0 if outcome == ACCEPTED else -0.5
    action_prior: dict[str, float] = {}
    for item in trajectory.get("evidence_trace") or []:
        action = str(item.get("action") or "")
        if not action:
            continue
        gain = float(item.get("gain") or 0.0)
        cost = max(0.1, float(item.get("cost") or 1.0))
        action_prior[action] = round(sign * gain / cost, 4)

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
            changed_paths=paths,
            attempts=int(trajectory.get("attempts") or 0),
            test_summary=redact(str(test.get("summary") or ""))[:500],
            review_summary=redact(str(review.get("summary") or ""))[:500],
            approved=approved if isinstance(approved, bool) else None,
            model=str(trajectory.get("model") or ""),
            duration_seconds=float(trajectory.get("duration_seconds") or 0.0),
            extra={
                "task_signature": task_signature(
                    task, [redact(p) for p in trajectory.get("changed_paths") or []]
                ),
                "reuse_constraints": reuse_constraints(
                    task,
                    [redact(p) for p in trajectory.get("changed_paths") or []],
                    outcome,
                    failure_type,
                ),
                "schema_version": "v3-experience-v2",
                "source_repo": str(trajectory.get("source_repo") or ""),
                "repo_commit": source_commit,
                "event_time": str(trajectory.get("ended_at") or ""),
                # 规则式归因（doc 02 §13）：跑通测试且有实际改动才算"这一步likely有效"
                "likely_effective": (
                    True
                    if outcome == ACCEPTED and (trajectory.get("changed_paths") or [])
                    else False
                    if outcome == REJECTED
                    else None
                ),
                "retrieval_count": 0,
                "used_count": 0,
                "helped_count": 0,
                "harmful_count": 0,
                "validation_strength": validation_strength(trajectory),
                "lifecycle_state": "active",
                "lifecycle_reason": "",
                "lifecycle_event_time": str(trajectory.get("ended_at") or ""),
                "compiler_config_hash": compiler_config_hash(),
                "action_prior": action_prior,
                # 延迟复评用：改动后的工作区指纹 vs 提交基线指纹
                "change_fingerprint": change_fingerprint,
                "baseline_fingerprint": baseline_fingerprint,
                "applied": (
                    change_fingerprint != baseline_fingerprint
                    if paths and baseline_fingerprint
                    else None
                ),
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

    def update_extra(self, trajectory_id: str, extra: dict[str, Any]) -> bool:
        cursor = self._conn.execute(
            "UPDATE experiences SET extra = ? WHERE trajectory_id = ?",
            (json.dumps(extra, ensure_ascii=False, default=str), trajectory_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

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

    def record_trajectory(self, trajectory: dict[str, Any], root: Path | None = None) -> list[str]:
        return [self.record(exp) for exp in build_experiences(trajectory, root)]

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

    def __enter__(self) -> ExperienceStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def experience_path(config: Any) -> Path:
    configured = (config.get("configurable") or {}).get("experience_path")
    return Path(str(configured)).expanduser() if configured else DEFAULT_EXPERIENCE_PATH


def record_trajectory(trajectory: dict[str, Any], config: Any) -> list[str]:
    """把一条轨迹写进经验库，返回经验 id 列表。"""
    with ExperienceStore(experience_path(config)) as store:
        return store.record_trajectory(trajectory)


def survival_of(experience: Experience, root: Path | None = None) -> str:
    """这次改动活下来了吗：intact / reverted / modified / unknown。

    trajectory 记的是"当时测试通过"，不等于改动后来存活——所以这里做**延迟复评**：
    拿当前内容跟"改动后指纹"和"提交基线指纹"比。回到基线 = 被回退；两个都不一样 = 又被改过。
    """
    extra = experience.extra or {}
    paths = list(experience.changed_paths or [])
    change = str(extra.get("change_fingerprint") or "")
    baseline = str(extra.get("baseline_fingerprint") or "")
    if not paths or not change or not baseline:
        return "unknown"
    if extra.get("applied") is False:
        return "not_applied"  # 沙箱里跑完但补丁没落地：不是回退，只是还没应用
    current = fingerprint(paths, root)
    if current == change:
        return "intact"
    if baseline and current == baseline:
        return "reverted"
    return "modified"


def reevaluate_utility(
    store: ExperienceStore,
    min_samples: int = UTILITY_MIN_SAMPLES,
    help_rate_floor: float = UTILITY_HELP_RATE_FLOOR,
) -> dict[str, list[str]]:
    """下游命中驱动的衰减与隔离：样本够了但命中率低于底线 → 隔离。

    隔离是可逆的：后续命中把命中率拉回底线以上会自动解除——记忆应该能"改过自新"，
    但不该在被证明有害之后继续被注入。
    """
    report: dict[str, list[str]] = {"isolated": [], "revived": [], "kept": []}
    for experience in store.all():
        extra = dict(experience.extra or {})
        used = int(extra.get("used_count") or 0)
        helped = int(extra.get("helped_count") or 0)
        if used < min_samples:
            report["kept"].append(experience.trajectory_id)
            continue
        rate = helped / used
        should_isolate = rate < help_rate_floor
        was_isolated = bool(extra.get("isolated"))
        if should_isolate and not was_isolated:
            extra["isolated"] = True
            extra["isolation_reason"] = (
                f"下游命中 {used} 次仅帮上 {helped} 次（命中率 {rate:.2f} < {help_rate_floor}）"
            )
            store.update_extra(experience.trajectory_id, extra)
            report["isolated"].append(experience.trajectory_id)
        elif not should_isolate and was_isolated:
            extra["isolated"] = False
            extra["isolation_reason"] = f"命中率回升到 {rate:.2f}，解除隔离"
            store.update_extra(experience.trajectory_id, extra)
            report["revived"].append(experience.trajectory_id)
        else:
            report["kept"].append(experience.trajectory_id)
    return report


def reevaluate_survival(store: ExperienceStore, root: Path | None = None) -> dict[str, list[str]]:
    """延迟复评：把"改动是否存活"写回经验，被回退的直接标成不可再用。

    侥幸通过（当时测试过了、后来被 revert）在这一步才会暴露；只靠写入时的质量分看不出来。
    """
    report: dict[str, list[str]] = {
        "intact": [],
        "reverted": [],
        "modified": [],
        "unknown": [],
        "not_applied": [],
    }
    for experience in store.all():
        state = survival_of(experience, root)
        extra = dict(experience.extra or {})
        if extra.get("survival") == state:
            report[state].append(experience.trajectory_id)
            continue
        extra["survival"] = state
        if state == "reverted":
            # 改动被回退 → 这条经验不能再当正面例子
            extra["likely_effective"] = False
            extra["reverted_reason"] = "改动之后回到提交基线（被回退或撤销）"
        store.update_extra(experience.trajectory_id, extra)
        report[state].append(experience.trajectory_id)
    return report


def record_usage_for_trajectory(trajectory: dict[str, Any], config: Any) -> dict[str, Any]:
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
    "fingerprint",
    "reevaluate_survival",
    "reevaluate_utility",
    "repo_commit",
    "record_trajectory",
    "record_usage_for_trajectory",
    "reuse_constraints",
    "survival_of",
    "task_signature",
    "task_key",
]
