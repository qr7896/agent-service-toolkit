"""SWE-bench 风格的评测任务（doc 03 §11）。

为什么换格式：自造任务"培训机构 demo 感"太强。真实软件工程任务的共同特征是
**每个任务都有明确的 base commit、可执行测试、独立判分方式**，所以这里把任务定义成
SWE-bench 的结构（instance_id / problem_statement / FAIL_TO_PASS / PASS_TO_PASS），
以后接真实 issue 时只是换数据，判分逻辑不用改。

判分原则：
  - `FAIL_TO_PASS` 全部通过 **且** `PASS_TO_PASS` 一个都不能退步，才算 resolved；
  - 每个 node 单独跑，给出逐条结果，而不是只看一个总 exit code；
  - 判分不读模型的自我报告。
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TaskSpec:
    instance_id: str
    problem_statement: str
    setup_files: dict[str, str] = field(default_factory=dict)
    test_files: dict[str, str] = field(default_factory=dict)
    gold_files: dict[str, str] = field(default_factory=dict)
    FAIL_TO_PASS: list[str] = field(default_factory=list)
    PASS_TO_PASS: list[str] = field(default_factory=list)
    repo: str = ""
    base_commit: str = ""


def _spec_from_dict(data: dict) -> TaskSpec:
    # PASS_TO_PASS 允许为空列表（有些任务确实没有需要保住的用例），但字段必须存在
    required = ("instance_id", "problem_statement", "FAIL_TO_PASS")
    missing = [key for key in required if not data.get(key)]
    if "PASS_TO_PASS" not in data:
        missing.append("PASS_TO_PASS")
    if missing:
        raise ValueError(f"任务缺少必填字段 {missing}：{data.get('instance_id') or data}")
    return TaskSpec(
        instance_id=str(data["instance_id"]),
        problem_statement=str(data["problem_statement"]),
        setup_files={str(k): str(v) for k, v in (data.get("setup_files") or {}).items()},
        test_files={str(k): str(v) for k, v in (data.get("test_files") or {}).items()},
        gold_files={str(k): str(v) for k, v in (data.get("gold_files") or {}).items()},
        FAIL_TO_PASS=list(data["FAIL_TO_PASS"]),
        PASS_TO_PASS=list(data.get("PASS_TO_PASS") or []),
        repo=str(data.get("repo") or ""),
        base_commit=str(data.get("base_commit") or ""),
    )


def load_tasks(path: Path) -> list[TaskSpec]:
    """读 JSONL 任务集，一行一个任务。"""
    specs: list[TaskSpec] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            specs.append(_spec_from_dict(json.loads(line)))
    return specs


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def prepare(spec: TaskSpec, root: Path, with_gold: bool = False) -> Path:
    """把任务铺到工作区：先写 base 状态的文件与测试；with_gold 时再打上标准答案。"""
    root = Path(root)
    _write(root, spec.setup_files)
    _write(root, spec.test_files)
    if with_gold:
        _write(root, spec.gold_files)
    return root


def _run_node(root: Path, node: str) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", node],
        cwd=str(root), capture_output=True, timeout=300,
        encoding="utf-8", errors="replace",
    )
    return proc.returncode == 0


def grade(spec: TaskSpec, root: Path) -> dict:
    """独立判分：逐条跑 FAIL_TO_PASS 与 PASS_TO_PASS。"""
    fail_to_pass = {node: _run_node(root, node) for node in spec.FAIL_TO_PASS}
    pass_to_pass = {node: _run_node(root, node) for node in spec.PASS_TO_PASS}
    resolved = all(fail_to_pass.values()) and all(pass_to_pass.values())
    return {
        "instance_id": spec.instance_id,
        "resolved": resolved,
        "fail_to_pass": fail_to_pass,
        "pass_to_pass": pass_to_pass,
        "detail": (
            f"F2P {sum(fail_to_pass.values())}/{len(fail_to_pass)}，"
            f"P2P {sum(pass_to_pass.values())}/{len(pass_to_pass)}"
        ),
    }


__all__ = ["TaskSpec", "grade", "load_tasks", "prepare"]
