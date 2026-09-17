# Agent Project：模块设计卡（Design Cards）

> 本文把整个项目拆成一张张“模块设计卡”。以后学习任何模块，不再只记“它是什么”，而必须回答：**问题、基线、机制、替代方案、Trade-off、失败、证据、未证明什么。**

---

# 设计卡模板

每个模块统一使用 8 个问题：

```text
1. Problem
   它解决哪个具体失败？

2. Baseline
   没有它的时候怎么做？

3. Mechanism
   它到底做了什么？

4. Alternative
   还有什么实现？

5. Trade-off
   为什么选这个？

6. Failure
   它什么时候会失败？

7. Evidence
   用什么数据证明有效？

8. Not Proven
   当前实验还没有证明什么？
```

---

# Card 01 — CodeGraph / Code Intelligence

## Problem

纯 `list_files + read_file` 容易让 Coding Agent：

- 盲读很多文件
- 只看局部文本
- 不理解 caller / callee / dependency / impact
- 难以快速找到 related tests

## Baseline

```text
list_files
→ read_file
```

当前项目进一步实现了 `search_code`，已经把“遍历”变成了“定位”。

## Mechanism

后续引入 CodeGraph：

```text
symbol_search
get_ai_context
get_callers
get_callees
analyze_impact
find_related_tests
```

## Alternative

- grep / ripgrep
- `search_code`
- embeddings / semantic code search
- RepoMap

## Trade-off

CodeGraph：

```text
+ structural context
+ graph relations
+ impact analysis
+ test relations
```

但代价是：

```text
indexing
staleness
extra infrastructure
```

## Failure

- graph stale
- dynamic dispatch
- generated code
- unsupported language constructs
- repository state changed after indexing

## Evidence

第一阶段 A/B：

```text
list_files + read_file
vs
search_code
```

已有真实实验：

```text
12 → 7 tool calls
9 → 4 files
17.1 → 14.2s
```

下一阶段：

```text
search_code
vs
CodeGraph
```

## Not Proven

当前还没有证明 CodeGraph 一定比 `search_code` 提高任务成功率。

---

# Card 02 — Search Code

## Problem

模型如果只能 `list_files + read_file`，会先遍历再判断。

## Baseline

```text
list_files
read_file
```

## Mechanism

`search_code`：

- keyword
- function/class name
- file name
- regex
- path scope
- line context
- output budget

## Alternative

直接把整个仓库交给模型。

## Trade-off

```text
search_code
+ cheap
+ deterministic
+ precise location
- only textual / lexical structure
```

## Evidence

现有 A/B 已验证工具调用和文件读取下降。

## Not Proven

没有证明它对所有 repository task 都优于语义搜索或 CodeGraph。

---

# Card 03 — Planner

## Problem

Agent 如果直接：

```text
task
→ tool
→ edit
```

容易：

- 边看边改
- 目标不清晰
- 修改顺序混乱
- 没有 verification plan

## Baseline

直接 Agent Loop。

## Mechanism

当前 Planner：

```text
read-only recon
→ JSON plan
→ deterministic validation
→ State
```

包含：

```text
order
action
path
reason
verification
open_questions
```

## Trade-off

优点：结构化、可验证。

成本：额外 LLM call / latency。

## Failure

- model 输出非法 JSON
- plan 与 repository 不一致
- plan 过度细化
- plan 本身错误

当前项目已经遇到 DeepSeek structured output 不可用的问题，于是改用 JSON prompt + bracket extraction + Pydantic validation。

## 下一步

接入：

```text
CodeGraph
+
Evidence State
+
Evidence Gate
```

---

# Card 04 — Evidence-Gated Planner

## Problem

“计划写出来”不代表“证据足够”。

## Mechanism

维护：

```text
Target Evidence
Impact Evidence
Verification Evidence
```

每个 Plan Step 都有 Evidence Card。

## 核心决策

```text
Evidence sufficient?
   ↓
YES → Coder
NO  → Retrieve More / Abstain
```

## Evidence

暂时是研究假设。

实验目标：

```text
减少无效读取
不降低成功率
减少错误文件修改
提高 verification coverage
```

---

# Card 05 — Edit Tools

## Problem

让 LLM 全量重写整个文件会产生大范围、难审核的副作用。

## Mechanism

当前：

```text
0 match
→ no write

>1 match
→ no write

1 match
→ write
```

敏感文件拒绝：

```text
.env*
*.pem
*.key
*.p12
id_rsa*
.git/**
```

## Alternative

- whole-file rewrite
- patch-based editing
- AST editing

## Trade-off

当前方案简单、确定、容易测试，但不是通用语义编辑器。

## Evidence

已有 11/11 工具验收。

---

# Card 06 — Permission Policy

## Problem

Agent 能调用工具，不意味着 Agent 应该在任何情况下都能调用工具。

## 当前机制

已经有：

```text
workspace boundary
path validation
tool allowlist
allow_write
sensitive path blacklist
HITL
pytest-only execution
```

## 深化方向

统一为：

```yaml
filesystem:
  read: ...
  write: ...

execution:
  pytest: allow
  shell: approval

network:
  enabled: false

git:
  diff: allow
  push: approval
```

## Evidence

重点评测：

- violation rate
- false rejection
- human approval
- bypass attempts

---

# Card 07 — Sandbox

## Problem

Path boundary 只能限制“去哪儿”。

它无法保证：

> Agent 在合法目录里也不会把代码改坏。

## Current Mechanism

```text
copy workspace
→ run in isolated copy
→ reclaim
```

已验证：

```text
main workspace = zero write
```

## Alternative

- git worktree
- Docker
- VM
- OS sandbox

## Trade-off

当前复制副本：

```text
+ 改动小
+ 复用原 PROJECT_ROOT 推导
+ 容易回收
- copy cost
- isolation strength < VM/container
```

## Not Proven

Docker 层目前只有静态验证，实际 build 尚未验证。

---

# Card 08 — Test / Verification

## Problem

LLM 可以说：

> “应该没问题。”

但这不是事实。

## Mechanism

当前 `run_tests`：

```text
pytest only
shell=False
timeout
structured status
exit_code
summary
traceback
output limit
```

## Core Principle

> LLM 提方案；确定性系统验事实。

## Evidence

已有故意失败、timeout、no_tests 等真实工具测试。

---

# Card 09 — Self-Correction

## Problem

第一次修改失败以后，Agent 不应该直接结束。

## Mechanism

```text
FAIL
 ↓
Debugger
 ↓
Coder
 ↓
Test
 ↓
PASS / retry / giveup
```

当前 `MAX_RETRIES = 3`。

## Important Design

失败依据：

```text
pytest status
```

不是：

```text
模型说自己修好了
```

---

# Card 10 — Reviewer

## Problem

“测试通过”不完全等于“完成了需求”。

## Mechanism

Reviewer：

- read-only
- diff
- search
- read
- tests
- structured verdict
- evidence references

## 一个真实设计迭代

第一次 reviewer 把正确任务拒绝了，因为它看见了任务之外的未提交代码。

由此增加：

```text
review_path
plan target
```

这是一个值得保留的 Failure → Diagnosis → Design Change 案例。

---

# Card 11 — HITL

## Problem

高风险副作用不能全部自动发生。

## Mechanism

```text
detect write
↓
interrupt
↓
approval
↓
execute
```

当前实现特别关注：

> approval 必须发生在副作用之前。

## Alternative

- 全自动
- 所有操作都审批
- 权限等级

## 当前取舍

只对真正有副作用的动作审批，不给 search/read/diff 造成审批噪音。

---

# Card 12 — Trajectory

## Problem

没有 trajectory，就没有可靠 evaluation，也没有可靠 experience。

## Mechanism

记录：

```text
task
plan
tool calls
changed paths
test results
review
approval
model
time
final outcome
```

并统一从 graph 收口。

## Important Principle

> Trajectory 是 Evaluation 与 Experience 的共同原始证据。

---

# Card 13 — Experience Memory

## Problem

仅有聊天历史不能可靠复用 coding experience。

## Mechanism

当前：

```text
Trajectory
→ Experience
```

并记录：

```text
accepted
rejected
test_failed
review_rejected
approval_denied
```

## 深化

升级成：

```text
Experience
+
Evidence
+
Applicable Conditions
+
CodeGraph Anchors
+
Verification
+
Freshness
```

---

# Card 14 — Experience Retrieval

## Problem

“相似”不等于“可复用”。

## 当前发现

Embedding 文本设计经过消融后发现：

```text
任务 + 结果 + 文件 + 步骤
```

可能因为大量重复字段稀释语义。

当前改成：

```text
任务文本 → embedding
其他字段 → metadata
```

## 深化

```text
semantic similarity
+
structural compatibility
+
repository compatibility
+
verification evidence
→
use / abstain
```

---

# Card 15 — Benchmark

## Problem

“看起来很好”不是证据。

## 当前 Benchmark

同一批任务：

```text
cold
vs
experience-enabled
```

n=3。

## 当前结论

不能证明 Experience 有效。

可以证明：

- 链路跑通
- 经验真实命中
- 工具调用 / 时间有方向性变化

## 下一步

```text
30–50 real tasks
+ repeated runs
+ held-out tasks
+ task-level failure analysis
```

---

# Card 16 — Evaluation Data

## Problem

没有真实任务，所有 Agent 实验都容易变成 demo。

## 推荐数据

```text
真实 GitHub Issue
+
Frozen Base Commit
+
Real Repository
+
Executable Tests
+
Independent Evaluator
```

## 目标

让：

```text
Data
→ Agent
→ Trajectory
→ Evaluation
→ Failure Taxonomy
→ New Design
```

形成数据飞轮。

---

# Card 17 — Model Routing

## Problem

不同任务不应该自动用同一成本模型。

## 当前

已经有基础成本统计：

```text
llm_calls
estimated_tokens
model_used
```

## 当前状态

复杂三层路由暂时冻结。

## 原因

先有稳定 Benchmark，再研究：

```text
quality
vs
cost
```

而不是先设计一个复杂 router，再找数据证明它存在价值。

---

# Card 18 — Skill / Deferred Loading

## 当前状态

暂未真正实现。

## 为什么先不做

当前核心问题：

```text
code understanding
execution reliability
verification
```

不是 Skill。

## 后续

只有当 Skill 数量真正成为 context bloat 问题时，再研究：

```text
metadata
→ discovery
→ deferred loading
→ permission
→ execution
```

并做：

```text
all loaded
vs
metadata only
vs
deferred loading
```

实验。

---

# Card 19 — Runtime

## Problem

Agent 不只是“模型 + tools”。

## Runtime 要负责

```text
state
permissions
sandbox
execution
retry
approval
verification
trajectory
```

## 原则

### SDK

```text
提供能力
```

### Runtime

```text
管理执行
```

因此本项目不需要自己重写 LLM SDK 或 MCP，而应该设计自己的 execution control plane。

---

# Card 20 — 项目最终核心问题

所有模块最终都必须能回到这一句话：

# 如何让 Coding Agent 更准确、更少读取无关代码、更少越权、更容易验证？

然后映射：

```text
准确
→ CodeGraph
→ Evidence-Gated Planner

少读取
→ search_code
→ CodeGraph
→ retrieval benchmark

少越权
→ Permission
→ Sandbox
→ HITL

容易验证
→ Test
→ Reviewer
→ Trajectory
→ Evaluation
```

如果一个新功能无法回答：

> “它具体改善了哪一个维度？”

默认不加入核心项目。

---

# 最终使用方式

以后每学一个新技术，不许只写：

```text
“今天学习了 XXX。”
```

必须新增一张 Design Card，并填写：

```text
Problem
Baseline
Mechanism
Alternative
Trade-off
Failure
Evidence
Not Proven
```

当一张卡的这 8 个问题都能独立回答时，才算从：

```text
L1 看懂
```

进入：

```text
L3 独立实现
→
L4 设计解释
```

这也是当前项目从“堆 Agent 功能”变成“真正理解 Agent Runtime”的训练机制。
