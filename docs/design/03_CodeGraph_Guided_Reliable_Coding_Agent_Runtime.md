# CodeGraph-Guided Reliable Coding Agent Runtime

> **项目收敛版架构文档**
>
> 核心问题：**如何让 Coding Agent 更准确、更少读取无关代码、更少越权、更容易验证？**

---

# 1. 为什么现在必须“砍”项目

当前项目已经做了大量能力：

```text
RAG
BGE-M3
Code Tools
search_code
Edit
Git Diff
Planning
Test
Debug
Reviewer
HITL
Trajectory
Experience
Memory Retrieval
Self-Correction
Benchmark
Sandbox
Docker
Model Routing
Agent Builder / Workflow
```

如果继续沿着“看到一个 Agent 能力就加一个”的方式扩展，最终会变成：

> 功能很多，但没有一个中心问题。

因此项目从现在开始不以“功能数量”为目标，而以一个统一问题为目标：

# 如何让 Coding Agent 更准确、更少读取无关代码、更少越权、更容易验证？

---

# 2. 项目新定位

## CodeGraph-Guided Reliable Coding Agent Runtime

中文：

> **CodeGraph 驱动的可靠 Coding Agent 执行运行时**

不是：

> “我自己造了一个 Codex。”

不是：

> “我复刻了 Claude Code。”

而是：

> **利用成熟的代码智能能力，把 Coding Agent 放入一个可控、可隔离、可验证、可审计、可评测的执行环境。**

---

# 3. 系统职责分层

```text
                 User Issue
                     ↓
             Code Understanding
                 CodeGraph
                     ↓
                  Planner
                     ↓
            Permission Policy
                     ↓
               Sandbox Runtime
                     ↓
                   Coder
                     ↓
              Test / Verification
                     ↓
                  Reviewer
                     ↓
                 Trajectory
                     ↓
                Evaluation
                     ↓
                Experience
```

每层只回答一个问题：

| 模块 | 核心问题 |
|---|---|
| CodeGraph | 我应该理解哪些代码？ |
| Planner | 我准备怎么解决？ |
| Permission | 我允许做什么？ |
| Sandbox | 在哪里做？ |
| Coder | 实际怎么修改？ |
| Test | 事实是否成立？ |
| Reviewer | 是否满足任务要求？ |
| Trajectory | 到底发生了什么？ |
| Experience | 过去有什么可复用经验？ |
| Evaluation | 这个系统是否真的变好了？ |

---

# 4. CodeGraph：负责“认识代码”，不要自己造

CodeGraph 当前提供结构化代码理解、符号搜索、AI context、调用关系、依赖关系、影响分析、相关测试等能力。

因此采用：

```text
CodeGraph
   ↓
MCP / Tool Interface
   ↓
Your Agent Runtime
```

而不是重新实现：

```text
tree-sitter
AST
symbol graph
call graph
```

原因非常简单：

> CodeGraph 是基础能力，不是本项目真正要研究的对象。

真正的研究对象是：

> **Agent 如何决定什么时候调用哪种代码证据，以及这些证据如何改变后续执行。**

CodeGraph 官方当前也已经明确支持 `get_ai_context`、`get_edit_context`、`analyze_impact`、`find_related_tests` 等针对 Coding Agent 的结构化能力。

---

# 5. 当前已有能力：哪些保留

## 必须保留

### A. Code Retrieval

- `search_code`
- `read_file`
- `list_files`

意义：提供 baseline，同时作为 CodeGraph 的 fallback / 对照。

### B. Editing

- `write_file`
- `edit_file`
- `git_diff`

### C. Planning

当前 Planner 已经做到：

```text
read-only recon
→ JSON plan
→ deterministic validation
→ State
```

并且会使用 `open_questions` 暴露不确定性。

### D. Verification

- `run_tests`
- structured result
- timeout
- deterministic status

### E. Self-Correction

```text
FAIL
→ Debug
→ Edit
→ Test
→ retry
```

并有 `MAX_RETRIES`。

### F. Reviewer

只读 Reviewer + 证据化 verdict。

### G. HITL

写操作在副作用前暂停。

### H. Sandbox

当前 workspace sandbox 已做到：

```text
copy repository
→ isolated execution
→ cleanup
→ main workspace zero write
```

### I. Trajectory / Experience

继续保留，作为 Evaluation 和后续研究的数据基础。

---

# 6. 哪些现在冻结，不再继续横向扩张

## 暂停：Skill Hot Plug

不是取消。

只是暂缓。

原因：当前核心问题不是 Skill，而是 repository understanding + execution reliability。

之后再研究：

```text
Skill Discovery
→ Deferred Loading
→ Permission
```

---

## 暂停：复杂 Multi-Agent

当前没有必要为了“看起来高级”加入更多 Agent。

保留：

```text
Planner
Coder
Tester
Reviewer
```

只有实验表明角色分离带来收益，才扩大。

---

## 暂停：大规模 Agent Builder / Platform

当前 Agent Builder / workflow 是平台化探索，不是核心科研问题。

保留代码，不继续横向扩张。

---

## 暂停：复杂 Cost-Aware Routing

当前成本记录已经足够作为基础设施。

复杂的 Local → Cheap → Strong Router 暂时冻结。

原因：如果 Evaluation 本身还没有形成稳定 benchmark，先做复杂 routing 很容易得到“漂亮但没有意义”的数据。

---

# 7. 当前项目真正的新主线

```text
真实 Coding Task
       ↓
CodeGraph / search_code
       ↓
Evidence-aware Planning
       ↓
Permission Gate
       ↓
Sandbox
       ↓
Minimal Edit
       ↓
Test
       ↓
Reviewer
       ↓
Trajectory
       ↓
Evaluation
       ↓
Experience
```

---

# 8. 四个核心子问题

## Q1：Agent 能不能更准确地理解代码？

比较：

```text
filesystem search
vs
search_code
vs
CodeGraph
```

---

## Q2：Agent 能不能少做无效探索？

指标：

- Tool Calls
- Files Read
- Context Tokens
- Time
- Duplicate Search Rate

---

## Q3：Agent 能不能更少越权 / 误改？

指标：

- Wrong-file modification
- Sensitive-file access
- Out-of-workspace access
- Permission violation
- Human intervention

---

## Q4：Agent 能不能更容易被验证？

指标：

- Test Pass Rate
- Reviewer approval
- Independent evaluator success
- Evidence coverage
- Unverified claim rate

---

# 9. CodeGraph 接入后的第一个实验

不要一下改完整 Agent。

先固定任务：

```text
真实 GitHub coding issues
```

比较：

### Baseline A

```text
list_files
read_file
```

### Baseline B

```text
search_code
read_file
```

### Improved C

```text
CodeGraph
```

### Improved D

```text
CodeGraph
+
impact analysis
+
related tests
```

---

# 10. Evaluation Matrix

| 指标 | A | B | C | D |
|---|---:|---:|---:|---:|
| Task Success | | | | |
| First-pass Success | | | | |
| Tool Calls | | | | |
| Files Read | | | | |
| Context Tokens | | | | |
| Time | | | | |
| Wrong-file Modification | | | | |
| Test Pass Rate | | | | |
| Reviewer Rejection | | | | |
| Human Intervention | | | | |

不要只看成功率。

因为很多 Retrieval 方法可能：

```text
成功率一样
但
Context Tokens ↓
Files Read ↓
Tool Calls ↓
```

这仍然是重要收益。

---

# 11. 真实任务数据从哪里来

核心数据源改成：

```text
真实 GitHub Issues
+
真实 Repository Snapshot
+
真实 Tests
+
Ground-truth Patch / Evaluator
```

可以从 SWE-bench / SWE-bench Verified 等公开软件工程任务中构建第一版 benchmark，也可以逐步加入自选开源仓库的问题。

重点不是“任务数量越多越好”，而是：

```text
每个任务
都有
明确的 base commit
可执行测试
独立判分方式
```

SWE-bench 的任务本身就是围绕真实 GitHub 软件工程 issue 组织的，适合解决当前项目“培训机构 demo 感太强”的问题。

---

# 12. 为什么不直接复用 Codex / Claude Code

回答框架：

```text
我没有试图重造 Coding Model。

我复用已有模型和基础工具能力，
研究的是它们进入受控软件研发环境后，
如何进行：

Code Understanding
Permission
Sandbox
Verification
Trajectory
Evaluation
```

因此：

```text
Model / SDK
→ capability provider

Runtime
→ execution control plane
```

---

# 13. 为什么不自己重造 CodeGraph

同样回答：

```text
CodeGraph 的价值
= code intelligence infrastructure

我的研究对象
= agent execution policy
```

因此：

> **基础设施成熟就复用；实验对象才自己做。**

这应该成为项目长期的技术选型原则。

---

# 14. 目前真正可以形成“原创系统思想”的地方

不是：

```text
我发明了 search_code
我发明了 HITL
我发明了 Sandbox
```

而是：

> **把 Coding Agent 看成一个需要“证据、权限、执行环境和验证反馈”的受控执行系统。**

当前项目里已经逐步形成：

```text
LLM
  → 负责提出方案

CodeGraph / Retrieval
  → 负责提供代码事实

Tools
  → 负责执行

Permission
  → 负责限制副作用

Sandbox
  → 负责限制损害范围

Test / Reviewer
  → 负责验证

Trajectory
  → 负责记录

Evaluation
  → 负责判断是否真的改善
```

---

# 15. 下一阶段只允许做三类事情

## 类型 1：提高 Code Understanding

```text
CodeGraph
Evidence-Gated Planner
```

## 类型 2：提高 Execution Reliability

```text
Permission Policy
Sandbox
Verification
```

## 类型 3：提高 Evaluation / Learning

```text
Trajectory
Experience
Benchmark
```

任何不能归到这三类的新功能，都暂缓。

---

# 16. 项目最终叙事

### 一句话

> **我不是在复刻 Codex，而是在研究如何把 Coding Agent 变成一个可理解代码、受权限控制、在隔离环境执行、由确定性测试验证、并能通过真实轨迹持续评测和改进的可靠执行系统。**

### 更技术化

> **The project studies a CodeGraph-guided execution runtime for repository-level coding agents, focusing on context acquisition, permission boundaries, sandboxed execution, deterministic verification, trajectory-based evaluation, and evidence-grounded experience reuse.**

---

# 17. 当前项目状态判断

| 部分 | 状态 |
|---|---|
| Agent Loop | 已有 |
| Code Retrieval | 已有 |
| Code Editing | 已有 |
| Planning | 已有 |
| Test | 已有 |
| Self-Correction | 已有 |
| Reviewer | 已有 |
| HITL | 已有 |
| Trajectory | 已有 |
| Experience | 已有 |
| Experience Retrieval | 已有 |
| Workspace Sandbox | 已有 |
| Docker | 静态验证，构建未验证 |
| Benchmark | 已跑通，但 n=3 |
| CodeGraph | 下一阶段接入 |
| Evidence-Gated Planner | 下一阶段研究 |
| Skill Deferred Loading | 暂缓 |
| 大规模 Multi-Agent | 暂缓 |
| 复杂 Model Routing | 暂缓 |

---

# 18. 最终路线：不是越来越大，而是越来越深

```text
现有项目
   ↓
CodeGraph
   ↓
Controlled Retrieval Experiment
   ↓
Evidence-Gated Planner
   ↓
Permission / Sandbox hardening
   ↓
Real GitHub task benchmark
   ↓
Trajectory / Experience deepening
   ↓
Regression benchmark
```

最终不再追求：

> “我做了多少 Agent 功能。”

而追求：

> **“我能否用实验解释：为什么这个 Agent 在这个任务上应该看这些代码、做这些动作、拥有这些权限、在这个环境里执行，并且最终如何证明自己真的做对了。”**
