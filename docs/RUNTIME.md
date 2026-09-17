# CodeGraph-Guided Reliable Coding Agent Runtime

> 这份文档是项目定位的唯一权威说明。功能清单会变，这一页的问题与边界不轻易变。
> 设计原件见 `docs/design/`（01 EGCP 算法、02 经验深化、03 项目收敛、04 模块设计卡，其中 04 为学习资料）。

## 一句话

> 我不是在复刻 Codex，而是在研究如何把 Coding Agent 变成一个**能理解代码、受权限控制、在隔离环境执行、由确定性测试验证、并能通过真实轨迹持续评测和改进**的可靠执行系统。

## 中心问题

**如何让 Coding Agent 更准确、更少读取无关代码、更少越权、更容易验证？**

四个维度各自对应一条主线，任何新功能必须能回答"它改善的是哪一个"：

| 维度 | 主线 | 对应模块 |
|---|---|---|
| 更准确 | CodeGraph + Evidence-Gated Planner | `code_intel.py` / `evidence.py` / `coding_planner.py` |
| 少读取 | 检索与停止策略 | `search_code` / `code_intel` / 检索基准 |
| 少越权 | 权限、隔离、人工闸门 | `code_tools._resolve_inside` / `workspace.py` / HITL |
| 易验证 | 测试、评审、轨迹、评测 | `test_tools.py` / `reviewer.py` / `trajectory.py` / `evals/` |

回答不了这个问题的功能，默认不进核心项目。

## 职责分层

| 模块 | 只回答一个问题 | 实现位置 |
|---|---|---|
| CodeGraph / Code Intel | 我该理解哪些代码？ | `src/agents/code_intel.py` |
| Planner（+ Evidence Gate） | 我准备怎么解决，证据够了吗？ | `src/agents/coding_planner.py` + `evidence.py` |
| Permission | 我允许做什么？ | `code_tools.py` 路径约束 + HITL |
| Sandbox | 在哪里做？ | `src/agents/workspace.py` |
| Coder | 实际怎么改？ | `src/agents/coding_agent.py` |
| Test / Reviewer | 事实是否成立？是否满足需求？ | `test_tools.py` / `reviewer.py` |
| Trajectory | 到底发生了什么？ | `src/agents/trajectory.py` |
| Experience | 过去什么可复用？ | `src/agents/experience.py` + `coding_memory.py` |
| Evaluation | 系统真的变好了吗？ | `evals/` |

## 技术选型原则

> **基础设施成熟就复用，实验对象才自己做。**

- 不重写 LLM SDK、不重写 MCP、不重写 tree-sitter / AST / 调用图引擎。
- CodeGraph 是**基础设施**，本项目的研究对象是"Agent 何时取哪种证据、证据如何改变后续执行"。
- 因此 `code_intel.py` 提供与 CodeGraph 对齐的只读动作（`symbol_search` / `get_callers` /
  `get_callees` / `analyze_impact` / `find_related_tests`），当前用标准库 `ast` 实现，
  接入真正的 CodeGraph 时替换实现即可，Planner 与 EGCP 不动。

## 已冻结（保留代码，不再横向扩张）

| 项目 | 状态 | 原因 |
|---|---|---|
| Skill 热插拔 / 延迟加载 | 暂缓 | 当前瓶颈不是 Skill，而是代码理解与执行可靠性 |
| 大规模 Multi-Agent | 暂缓 | 角色分离的收益需要先被实验证明 |
| Agent Builder / 平台化 | 冻结 | 平台是探索成果，不是研究问题 |
| 复杂 Model Routing | 冻结 | 评价基准还不稳定时做路由，只会得到漂亮但无意义的数据 |

## 新主线

```text
真实 Coding Task
   → CodeGraph / code_intel（结构化证据）
   → Evidence-aware Planning（Evidence State + Gate + 弃权）
   → Permission Gate → Sandbox
   → Minimal Edit → Test → Reviewer
   → Trajectory → Evaluation → Experience（带条件与效用的经验）
```

## 评估矩阵

同一批任务、同一模型、同一提示词、同一 base commit，只改一个变量：

| 指标 | A: list_files+read | B: search_code | C: code_intel | D: C + Evidence Gate |
|---|---:|---:|---:|---:|
| Task Success | | | | |
| First-pass Success | | | | |
| Tool Calls | | | | |
| Files Read | | | | |
| Context Tokens | | | | |
| Wrong-file Modification | | | | |
| Test Pass Rate | | | | |
| Reviewer Rejection | | | | |
| Human Intervention | | | | |

**不要只看成功率**：检索类改进常常表现为"成功率持平，但读取文件数、上下文 token、工具调用下降"，那同样是收益。

## 数据来源

```text
真实 GitHub Issue + Frozen Base Commit + 可执行测试 + 独立判分
```

以 SWE-bench / SWE-bench Verified 这类公开软件工程任务为第一版基准的来源，逐步加入自选开源仓库的问题。重点不是任务数量，而是**每个任务都有明确 base commit、可执行测试、独立判分方式**。

## 当前进度与已知边界

见 [PROGRESS.md](./PROGRESS.md)。两处必须诚实标注的边界：

- **Benchmark 只有 n=3**，只能算方向性观察，不能宣称经验记忆有效。
- **容器化只有静态校验**，本机没装 Docker，镜像构建未验证。

## 叙事边界

不宣称：

- 不是"我发明了 CodeGraph / HITL / Sandbox"。
- 不在系统文献综述与受控实验之前声称 EGCP 是"世界第一个"。

正确的说法是：

> 这是基于现有项目约束提出的候选算法假设，我计划通过受控消融实验验证它是否构成有价值、可复现的设计增量。
