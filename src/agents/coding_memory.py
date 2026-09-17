"""Experience Retrieval：把阶段 15 的经验检索出来交给 Planner（阶段 16）。

路线图 §26 的形态：`User Task → Experience Retrieval → 找类似历史任务 → Planner`。
例如历史任务"FastAPI 路由注册导致 404"应当能被新任务"FastAPI endpoint 找不到"
召回，即使两者几乎没有共同关键词，所以这里用 BGE-M3 + Chroma 做语义检索。

两条硬约束：
  1) 无命中时必须是**完全的无操作**——Planner 拿到的提示词与没有本模块时逐字一致；
  2) 检索结果必须带 `trajectory_id`，让模型知道"这是有证据的历史"，而不是它的先验知识。

依赖（BGE-M3 / Chroma）不可用时自动退回阶段 15 的关键词召回，并在结果里标注
`retrieval="keyword"`，让上层知道自己拿到的是哪种证据。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from agents.code_tools import PROJECT_ROOT
from agents.experience import (
    ACCEPTED,
    Experience,
    ExperienceStore,
    compatibility,
    experience_path,
    repo_commit,
    task_signature,
)

DEFAULT_CHROMA_DIR = PROJECT_ROOT / ".codex" / "experience" / "chroma"
COLLECTION_NAME = "coding_experience"
DEFAULT_TOP_K = 3
# 相关性下限（余弦）。BGE-M3 对中文短句的相似度普遍落在 0.45~0.52 这个窄带里，
# 所以这不是"质量闸门"，只是防止把近乎无关的命中当证据注入提示词。
DEFAULT_MIN_SIMILARITY = 0.40

logger = logging.getLogger(__name__)


def experience_document(experience: Experience) -> str:
    """要被向量化的文本：**只有任务本身**。

    用 BGE-M3 在本机实测过三种拼法（三条历史经验互相竞争，查询是改写过的提问）：

      查询"这个 endpoint 为什么找不到？"
        只嵌任务            0.515  / 0.505  / 0.468   正确项第一
        任务+结果标签        0.514  / 0.517  / 0.468   被"失败（test_failed）"反超
        任务+相同文件路径     0.468  / 0.466  / 0.460   几乎并列
      查询"FastAPI endpoint 找不到"
        只嵌任务            0.734  / 0.451  / 0.404
        任务+结果标签        0.668  / 0.457  / 0.394

    两个结论：① 文件路径、步骤这类结构性字段在所有经验里高度重复，会把任务语义稀释掉；
    ② 结果标签会给"问题形状"的提问染上失败语义，把提问拉向失败经验——而它本来也不该
    影响"哪条任务相似"，只该影响拿到之后怎么用。所以两者都只进 metadata。
    """
    return experience.task


_HEADERS = {
    "planning": "历史经验（来自真实任务轨迹，可用 trajectory_id 追溯；不是当前仓库的事实）：",
    "debug": "同类任务的历史经验（来自真实轨迹，可用 trajectory_id 追溯；只作修复方向参考）：",
}


def format_experience_context(hits: list[dict[str, Any]], mode: str = "planning") -> str:
    """把召回结果渲染成上下文；空列表返回空串（对调用方完全无操作）。"""
    if not hits:
        return ""
    lines = [_HEADERS.get(mode, _HEADERS["planning"])]
    for i, hit in enumerate(hits, start=1):
        paths = ", ".join(hit.get("changed_paths") or [])
        if hit.get("outcome") == ACCEPTED:
            if mode == "debug":
                verdict = f"同类问题后来被修好过（改动：{paths}）" if paths else "同类问题后来被修好过"
            else:
                verdict = "这类做法跑通了测试，可以作为思路参考"
        else:
            reason = hit.get("failure_type") or "unknown"
            verdict = (
                f"同类问题当时最终没修好（{reason}），避免重复这条路"
                if mode == "debug"
                else f"这类做法失败过（{reason}），应主动避开"
            )
        detail = "; ".join(filter(None, [hit.get("test_summary"), hit.get("review_summary")]))
        lines.append(
            f"{i}. [{hit.get('outcome')}] {hit.get('task')}\n"
            f"   - {verdict}\n"
            f"   - 证据：trajectory_id={hit.get('trajectory_id')}"
            + (f"；涉及 {paths}" if paths else "")
            + (
                f"\n   - 兼容性 {hit.get('compatibility')}：{'；'.join(hit.get('compatibility_notes') or [])}"
                if hit.get("compatibility_notes")
                else ""
            )
            + (f"\n   - 结果摘要：{detail}" if detail else "")
        )
    return "\n".join(lines)


def _hit(experience: Experience, distance: float | None = None) -> dict[str, Any]:
    return {
        "trajectory_id": experience.trajectory_id,
        "task": experience.task,
        "outcome": experience.outcome,
        "failure_type": experience.failure_type,
        "changed_paths": experience.changed_paths,
        # 带上记录时的版本：冲突分流要据此判断"这条经验引用的文件是否已经变了"
        "repo_commit": (experience.extra or {}).get("repo_commit") or "",
        "test_summary": experience.test_summary,
        "review_summary": experience.review_summary,
        "distance": distance,
    }


class ExperienceIndex:
    """Chroma 向量索引：内容来自经验库，可整体重建。"""

    def __init__(
        self,
        embedding_function: Any | None = None,
        persist_directory: Path | str = DEFAULT_CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        if embedding_function is None:
            # 与知识库共用同一个本地 BGE-M3 实例（进程内单例）
            from agents.tools import get_embeddings

            embedding_function = get_embeddings()
        from langchain_chroma import Chroma

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self._chroma = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_function,
            persist_directory=str(self.persist_directory),
        )

    def sync(self, store: ExperienceStore) -> int:
        """按经验库重建索引（练习规模下整体重建比增量去重更不容易出错）。"""
        experiences = store.all()
        self._chroma.reset_collection()
        if experiences:
            self._chroma.add_texts(
                texts=[experience_document(e) for e in experiences],
                metadatas=[
                    {
                        "experience_id": e.id,
                        "trajectory_id": e.trajectory_id,
                        "outcome": e.outcome,
                        "failure_type": e.failure_type,
                        "task": e.task,
                        "changed_paths": ",".join(e.changed_paths),
                        "test_summary": e.test_summary,
                        "review_summary": e.review_summary,
                    }
                    for e in experiences
                ],
                ids=[e.id for e in experiences],
            )
        return len(experiences)

    def search(self, task: str, k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
        pairs = self._chroma.similarity_search_with_score(task, k=k)
        hits: list[dict[str, Any]] = []
        for document, distance in pairs:
            meta = document.metadata or {}
            # 项目里的 embeddings 是归一化的，L2 距离可换算成余弦相似度
            similarity = max(-1.0, min(1.0, 1.0 - (float(distance) ** 2) / 2))
            hits.append(
                {
                    "trajectory_id": str(meta.get("trajectory_id") or ""),
                    "task": str(meta.get("task") or ""),
                    "outcome": str(meta.get("outcome") or ""),
                    "failure_type": str(meta.get("failure_type") or ""),
                    "changed_paths": [p for p in str(meta.get("changed_paths") or "").split(",") if p],
                    "test_summary": str(meta.get("test_summary") or ""),
                    "review_summary": str(meta.get("review_summary") or ""),
                    "distance": float(distance),
                    "similarity": round(similarity, 4),
                }
            )
        return hits


def chroma_path(config: dict[str, Any]) -> Path:
    configured = (config.get("configurable") or {}).get("experience_chroma_path")
    return Path(str(configured)).expanduser() if configured else DEFAULT_CHROMA_DIR


def top_k(config: dict[str, Any]) -> int:
    raw = (config.get("configurable") or {}).get("experience_top_k", DEFAULT_TOP_K)
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_TOP_K


def min_similarity(config: dict[str, Any]) -> float:
    raw = (config.get("configurable") or {}).get("experience_min_similarity", DEFAULT_MIN_SIMILARITY)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return DEFAULT_MIN_SIMILARITY


def recall_experiences(task: str, config: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    """返回 (命中列表, 检索方式)。库为空 / 无命中时是 ([], "none")。"""
    path = experience_path(config)
    k = top_k(config)
    if k == 0 or not Path(path).exists():
        return [], "none"

    # 第二层检索的判据：当前任务的签名 + 当前代码版本（doc 02 §8/§11）
    context = {**task_signature(task), "repo_commit": repo_commit()}
    with ExperienceStore(path) as store:
        if not store.stats()["total"]:
            return [], "none"
        try:
            index = ExperienceIndex(persist_directory=chroma_path(config))
            floor = min_similarity(config)
            hits = [h for h in index.search(task, k=k) if h["similarity"] >= floor]
            if not hits:
                # 索引可能是空的或落后于经验库，重建一次再查
                index.sync(store)
                hits = [h for h in index.search(task, k=k) if h["similarity"] >= floor]
            # 向量检索成功就用它的结果（哪怕为空）：判"没有相关经验"要靠相关性下限，
            # 而不是靠改回关键词匹配硬凑出几条弱命中。
            kept = _apply_compatibility(hits, store, context)
            if kept:
                return kept, "vector"
            # 语义阶段本来就没有候选 → none；有候选但被判不兼容 → abstain。
            # 两种"不注入"的语义不同，混在一起会让上游分不清是"没找到"还是"不敢用"。
            return [], ("none" if not hits else "abstain")
        except Exception:  # 依赖缺失 / 模型加载失败都不该让规划失败
            logger.warning("experience vector retrieval unavailable, falling back to keyword recall", exc_info=True)
            kept = _apply_compatibility(
                [_hit(e) for e in store.recall(task, limit=k)], store, context
            )
            return kept, ("keyword" if kept else "abstain")


def _apply_compatibility(
    hits: list[dict[str, Any]], store: ExperienceStore, context: dict[str, str]
) -> list[dict[str, Any]]:
    """证据兼容性过滤 + 弃权（doc 02 §8/§10）。

    硬冲突（分数为 0，例如语言不同）直接丢弃；全被丢掉就返回空列表——
    **"找到一条相似经验"不等于"应该使用它"**。调用方看到空列表即退回原有行为。
    """
    kept: list[dict[str, Any]] = []
    for hit in hits:
        experience = store.get(str(hit.get("trajectory_id") or ""))
        if experience is None:
            kept.append(hit)
            continue
        score, notes = compatibility(experience, context)
        # 补齐冲突分流需要的静态信息（向量命中的 metadata 里可能没有这两项）
        enriched = {
            **hit,
            "compatibility": score,
            "compatibility_notes": notes,
            "repo_commit": (experience.extra or {}).get("repo_commit") or hit.get("repo_commit", ""),
            "changed_paths": experience.changed_paths or hit.get("changed_paths") or [],
        }
        if score > 0:
            kept.append(enriched)
    return kept


__all__ = [
    "DEFAULT_CHROMA_DIR",
    "ExperienceIndex",
    "chroma_path",
    "experience_document",
    "format_experience_context",
    "min_similarity",
    "recall_experiences",
    "top_k",
]
