# AI Coding Agent 魔改总路线（LangGraph 深入学习版）

> 基于 `JoshuaC215/agent-service-toolkit` 的现有魔改项目继续推进。\
> 本文档用于把当前项目与三个参考仓库对照，明确：**看什么、抄什么、不抄什么、移植到哪里、先做什么、每一步如何验收**。\
> 更新时间：2026-09-15

------------------------------------------------------------------------

# 0. 当前项目基线

## 0.1 原始项目

主项目：

- `JoshuaC215/agent-service-toolkit`
- 自己的 fork：`qr7896/agent-service-toolkit`

原项目本质是一个：

``` text
LangGraph
+
FastAPI
+
Streamlit
+
Agent Registry
+
Checkpointer / Store
+
RAG
+
SSE Streaming
+
HITL
```

的 Agent Service 骨架。

当前项目已经完成：

``` text
Day 1 / 请求链路
        ↓
项目分层理解
        ↓
LangGraph StateGraph / ToolNode / 条件边
        ↓
原始 RAG
        ↓
本地 BGE-M3
        ↓
Coding Agent
        ↓
list_files
        ↓
read_file
```

当前项目进度文档明确记录：下一步是
`search_code`，然后才进入写代码、Planning、测试/调试、自修复、HITL、Evaluation
等阶段。

------------------------------------------------------------------------

# 1. 本次魔改的最终目标

不要把目标定义成：

> "把一个 GitHub Coding Agent 搬进来。"

真正目标：

> **基于现有 agent-service-toolkit，自己使用 LangGraph
> 构建一个能够理解代码、检索代码、规划修改、编辑代码、运行测试、根据失败结果自修复，并能够积累历史
> Coding Experience 的 AI Coding Agent。**

最终形成：

``` text
                         User
                           │
                           ▼
                  ┌─────────────────┐
                  │ Task Analyzer   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Code Retrieval  │
                  │ search / read   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Experience      │
                  │ Memory          │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Planner         │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Coder / Editor  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Test / Execute  │
                  └────────┬────────┘
                           │
                     ┌─────┴─────┐
                     │           │
                    PASS        FAIL
                     │           │
                     ▼           ▼
                 Reviewer    Diagnose
                     │           │
                     ▼           │
              Save Experience ◄──┘
                     │
                     ▼
                    END
```

------------------------------------------------------------------------

# 2. 三个参考仓库的角色分工

本次不是三个项目平均搬。

应该明确分工：

  ------------------------------------------------------------------------
  参考仓库                                   主要学习什么                                                   在你的项目中的定位
  ------------------------------------------------------------------------
  `langchain-ai/open-swe`                    成熟 Coding Agent                                              **架构参考**
                                             架构、Planning、Sandbox、Tools、Middleware、Subagent、Review  

  `wusuiling-if/mini-code-agent-langgraph`   LangGraph Coding                                               **最适合局部移植/重写**
                                             Loop、验证、patch、trajectory、transaction、安全边界、memory  

`IoanRoume/self-improving-code-agent`      Critic → Score → Retry → Memory → 自进化                       **自进化创新参考**
-----------------------------------------------------------------------------------------------------------------------------------

最终不是：

``` text
A + B + C = 大杂烩
```

而是：

``` text
你的 agent-service-toolkit
        │
        ├── Open SWE：学习高级架构
        │
        ├── mini-code-agent：学习 Coding Runtime / Verification
        │
        └── self-improving-code-agent：学习 Experience Loop
                         ↓
                 自己重新实现
```

------------------------------------------------------------------------

# 3. 参考仓库一：Open SWE

仓库：

`langchain-ai/open-swe`

官方定位是开源异步 Coding Agent / Software Factory。

它现在的体系已经包含：

- Planning / investigation
- isolated sandbox
- code modification
- validation
- PR delivery
- reviewer
- analyzer
- chat
- scheduler
- subagents
- middleware
- repository instructions
- GitHub / Slack / Linear 等触发入口

Open SWE 当前使用 Deep Agents 作为 harness，而 LangGraph 负责 durable
runtime。

## 3.1 对你最有价值的部分

### A. Agent Assembly

重点研究：

``` text
agent/server.py
```

Open SWE 的 `get_agent()` 是一个重要的组装入口：

``` text
model
+
system prompt
+
tools
+
backend
+
middleware
```

这对你的 `coding_agent.py` 很有参考价值。

### B. Tools

重点研究：

``` text
agent/tools/
```

尤其理解：

``` text
工具不是越多越好
工具应该围绕 Coding Workflow 精选
```

你现在：

``` text
list_files
read_file
```

未来：

``` text
search_code
write_file
edit_file
run_tests
git_diff
```

应该继续保持"小而明确"。

### C. Prompt / Context Engineering

重点研究：

``` text
agent/prompt.py
agent/resources/default_prompt.md
AGENTS.md
```

Open SWE 将：

``` text
工作环境
+
任务执行流程
+
依赖管理
+
提交/PR
+
仓库规则
```

组织进 prompt。

你可以把这个思想缩小到：

``` text
coding_prompt.py
+
AGENTS.md
```

### D. Middleware

Open SWE 使用 middleware 处理：

``` text
tool error
消息队列
step limit
CI check
```

你未来可以把其中一小部分变成：

``` text
tool_error_guard
test_result_guard
step_limit_guard
```

但不要现在就做。

### E. Sandbox

Open SWE 最大的工程价值之一就是：

> Agent 可以拥有很强的执行权限，但工作必须隔离。

你的 Windows 本地项目暂时不要直接复制云 Sandbox。

先做：

``` text
安全路径限制
+
git diff
+
测试前后状态
```

之后再考虑：

``` text
Docker / WSL2 / Git Worktree
```

------------------------------------------------------------------------

# 4. Open SWE：哪些值得抄

  Open SWE 思路     是否移植               你的实现位置
  ------------------------------------------------------------------------
  Agent assembly    **强烈建议学习**       `src/agents/coding_agent.py`
  curated tools     **直接采用思想**       `src/agents/code_tools.py`
  prompt 分模块     **建议**               `src/agents/coding_prompt.py`
  AGENTS.md         **建议后期加入**       项目根目录
  middleware        **后期**               `src/agents/middleware.py`
  planning          **必须学习**           `coding_agent.py` 或单独 `coding_graph.py`
  subagent          **后期**               `src/agents/subagents/`
  sandbox           **先学习，不直接搬**   后期
  GitHub PR         **暂不做**             后期
  Slack / Linear    **不要做**             不属于当前核心目标
  Dashboard         **不要做**             已经有 Streamlit
  Open SWE 全项目   **绝对不要整体复制**   ---

------------------------------------------------------------------------

# 5. 参考仓库二：mini-code-agent-langgraph

仓库：

`wusuiling-if/mini-code-agent-langgraph`

这是目前三个仓库中：

> **最适合你拿来对照自己的 LangGraph Coding Agent 逐步重写的项目。**

它的项目结构中有：

``` text
src/mini_code_agent/
├── agent.py
├── chat.py
├── executor.py
├── verification.py
├── trajectory.py
├── transaction.py
├── transaction_adapter.py
├── receipt.py
├── memory_models.py
├── memory_store.py
├── locking.py
├── security.py
└── cli.py
```

## 5.1 最值得研究的模块

### `agent.py`

研究：

``` text
Agent Loop
State
Tool Calls
Loop
```

对照：

``` text
你的 coding_agent.py
```

### `executor.py`

研究：

``` text
工具执行
approval
sandbox
```

对照：

``` text
你的 code_tools.py
```

### `verification.py`

这是你未来特别值得学习的。

核心思想：

> 测试通过并不代表"永远有效"。

必须把：

``` text
verification result
```

绑定到：

``` text
某个精确 workspace 状态
```

你的简化版可以先做：

``` text
修改前 git status
修改后 git diff
运行测试
记录测试结果
```

### `trajectory.py`

研究：

``` text
Agent 做了什么
调用了哪些工具
进行了多少次尝试
```

这对你后面的 Evaluation 和 Self-Improving Memory 非常重要。

### `memory_store.py`

这是你的自进化模块的重要参考。

但是你不要直接复制它的完整安全 Memory 实现。

先理解：

``` text
Experience
↓
Store
↓
Retrieve
```

------------------------------------------------------------------------

# 6. mini-code-agent：哪些值得抄

  模块/思想      是否移植           目标
  ------------------------------------------------------------------------
  Agent Loop     **强烈建议重写**   深入 LangGraph
  Executor       **部分重写**       统一 Coding Tools
  Verification   **强烈建议学习**   测试可信度
  Trajectory     **强烈建议加入**   Evaluation / Memory
  Transaction    **后期加入**       安全编辑
  Worktree       **后期加入**       隔离修改
  HMAC Receipt   **暂不做**         复杂度过高
  Locking        **后期**           并发安全
  完整 Sandbox   **暂不做**         先完成核心 Agent
  完整 CLI       **不做**           你已有 Streamlit

------------------------------------------------------------------------

# 7. 参考仓库三：self-improving-code-agent

仓库：

`IoanRoume/self-improving-code-agent`

它的核心 LangGraph Loop：

``` text
Problem
  ↓
Researcher
  ↓
Coder
  ↓
Critic
  ↓
Score
  ├── 高分 → Memory → END
  │
  ├── 低分 + retry < 3 → Coder
  │
  └── retry >= 3 → Memory → END
```

这是三个项目中：

> **最值得你用来设计"自进化"部分的仓库。**

## 7.1 你应该学习的核心不是 Fine-tuning

这个项目最终还会：

``` text
Memory
↓
Training Dataset
↓
QLoRA
↓
KTO
↓
Fine-tuned Model
```

你目前不要做这个。

因为你的目标是：

``` text
LangGraph
+
AI Coding
+
Agent Self-Correction
```

不是：

``` text
训练自己的 Coding LLM
```

------------------------------------------------------------------------

# 8. 你的"轻量自进化"设计

建议命名：

> **Experience-Guided Self-Correction**

中文：

> **经验引导的自修复 Coding Agent**

不要宣称：

> Agent 自己训练自己。

而定义为：

> Agent 将历史 Coding Task
> 的成功/失败、错误原因、修复方式和验证结果形成结构化
> Experience，并在后续相似任务中检索这些经验，减少重复试错。

------------------------------------------------------------------------

# 9. Experience 数据结构

建议未来新增：

``` text
src/agents/experience.py
```

初期数据：

``` python
{
    "task": "...",
    "error": "...",
    "files": [...],
    "attempts": 2,
    "fix_summary": "...",
    "test_command": "pytest -q",
    "test_result": "passed",
    "score": 0.9,
    "label": "accepted"
}
```

注意：

第一版甚至不需要向量数据库。

可以先：

``` text
LangGraph Store
```

或者：

``` text
SQLite
```

完成。

第二阶段再考虑：

``` text
BGE-M3
+
Chroma
```

做 Experience Retrieval。

这样你的原项目 RAG 能力又被真正利用起来。

------------------------------------------------------------------------

# 10. 最终建议的项目目录

不要一次全部创建。

按阶段逐步增加。

最终可以演化成：

``` text
src/
├── agents/
│   ├── agents.py
│   │
│   ├── coding_agent.py
│   │
│   ├── coding_prompt.py
│   │
│   ├── code_tools.py
│   │
│   ├── test_tools.py
│   │
│   ├── experience.py
│   │
│   ├── reviewer.py
│   │
│   ├── middleware.py
│   │
│   └── subagents/
│       ├── planner.py
│       ├── coder.py
│       └── reviewer.py
│
├── memory/
│   ├── ...
│   └── coding_memory.py
│
├── service/
├── client/
├── core/
└── schema/
```

但是当前阶段只允许：

``` text
src/agents/code_tools.py
src/agents/coding_agent.py
src/agents/agents.py
```

继续改。

------------------------------------------------------------------------

# 11. 当前文件逐个改造路线

# 11.1 `src/agents/code_tools.py`

当前：

``` text
list_files
read_file
```

下一步：

``` text
search_code
```

之后：

``` text
write_file
edit_file
```

之后：

``` text
run_tests
```

最终：

``` text
list_files
read_file
search_code
write_file
edit_file
run_tests
git_diff
```

工具设计统一遵守：

``` text
1. 路径不能越权
2. 输出必须有限制
3. 返回路径
4. 返回行号
5. 错误不要炸掉整个 Graph
6. 工具必须可以被模型明确理解
```

------------------------------------------------------------------------

# 12. `search_code` 第一版

目标：

``` text
用户：
AgentClient 定义在哪里？

Agent：
search_code("class AgentClient")
        ↓
src/client/client.py:25
        ↓
read_file(...)
        ↓
给答案
```

而不是：

``` text
list_files
↓
read_file A
↓
read_file B
↓
read_file C
↓
...
```

第一版支持：

``` text
关键词
函数名
类名
文件名
```

输出：

``` text
src/client/client.py:25
class AgentClient:
```

同时增加：

``` text
匹配数量限制
文件数量限制
上下文行数
```

------------------------------------------------------------------------

# 13. `write_file` / `edit_file`

不要直接允许：

``` text
模型重写整个文件
```

优先设计：

``` text
edit_file(
    path,
    old_text,
    new_text
)
```

或者后期：

``` text
apply_patch(...)
```

原因：

``` text
整文件重写
↓
风险高
↓
容易覆盖用户代码
```

而：

``` text
局部 patch
↓
修改范围小
↓
diff 清晰
↓
容易验证
```

------------------------------------------------------------------------

# 14. `run_tests`

新增：

``` text
src/agents/test_tools.py
```

第一版只支持：

``` text
pytest -q
```

之后再允许：

``` text
pytest path/to/test.py
python -m pytest
ruff check
```

工具返回结构：

``` python
{
    "command": "pytest -q",
    "exit_code": 1,
    "stdout": "...",
    "stderr": "...",
    "passed": False
}
```

不要只返回：

``` text
Test failed
```

因为后面的 Debug Agent 必须看到：

``` text
错误信息
+
具体文件
+
具体行
```

------------------------------------------------------------------------

# 15. `coding_agent.py` 的演化

当前：

``` text
model
 ↓
tools
 ↓
model
 ↓
END
```

第一阶段：

``` text
model
 ↓
search/read
 ↓
model
```

第二阶段：

``` text
model
 ↓
search/read/edit
 ↓
model
```

第三阶段：

``` text
planner
 ↓
coder
 ↓
test
 ↓
END
```

第四阶段：

``` text
planner
 ↓
coder
 ↓
test
 ↓
┌──── PASS ────→ reviewer
│
└──── FAIL
       ↓
    debugger
       ↓
     coder
```

第五阶段：

``` text
experience_retrieval
          ↓
       planner
          ↓
        coder
          ↓
         test
          ↓
      critic/reviewer
          ↓
      experience_store
```

------------------------------------------------------------------------

# 16. `agents.py`

当前：

``` python
{
    ...
    "coding-agent": coding_agent
}
```

保持这个模式。

后期可以增加：

``` python
{
    "coding-agent": coding_agent,
    "coding-reviewer": coding_reviewer,
}
```

但不要一开始就拆成大量 Agent。

你的学习重点应该是：

> **什么时候一个 Graph 足够？什么时候需要 Subgraph？什么时候才值得
> Multi-Agent？**

------------------------------------------------------------------------

# 17. 推荐的 LangGraph 图设计

第一阶段：

``` text
START
 ↓
model
 ↓
tools?
 ├── YES → tools → model
 └── NO  → END
```

第二阶段：

``` text
START
 ↓
planner
 ↓
coder
 ↓
tools
 ↓
coder
```

第三阶段：

``` text
START
 ↓
planner
 ↓
coder
 ↓
test
 ↓
check_test
 ├── PASS → reviewer
 └── FAIL → debugger
                ↓
               coder
```

第四阶段：

``` text
START
 ↓
retrieve_experience
 ↓
planner
 ↓
coder
 ↓
test
 ↓
critic
 ↓
route
 ├── accepted → save_experience → END
 ├── retry → debugger → coder
 └── rejected → save_experience → END
```

这就是你最终真正需要掌握的 LangGraph。

------------------------------------------------------------------------

# 18. 自进化模块的 LangGraph State

最终 State 可以逐渐演化：

``` python
class CodingState(TypedDict):
    messages: list
    task: str
    plan: list
    relevant_files: list
    changes: list
    test_result: dict
    errors: list
    attempts: int
    experience: list
    final_status: str
```

不要一次全部加入。

推荐：

## 第一版

``` text
messages
```

### 第二版

``` text
messages
plan
```

### 第三版

``` text
messages
plan
test_result
attempts
```

### 第四版

``` text
messages
plan
test_result
attempts
experience
```

这样每一步都能理解 State 如何演化。

------------------------------------------------------------------------

# 19. 三个仓库对应你的文件

  ------------------------------------------------------------------------
  你的文件             Open SWE            mini-code-agent   self-improving
  ------------------------------------------------------------------------
  `coding_agent.py`    `agent/server.py` / `agent.py`        orchestrator
                       Agent assembly  

  `code_tools.py`      Deep Agents         `executor.py`     coder tools
                       file/search tools  

  `agents.py`          graph entrypoints   agent entry       orchestrator

  `coding_prompt.py`   `agent/prompt.py`   ---               coder prompt

  `test_tools.py`      shell / validation  executor /        critic
                                           verification  

  `experience.py`      memory / learned    memory_store.py   memory agent
                       guidance 思想  

  `reviewer.py`        reviewer graph      verification      critic

  `middleware.py`      middleware          ---               ---

`coding_memory.py`   thread/state 思想   memory_store      memory
---------------------------------------------------------------------------

------------------------------------------------------------------------

# 20. 哪些代码"直接抄"

这里必须区分：

## 可以直接参考结构

``` text
函数组织
State 字段设计
Graph 节点划分
条件边逻辑
工具返回结构
测试结果结构
Memory 数据结构
```

## 不建议直接复制

``` text
Open SWE 整套 server
Deep Agents 整套 harness
云 Sandbox
GitHub App
Slack integration
Linear integration
Dashboard
完整 Transaction Runtime
HMAC receipt
QLoRA/KTO training
```

原因：

> 复制这些东西会让你失去 LangGraph
> 学习价值，而且会把项目复杂度一下拉高。

------------------------------------------------------------------------

# 21. 魔改阶段总表

  阶段   功能                   文件                 学习重点                 状态
  ------------------------------------------------------------------------
  0      原项目运行             全项目               Service 架构             ✅
  1      LangGraph Mini Graph   `lg_practice/`       State/Node/Edge          ✅
  2      RAG                    `tools.py`           Retriever                ✅
  3      BGE-M3                 `tools.py`           Embedding                ✅
  4      list/read              `code_tools.py`      Tool Calling             ✅
  5      Coding Agent           `coding_agent.py`    Agent Loop               ✅
  6      search_code            `code_tools.py`      Code Retrieval           **当前**
  7      write/edit             `code_tools.py`      Code Editing             ⏳
  8      diff                   `code_tools.py`      Patch                    ⏳
  9      Planning               `coding_agent.py`    Graph Routing            ⏳
  10     Test                   `test_tools.py`      Execution                ⏳
  11     Debug Loop             `coding_agent.py`    Conditional Loop         ⏳
  12     Reviewer               `reviewer.py`        Subgraph / Agent         ⏳
  13     HITL                   Graph                `interrupt()`            ⏳
  14     Trajectory             `trajectory`         Evaluation               ⏳
  15     Experience Memory      `experience.py`      Store                    ⏳
  16     Experience Retrieval   `coding_memory.py`   RAG + Memory             ⏳
  17     Self-Correction        Graph                Experience-guided loop   ⏳
  18     Benchmark              `evals/`             Agent Evaluation         ⏳
  19     Sandbox                后期                 安全执行                 ⏳
  20     Docker                 后期                 工程化                   ⏳

------------------------------------------------------------------------

# 22. 详细执行顺序

## Phase A：Code Retrieval

### A1

新增：

``` text
search_code
```

验收：

``` text
搜索类名
搜索函数名
搜索普通关键词
限制返回数量
返回路径
返回行号
```

必须完成。

------------------------------------------------------------------------

## Phase B：Code Editing

新增：

``` text
write_file
edit_file
```

验收：

``` text
能新增文件
能局部修改文件
能拒绝项目外路径
能处理不存在的 old_text
能返回修改结果
```

------------------------------------------------------------------------

## Phase C：Diff

新增：

``` text
git_diff
```

验收：

``` text
Agent 修改
↓
git diff
↓
看到具体修改
```

这是进入真正 Coding Agent 的关键。

------------------------------------------------------------------------

## Phase D：Planning

增加：

``` text
planner
```

要求：

``` text
用户需求
↓
Planner
↓
明确：
1. 修改哪些文件
2. 为什么修改
3. 修改顺序
4. 如何验证
```

然后再交给 coder。

------------------------------------------------------------------------

# 23. Phase E：Test / Debug

加入：

``` text
run_tests
```

Graph：

``` text
Coder
 ↓
Test
 ↓
PASS?
 ├── YES → Reviewer
 └── NO → Debugger
             ↓
            Coder
```

必须设置：

``` text
MAX_RETRIES = 3
```

防止：

``` text
Coder
 ↓
Test
 ↓
Fail
 ↓
Coder
 ↓
Test
 ↓
Fail
...
```

无限循环。

------------------------------------------------------------------------

# 24. Phase F：Reviewer

Reviewer 不应该继续修改代码。

它应该只负责：

``` text
检查 diff
检查需求
检查测试
检查潜在问题
给出 verdict
```

例如：

``` python
{
    "approved": True,
    "score": 0.92,
    "issues": [],
    "summary": "..."
}
```

如果：

``` text
approved = False
```

回到：

``` text
Coder
```

------------------------------------------------------------------------

# 25. Phase G：Experience Memory

记录：

``` text
task
plan
files
errors
attempts
changes
test result
review result
final status
```

保存：

``` text
accepted
```

或者：

``` text
rejected
```

------------------------------------------------------------------------

# 26. Phase H：Experience Retrieval

下一次任务开始：

``` text
User Task
 ↓
Experience Retrieval
 ↓
找类似历史任务
 ↓
Planner
```

例如历史：

``` text
FastAPI 404
```

新任务：

``` text
FastAPI endpoint 找不到
```

检索到：

``` text
过去曾经因为 route registration 出现 404
```

于是 Planner 得到额外 context。

------------------------------------------------------------------------

# 27. 最终"自进化"实验

至少准备：

``` text
20~50 个 Coding Tasks
```

分两组：

## Baseline

``` text
Coding Agent
```

### Improved

``` text
Coding Agent
+
Experience Memory
```

比较：

``` text
Task Success Rate
Average Attempts
Average Tool Calls
Average Test Pass Rate
Average Time
```

如果：

``` text
Experience Memory
```

能减少：

``` text
平均修复次数
```

或者提高：

``` text
测试通过率
```

你的"自进化"就有了实验依据。

------------------------------------------------------------------------

# 28. 最终项目卖点

最终不要宣传：

> "我做了一个 Claude Code。"

应该宣传：

> **Built a LangGraph-based AI Coding Agent with code retrieval,
> planning, patch-based editing, test-driven self-correction,
> human-in-the-loop control, and experience-guided memory.**

中文：

> **基于 LangGraph 构建 AI Coding Agent，实现代码检索、任务规划、Patch
> 编辑、测试驱动自修复、人机协同和经验引导的持续改进机制。**

------------------------------------------------------------------------

# 29. 你当前绝对不要做的事情

现在暂时禁止：

``` text
❌ 整体复制 Open SWE
❌ 接 GitHub App
❌ 接 Slack
❌ 接 Linear
❌ 做 Dashboard
❌ 做 QLoRA
❌ 做 KTO
❌ 做复杂云 Sandbox
❌ 做多 Agent 大拆分
❌ 一次性加入 20 个 Tool
```

当前唯一任务：

``` text
search_code
```

------------------------------------------------------------------------

# 30. 当前第一关：search_code

当前项目已有：

``` text
list_files
read_file
```

目标：

``` text
list_files
      ↓
search_code
      ↓
read_file
```

让 Agent 学会：

> **先定位，再精读。**

建议流程：

``` text
用户问题
 ↓
model
 ↓
search_code
 ↓
得到命中位置
 ↓
read_file
 ↓
得到上下文
 ↓
model
 ↓
回答
```

------------------------------------------------------------------------

# 31. 下一阶段的第一批新文件

不要全部创建。

第一批只创建：

``` text
src/agents/code_tools.py
    ↑ 修改 search_code

src/agents/coding_agent.py
    ↑ 不急着大改

src/agents/agents.py
    ↑ 暂时只保持注册
```

第二批：

``` text
src/agents/test_tools.py
```

第三批：

``` text
src/agents/coding_prompt.py
```

第四批：

``` text
src/agents/experience.py
src/agents/coding_memory.py
```

第五批：

``` text
src/agents/reviewer.py
```

------------------------------------------------------------------------

# 32. 每一个阶段必须有"过关题"

## Search Code

必须回答：

> `search_code` 为什么比 `list_files + read_file` 更适合 Coding Agent？

------------------------------------------------------------------------

## Edit

必须回答：

> 为什么 `edit_file` 比直接让 LLM 重写整个文件更安全？

------------------------------------------------------------------------

## Planning

必须回答：

> Planner 的输出为什么应该进入 State，而不是只打印给用户？

------------------------------------------------------------------------

## Test

必须回答：

> 测试结果如何重新进入 LangGraph State？

------------------------------------------------------------------------

## Debug

必须回答：

> Graph 如何判断 PASS / FAIL 并决定 END 还是回到 Coder？

------------------------------------------------------------------------

## Memory

必须回答：

> Experience 为什么不能只是聊天历史？

------------------------------------------------------------------------

## Self-Improving

必须回答：

> 你的 Agent
> 到底"进化"了什么？是模型参数变了，还是决策过程利用了历史经验？

------------------------------------------------------------------------

# 33. 当前最重要的学习原则

每加入一个参考项目里的机制，都必须完成：

``` text
看源码
 ↓
画 Graph
 ↓
解释 State
 ↓
自己重写
 ↓
跑测试
 ↓
制造一个失败案例
 ↓
解释为什么失败
 ↓
修复
 ↓
写到 Git commit
```

不要：

``` text
复制
↓
能跑
↓
结束
```

------------------------------------------------------------------------

# 34. Git Commit 建议

以后每个阶段单独提交：

``` text
feat(coding): add code search tool
feat(coding): add safe file editing
feat(coding): add patch generation
feat(coding): add coding planner
feat(coding): add test execution loop
feat(coding): add self-correction loop
feat(coding): add coding reviewer
feat(memory): add coding experience store
feat(memory): add experience retrieval
feat(coding): add experience-guided self-correction
test(coding): add coding agent evaluation set
```

这样最后 GitHub 历史本身就是你的学习路线。

------------------------------------------------------------------------

# 35. 三个参考项目最终怎么用

``` text
OPEN SWE
│
├── 看架构
├── 看 Prompt
├── 看 Tools
├── 看 Middleware
├── 看 Sandbox
└── 看 Reviewer / Analyzer
        │
        ▼
    不整体复制


MINI CODE AGENT
│
├── 看 Agent Loop
├── 看 Verification
├── 看 Trajectory
├── 看 Transaction
├── 看 Memory
└── 看 Security
        │
        ▼
    选择性重写


SELF-IMPROVING CODE AGENT
│
├── 看 Critic
├── 看 Score
├── 看 Retry
├── 看 Memory
└── 看 Feedback Loop
        │
        ▼
    改造成自己的
    Experience-Guided
    Self-Correction
```

------------------------------------------------------------------------

# 36. 最终路线图

``` text
                     现在
                       │
                       ▼
              ┌────────────────┐
              │ search_code    │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ write/edit     │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ diff / patch   │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Planning       │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Test           │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Debug Loop     │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Reviewer       │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ HITL           │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Experience     │
              │ Memory         │
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │ Retrieval      │
              └───────┬────────┘
                      ▼
              ┌────────────────────────┐
              │ Experience-Guided      │
              │ Self-Correction        │
              └───────────┬────────────┘
                          ▼
                    Evaluation
                          ▼
                 Docker / Sandbox
```

------------------------------------------------------------------------

# 37. 结论

你的项目现在**不用换仓库**。

最合理的组合是：

``` text
agent-service-toolkit
       +
Open SWE 架构思想
       +
mini-code-agent 的 Verification / Trajectory / Transaction 思想
       +
self-improving-code-agent 的 Critic / Retry / Memory 思想
       ↓
自己的 LangGraph AI Coding Agent
       ↓
Experience-Guided Self-Correction
```

最重要的顺序只有一句：

> **先把 Coding Agent
> 做"会找代码"，再做"会改代码"，再做"会测试"，再做"会修复"，最后才做"会从过去的修复中学习"。**

当前任务仍然是：

``` text
★★★★★ search_code
```

不要跳到自进化。

------------------------------------------------------------------------

# 38. 参考资料

- Open SWE: `https://github.com/langchain-ai/open-swe`
- Open SWE Customization:
  `https://github.com/langchain-ai/open-swe/blob/main/docs/CUSTOMIZATION.md`
- mini-code-agent-langgraph:
  `https://github.com/wusuiling-if/mini-code-agent-langgraph`
- self-improving-code-agent:
  `https://github.com/IoanRoume/self-improving-code-agent`

本文中的参考仓库能力判断以 2026-09-15
检索到的仓库内容为准；这些项目仍在变化，因此真正开始移植某个模块时，应再次查看对应仓库当前版本源码。

------------------------------------------------------------------------

# 19. 新增：AICoding Agent 的核心顾虑、解决方案与测试体系

这一章把本次新增的"顾虑 + 解决方法 + 如何测试"正式并入魔改路线。

> **核心原则：不要追求让 LLM 永远不犯错，而要让整个 AICoding System
> 具备"错误可发现、结果可验证、失败可恢复、能力可迭代"的能力。**

## 19.1 核心问题：AICoding 不能只看"代码生成得像不像"

普通聊天 Agent 的回答只要语义合理即可。

AICoding Agent 不一样：

``` text
用户需求
   ↓
Agent 理解
   ↓
Code Retrieval / RAG
   ↓
Plan
   ↓
Code Edit
   ↓
Execute
   ↓
Test
   ↓
PASS ─────────→ Review → END
   │
   ↓ FAIL
Debug
   ↓
Fix
   ↓
再次 Test
   ↓
Evaluation
   ↓
Experience Store
```

因此项目真正追求的是：

``` text
不是：
LLM 永远正确

而是：
LLM 即使犯错
    ↓
系统能够发现错误
    ↓
能够定位错误
    ↓
能够尝试修复
    ↓
能够再次验证
    ↓
失败可以停止 / 回滚 / 人工接管
    ↓
成功或失败经验可以沉淀
```

这也是后续 LangGraph 设计的核心。

------------------------------------------------------------------------

# 20. 顾虑一：我的 Coding Agent 会不会只是"套了一个 Agent 壳"？

## 问题

如果项目最终只是：

``` text
User
 ↓
LLM
 ↓
生成代码
```

那么本质上只是 AI Code Generation，而不是完整的 AICoding Agent。

## 解决方案

必须逐步把 Coding 变成一个闭环：

``` text
需求理解
 ↓
代码检索
 ↓
知识检索
 ↓
制定方案
 ↓
修改代码
 ↓
运行
 ↓
测试
 ↓
错误分析
 ↓
自动修复
 ↓
再次测试
 ↓
Review
 ↓
Evaluation
```

对应本项目的阶段：

``` text
当前
list_files
 ↓
read_file
 ↓
search_code

下一阶段
 ↓
write/edit
 ↓
run_tests
 ↓
debug
 ↓
review
 ↓
experience
```

## 怎么测试？

不能只问：

> "模型生成的代码看起来不错吗？"

而应该测试：

1. 能不能找到正确文件？
2. 能不能定位正确函数 / 类？
3. 能不能完成代码修改？
4. 修改后能不能运行？
5. 测试能不能通过？
6. 测试失败后能不能利用错误信息继续修复？
7. 最终任务能不能完成？

核心指标：

``` text
Task Success Rate
Test Pass Rate
First-Try Success Rate
Average Attempts
Average Tool Calls
Human Intervention Rate
```

------------------------------------------------------------------------

# 21. 顾虑二：Code Repository 和 RAG 会不会重复？

这是后续架构必须提前解决的问题。

## 两者不要定义成同一种东西

  数据源            主要内容                 主要回答的问题
  ------------------------------------------------------------------------
  Code Repository   当前项目源代码           "代码现在是什么？"
  RAG Knowledge     文档、规范、经验、方案   "应该怎么做？"

例如：

``` text
用户：
修改支付重试逻辑
```

Code Retrieval：

``` text
找到 retryPayment()
```

RAG：

``` text
公司规范：
支付最多重试 3 次
```

所以：

``` text
Code Repository = Implementation Ground Truth
RAG = Knowledge / Policy Ground Truth
```

## 后续 Code Retrieval 不应该只有 Vector Search

逐步升级为：

``` text
Keyword Search
+
Semantic Search
+
Symbol Search
+
AST
+
Dependency Graph
```

当前只做：

``` text
search_code
```

先把最基本的关键词 / 文本检索跑通。

## 怎么测试？

准备一批已知代码位置的测试任务：

``` text
问题：
“找到用户登录失败重试逻辑”

Ground Truth：
auth/service.py
retry_login()
```

测试：

``` text
Top-1 Retrieval Accuracy
Top-5 Retrieval Recall
正确文件命中率
正确 Symbol 命中率
```

当前阶段不需要一次性做复杂 Benchmark。

先验证：

``` text
search_code("retry")
    ↓
是否真的返回包含 retry 的正确文件 / 行号 / 代码片段
```

------------------------------------------------------------------------

# 22. 顾虑三：Agent 自己的代码和用户代码库是什么关系？

这是 Coding Agent 很容易混乱的地方。

``` text
Agent Code
    ↓
“我应该怎么工作？”

Code Repository
    ↓
“我要修改什么？”
```

可以把它理解成：

``` text
Agent = 工程师
Tool = 工程师使用的工具
LangGraph = 工程师的工作流程
Code Repository = 工程师正在工作的项目
```

例如 Agent 自己的代码：

``` text
coding_agent.py
code_tools.py
agents.py
planner.py
reviewer.py
```

负责定义 Agent 行为。

而目标代码库可能是：

``` text
frontend/
backend/
database/
tests/
```

负责成为 Agent 的工作对象。

## 怎么测试？

做"边界测试"：

``` text
Agent 不应该：
修改自己的 Agent Framework
```

除非用户明确要求修改 Agent 本身。

测试：

``` text
给 Agent 一个：
“修改 demo_project 中的 login.py”

观察：
是否只访问 / 修改 demo_project？
是否错误修改 coding_agent.py？
```

后续要加入：

``` text
Path Validation
Workspace Root
Permission Boundary
```

------------------------------------------------------------------------

# 23. 顾虑四：为什么不用现成 Codex，而要自己做 AICoding Agent？

不要把问题理解成：

``` text
自己做 AICoding
vs
Codex
```

更准确的是：

``` text
企业 Agent Platform
        ↓
    Coding Skill
        ↓
 ┌──────┼──────┐
 ↓      ↓      ↓
自研   Codex  其他 Coding Agent
```

企业真正需要控制的是：

``` text
企业代码
企业知识
企业权限
企业 Workflow
企业 MCP
企业 CI/CD
企业 Review
企业数据
```

所以这个项目的学习目标不是：

> "造一个比 Codex 更强的模型。"

而是：

> **学习如何把 Coding Model 放进一个可控制、可验证、可扩展的 Agent
> 系统。**

## 怎么测试？

未来可以做模型替换实验：

``` text
Strong Model
     ↓
同一套 Agent Workflow
     ↓
Local / Weaker Model
```

保持：

``` text
Tools
Workflow
Test
Evaluation
```

不变。

比较：

``` text
Task Success Rate
Average Attempts
Token Cost
Latency
```

从而验证：

> 模型是可替换组件，而不是整个系统本身。

------------------------------------------------------------------------

# 24. 顾虑五：AICoding Agent 到底应该能做什么？

最终可以逐渐覆盖六类任务：

## ① 新功能开发

``` text
Requirement
 ↓
Code Analysis
 ↓
Implementation
 ↓
Test
 ↓
Review
 ↓
PR
```

### ② Bug 修复

``` text
Bug / Error
 ↓
Logs
 ↓
Code Retrieval
 ↓
Root Cause
 ↓
Fix
 ↓
Test
```

### ③ 自动测试

``` text
Code
 ↓
Generate Test
 ↓
Execute
 ↓
Failure
 ↓
Fix
```

### ④ 重构 / 技术债

``` text
Old Code
 ↓
Dependency Analysis
 ↓
Migration Plan
 ↓
Batch Edit
 ↓
Test
```

### ⑤ Code Review

``` text
Diff
 ↓
Bug
 ↓
Security
 ↓
Style
 ↓
Performance
 ↓
Review
```

### ⑥ 自动化研发流程

``` text
Jira / Issue
 ↓
Agent
 ↓
RAG
 ↓
Code
 ↓
Test
 ↓
Review
 ↓
CI/CD
 ↓
PR
```

当前项目**不要全部实现**。

优先顺序仍然是：

``` text
search_code
 ↓
edit
 ↓
test
 ↓
debug
 ↓
review
 ↓
experience
```

------------------------------------------------------------------------

# 25. 顾虑六：AICoding 如何做到"准确"？

这是整个项目最重要的设计原则之一。

## 不要要求 LLM 自己证明自己正确

错误做法：

``` text
LLM：
“我检查过了，这段代码应该没问题。”
```

正确做法：

``` text
LLM
 ↓
Compiler
 ↓
Type Check
 ↓
Lint
 ↓
Unit Test
 ↓
Integration Test
 ↓
Security Scan
 ↓
CI
```

把：

``` text
“我认为是对的”
```

变成：

``` text
“系统验证通过了”
```

## 最关键原则

> **LLM 负责提出方案，确定性系统负责验证事实。**

适合交给 LLM：

``` text
理解
推理
规划
生成
Debug
```

不要只交给 LLM：

``` text
是否编译通过
测试是否通过
权限是否正确
是否满足 CI
是否允许提交
```

这些应该尽量由：

``` text
Compiler
Test
Linter
Type Checker
Security Scanner
CI/CD
Permission System
```

完成。

------------------------------------------------------------------------

# 26. 顾虑七：如何实现真正的自纠错？

核心循环：

``` text
Generate
   ↓
Execute
   ↓
Observe
   ↓
Reflect
   ↓
Fix
   ↓
Execute
```

LangGraph 中可以显式建模：

``` text
Planner
   ↓
Coder
   ↓
Tester
   ↓
 ┌─┴───────┐
 ↓         ↓
PASS      FAIL
 ↓         ↓
Reviewer  Debugger
 ↓         ↓
END       Coder
           ↓
         Tester
```

State 至少需要逐步承载：

``` python
state = {
    "requirement": ...,
    "plan": ...,
    "files": ...,
    "changes": ...,
    "test_result": ...,
    "error": ...,
    "iteration": ...
}
```

当前不要一次性加入所有字段。

当前仍然只推进：

``` text
search_code
```

然后再逐步增加：

``` text
edit
test_result
error
iteration
```

## 怎么测试？

人为制造一个确定会失败的任务：

``` text
已有：
def add(a, b):
    return a - b
```

任务：

``` text
让 add() 正确返回两数之和
```

流程应该出现：

``` text
修改
 ↓
Test
 ↓
PASS
```

再设计一个会产生错误的任务：

``` text
修改代码
 ↓
Test
 ↓
FAIL
 ↓
读取 stderr / traceback
 ↓
Debug
 ↓
Fix
 ↓
Test
 ↓
PASS
```

测试的不是"第一次一定正确"，而是：

> **第一次错误以后，Agent 是否能利用反馈完成修复。**

------------------------------------------------------------------------

# 27. 顾虑八：如果换成一个很笨的本地模型，Agent 会不会不能用了？

答案是：

``` text
模型能力下降
≠
系统完全失效
```

如果系统只是：

``` text
AICoding = LLM
```

那么确实会高度依赖模型。

但如果是：

``` text
AICoding =
LLM
+
Code Retrieval
+
Tools
+
Workflow
+
Test
+
Verification
+
RAG
+
Memory
+
Model Routing
```

那么弱模型主要影响：

``` text
理解能力
规划能力
Debug 能力
复杂任务完成率
```

但系统仍然可以保留：

``` text
确定性检索
工具执行
测试
验证
状态管理
安全边界
```

------------------------------------------------------------------------

# 28. 顾虑九：如何解决不同模型能力不同？

## Model Routing

不要让一个模型承担全部任务：

``` text
Agent
 ↓
Model Router
 ↓
 ┌──────────┼──────────┐
 ↓          ↓          ↓
强模型     中模型      本地模型
 ↓          ↓          ↓
复杂任务   普通任务    简单任务
```

例如：

``` text
修改变量名
→ 本地模型

增加参数校验
→ 中等模型

重构支付系统
→ 强模型
```

## 更进一步：角色分工

``` text
Supervisor
 ↓
 ┌──────────┼──────────┐
 ↓          ↓          ↓
Planner    Coder     Reviewer
 ↓          ↓          ↓
强模型     本地模型   强模型
```

这样可以：

``` text
强模型：
负责规划 / Review / 复杂 Debug

本地模型：
负责具体 Coding
```

## 怎么测试？

建立同一批任务：

``` text
Model A
Model B
Local Model
```

保持：

``` text
Prompt
Tools
Workflow
Tests
```

尽量一致。

比较：

``` text
Task Success Rate
First-Try Success Rate
Average Attempts
Token Cost
Latency
```

这样才能知道：

> 到底是模型变强了，还是 Agent Workflow 变强了。

------------------------------------------------------------------------

# 29. 顾虑十：怎么证明 Agent "真的进化"了？

不能使用：

> "感觉它越来越聪明。"

必须建立 Evaluation System。

每次 Coding Task 至少记录：

``` text
Task
 ↓
Agent
 ↓
Result
```

保存：

``` text
任务类型
任务难度
修改文件
代码变更
测试结果
错误次数
修复次数
Tool Calls
Token
耗时
人工修改量
最终是否成功
```

最终形成：

``` text
Task
 ↓
Trajectory
 ↓
Evaluation
 ↓
Experience
```

------------------------------------------------------------------------

# 30. AICoding Agent 的五层测试体系

## Level 1：代码正确性

``` text
Compile
Type Check
Lint
Unit Test
Integration Test
```

回答：

> 代码能不能运行？

## Level 2：功能正确性

例如：

``` text
Input:
100

Expected:
200

Actual:
200
```

回答：

> 功能是不是正确？

## Level 3：任务完成率

例如 100 个真实任务：

``` text
85 成功
15 失败
```

则：

``` text
Task Success Rate = 85%
```

这是 Coding Agent 最核心的指标之一。

## Level 4：Agent 行为质量

观察：

``` text
Tool Call 次数
错误 Tool Call
重复搜索
无效修改
无限循环
错误文件修改
```

回答：

> Agent 是否在高效工作？

## Level 5：企业级安全

测试：

``` text
权限
敏感数据
越权访问
危险命令
生产环境操作
代码泄露
```

回答：

> Agent 是否安全可控？

------------------------------------------------------------------------

# 31. 当前项目应该如何建立测试体系？

不要一开始就做一个巨大的 Benchmark。

采用：

``` text
单工具测试
 ↓
节点测试
 ↓
Graph 测试
 ↓
Coding Task 测试
 ↓
Regression Benchmark
```

## Stage 1：Tool Test

当前：

``` text
list_files
read_file
search_code
```

分别测试：

``` text
正常输入
空输入
不存在文件
不存在关键词
超长输出
路径越界
编码异常
```

例如：

``` text
search_code("retry")
```

必须验证：

``` text
是否真的搜索到了 retry
是否返回文件路径
是否返回匹配位置
是否返回上下文
不存在关键词时是否稳定返回
```

## Stage 2：Node Test

例如未来：

``` text
planner_node
coder_node
tester_node
reviewer_node
```

每个节点单独测试：

``` text
Input State
 ↓
Node
 ↓
Output State
```

重点检查：

``` text
输入字段是否正确
输出字段是否正确
是否修改了不该修改的字段
异常是否可控
```

## Stage 3：Graph Test

测试完整 LangGraph：

``` text
START
 ↓
Planner
 ↓
Coder
 ↓
Tester
 ↓
Conditional Edge
```

至少测试：

``` text
PASS 路径
FAIL 路径
Retry 路径
Max Retry 路径
异常路径
```

## Stage 4：真实 Coding Task Test

建立 20～50 个任务。

例如：

``` text
Task 001：
修复一个函数 Bug

Task 002：
增加参数校验

Task 003：
增加一个 Unit Test

Task 004：
重构一个简单函数

...
```

每个任务保存：

``` text
Task ID
Repository
Requirement
Expected Files
Expected Behavior
Test Command
Expected Result
```

## Stage 5：Regression Benchmark

以后每一次修改：

``` text
修改 Agent
 ↓
重新跑全部 Benchmark
 ↓
比较结果
```

防止：

``` text
search_code 变好了
但是 test/debug 变坏了
```

------------------------------------------------------------------------

# 32. 如何验证"自进化"到底有效？

最终做一个非常重要的 A/B Experiment。

## Baseline

``` text
Coding Agent
+
Code Retrieval
+
Tools
+
Test
```

## Improved

``` text
Coding Agent
+
Code Retrieval
+
Tools
+
Test
+
Experience Retrieval
```

使用同一批任务。

比较：

  指标                       Baseline   Improved
  ------------------------------------------------------------------------
  Task Success Rate  
  First-Try Success Rate  
  Average Attempts  
  Average Tool Calls  
  Test Pass Rate  
  Human Intervention  
  Token Cost  
  Task Time  

如果加入 Experience Memory 后：

``` text
Task Success Rate ↑
First-Try Success Rate ↑
Average Attempts ↓
Human Intervention ↓
```

才可以有依据地说：

> Experience-Guided Self-Correction 对 Coding Agent 有帮助。

这比单纯说"Agent 可以自我进化"更有说服力。

------------------------------------------------------------------------

# 33. "自进化"不要一上来就 Fine-tuning

可以把自进化分成五层：

``` text
Level 1 Prompt
      ↓
Level 2 Workflow
      ↓
Level 3 Tool
      ↓
Level 4 Knowledge / Experience
      ↓
Level 5 Model
```

## Level 1：Prompt 优化

发现：

``` text
Agent 经常忘记测试
```

加入：

``` text
修改代码后必须运行相关测试。
```

## Level 2：Workflow 优化

发现：

``` text
直接 Coding → Test
经常失败
```

改成：

``` text
Requirement
 ↓
Code Search
 ↓
Dependency Analysis
 ↓
Coding
 ↓
Test
```

## Level 3：Tool 优化

发现：

``` text
Agent 经常找不到代码
```

逐步增加：

``` text
Keyword Search
Symbol Search
AST
Semantic Search
Dependency Graph
```

## Level 4：Experience / Knowledge 优化

保存：

``` text
Bug
 ↓
Cause
 ↓
Fix
 ↓
Test Result
 ↓
Review
```

下一次：

``` text
New Bug
 ↓
Retrieve Similar Experience
 ↓
Reference
 ↓
Fix
```

## Level 5：Model 优化

未来才考虑：

``` text
Coding Tasks
+
Correct Answers
+
Wrong Answers
+
Test Results
+
Human Feedback
```

再考虑：

``` text
Fine-tuning
Preference Optimization
RL
```

当前项目不做 QLoRA / KTO。

当前项目重点：

``` text
LangGraph
+
Coding Workflow
+
Verification
+
Experience Memory
+
Evaluation
```

------------------------------------------------------------------------

# 34. 最终完整架构：把"顾虑"和"测试"真正接入魔改路线

``` text
                         Coding Task
                              ↓
                    ┌──────────────────┐
                    │  Task Analyzer   │
                    └────────┬─────────┘
                             ↓
                  Code Retrieval + RAG
                             ↓
                    Experience Retrieval
                             ↓
                          Planner
                             ↓
                           Coder
                             ↓
                     Execute / Test
                             ↓
                    ┌────────┴────────┐
                    ↓                 ↓
                  PASS              FAIL
                    ↓                 ↓
                 Reviewer          Debugger
                    ↓                 ↓
                    └───────┬─────────┘
                            ↓
                        Evaluation
                            ↓
                     Experience Store
                            ↓
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          Prompt         Workflow        RAG / Memory
          优化             优化             更新
             └──────────────┼──────────────┘
                            ↓
                      Model Routing
                            ↓
                       下一次任务
```

外围必须有：

``` text
Permission Boundary
Path Validation
Sandbox
HITL
Rollback
CI
Security
```

------------------------------------------------------------------------

# 35. 本项目新增的"可靠性原则"

后续每一个功能都用下面这套问题检查：

## ① 能不能验证？

``` text
有没有确定性测试？
```

### ② 失败怎么办？

``` text
有没有 Error → Debug → Retry？
```

### ③ 改错了怎么办？

``` text
有没有 Diff / Rollback / HITL？
```

### ④ Agent 有没有乱改？

``` text
有没有 Workspace / Path Boundary？
```

### ⑤ 换模型还能不能工作？

``` text
Workflow / Tools / Verification 是否独立于模型？
```

### ⑥ 怎么证明变好了？

``` text
有没有 Benchmark？
有没有 Baseline？
有没有 A/B Experiment？
```

### ⑦ 经验有没有真正发挥作用？

``` text
Experience Retrieval
 ↓
是否减少重复错误？
 ↓
是否提高成功率？
```

------------------------------------------------------------------------

# 36. 与三个参考仓库的对应关系重新整理

  ------------------------------------------------------------------------
  参考仓库                    本项目主要学习内容                                        当前是否直接移植
  ------------------------------------------------------------------------
  open-swe                    Agent 架构、工具体系、Sandbox、Review、CI、Middleware     否，主要学习架构

  mini-code-agent-langgraph   Transaction、Verification、Trajectory、Memory、安全边界   部分移植思想

  self-improving-code-agent   Critic、Score、Retry、Memory、自修复闭环                  部分移植思想

本项目                      LangGraph + Coding + RAG + Verification + Experience      主体
-------------------------------------------------------------------------------------------------------------

最终不要变成：

``` text
Open SWE + mini-code-agent + self-improving
```

而应该变成：

``` text
agent-service-toolkit
        +
Open SWE 架构思想
        +
mini-code-agent 的可靠性思想
        +
self-improving 的经验闭环
        ↓
自己的 LangGraph AI Coding Agent
```

------------------------------------------------------------------------

# 37. 更新后的魔改优先级

非常重要：

**不要因为加入了这些顾虑，就改变当前学习节奏。**

当前仍然是：

``` text
现在
 ↓
search_code
```

之后才是：

``` text
search_code
 ↓
write/edit
 ↓
run_tests
 ↓
Planner
 ↓
Debug / Self-Correction
 ↓
Reviewer
 ↓
HITL
 ↓
Experience Memory
 ↓
Evaluation
 ↓
Model Routing
```

也就是说：

> **"可靠性体系"现在先作为架构设计原则和测试标准加入脑子里，但代码仍然一层一层实现。**

当前最重要的验收标准仍然只有：

``` text
search_code
```

做到：

``` text
输入关键词
 ↓
搜索目标 Workspace
 ↓
找到匹配代码
 ↓
返回文件路径
 ↓
返回行号 / 上下文
 ↓
Agent 能够利用搜索结果继续工作
```

完成这一关之后，再进入下一阶段。

------------------------------------------------------------------------

# 38. 最终项目可以如何包装成一个完整项目故事

最终面试 / 项目介绍可以形成：

> 我基于 LangGraph 构建了一个 AI Coding
> Agent。最开始它只有文件浏览和代码读取能力，之后逐步加入代码检索、代码编辑、测试执行、错误分析和自动修复，并通过
> LangGraph 显式管理 Planner、Coder、Tester、Debugger、Reviewer
> 等状态和路由。
>
> 在可靠性方面，我没有把"代码正确性"交给 LLM 自己判断，而是建立了
> Compile / Test / Lint / Type Check
> 等验证机制，并记录每次任务的错误、修改、测试结果和迭代轨迹。
>
> 在此基础上，我加入 Experience-Guided Self-Correction：将成功和失败的
> Coding Experience 结构化保存，并在新任务中检索相似经验，帮助 Agent
> 减少重复试错。
>
> 最后通过离线 Coding Benchmark 对比加入 Experience Memory 前后的 Task
> Success Rate、First-Try Success Rate、Average Attempts、Tool Calls
> 和人工干预量，从实验上验证 Agent 是否真的得到改进。

这个项目故事的重点不是：

``` text
“我调用了某个大模型 API。”
```

而是：

``` text
我设计了一个
可检索
可执行
可验证
可纠错
可评测
可持续优化
的 LangGraph Coding Agent。
```

------------------------------------------------------------------------

# 39. 一句话总纲

> **不要让模型承担所有可靠性。**

让：

``` text
LLM
负责：
理解 / 推理 / 规划 / 生成 / Debug

Tools
负责：
操作真实世界

Code Retrieval / RAG
负责：
提供事实和上下文

LangGraph
负责：
状态和 Workflow

Compiler / Test / Lint / CI
负责：
验证事实

HITL / Permission
负责：
风险控制

Experience Memory
负责：
沉淀过去经验

Evaluation
负责：
证明系统是否真的变好了
```

最终：

``` text
不可靠的 LLM
      ↓
可靠的 Agent System
      ↓
可靠的 Coding Workflow
      ↓
可验证的结果
      ↓
可持续优化的系统
```

这就是本项目从"LangGraph 练习项目"升级成"真正有工程深度的 AI Coding
Agent"时，最核心的设计思想。

# 40. 新增：Cost-Aware Adaptive Model Routing（成本感知自适应模型路由）

> 本项目进一步加入一个面向小团队/小企业部署场景的优化方向：**不让最高级模型承担所有 Coding 工作，而是根据任务复杂度、失败类型、上下文规模和剩余预算动态选择模型。**

## 40.1 为什么要做模型路由？

AI Coding Agent 的主要成本并不来自简单的 `search_code`，而主要集中在：

```text
大模型反复 Coding
        ↓
大段代码上下文重复输入
        ↓
Test 失败
        ↓
Debug
        ↓
再次 Coding
        ↓
再次 Test
```

因此需要同时关注两个指标：

- **Token 消耗热点**：强模型的 Coding / Debug / Review，以及失败重试时反复携带的大量代码上下文。
- **时间消耗热点**：模型推理延迟、Build / Test / Install，以及多轮 Agent Loop。

核心原则：

> **高能力模型负责高价值决策，低成本模型负责高频执行；确定性工具负责验证事实。**

## 40.2 推荐的模型分工

```text
                         Coding Task
                              ↓
                       Task Analyzer
                              ↓
                       Model Router
              ┌───────────────┼────────────────┐
              ↓               ↓                ↓
          Local 7B         Cheap API       Strong API
              ↓               ↓                ↓
      简单检索/总结/      普通 Coding/      复杂规划/架构/
      分类/重排/简单Debug  普通 Debug       复杂 Debug/Review
              └───────────────┼────────────────┘
                              ↓
                         Execute / Test
                              ↓
                       PASS / FAIL Router
                              ↓
                    必要时升级到 Strong Model
```

建议职责：

| 模型 | 主要职责 | 原则 |
|---|---|---|
| Local 7B | 代码摘要、错误分类、检索结果重排、简单修改/Debug、测试生成 | 高频、低成本、低延迟 |
| 普通/低价 API | 常规 Coding、普通 Debug、一般任务 | 性价比优先 |
| Strong API | 任务拆解、复杂规划、架构决策、复杂 Debug、最终 Review | 只处理高价值难题 |
| Deterministic Tools | Test、Compile、Lint、Type Check、Security Scan | 不交给 LLM 猜 |

## 40.3 “邪修”成本优化方案

### 方法 1：先检索，再给强模型

禁止默认把整个 Repository 塞给 Strong Model。

```text
User Task
 ↓
search_code
 ↓
Symbol / Dependency Filtering
 ↓
Local 7B / Embedding Rerank
 ↓
Top-K Relevant Context
 ↓
Strong Model
```

目标是让 Strong Model 看到“完成任务所需要的代码”，而不是“整个项目”。

### 方法 2：上下文压缩

把：

```text
大量原始代码
 ↓
局部函数 / Symbol
 ↓
依赖关系
 ↓
必要上下文
 ↓
Strong Model
```

避免每轮 Debug 都重复发送无关代码。

### 方法 3：Failure Router

```text
Test FAIL
 ↓
错误分类
 ├── 简单语法/类型错误 → Local 7B
 ├── 普通业务错误 → Cheap API
 └── 架构/复杂依赖问题 → Strong API
```

并设置升级规则：

```text
Local 7B 修复失败
 ↓
Cheap API
 ↓
仍失败
 ↓
Strong API
```

### 方法 4：Budget-aware State

后续可在 LangGraph State 中加入：

```python
state = {
    "attempts": ...,
    "llm_calls": ...,
    "estimated_tokens": ...,
    "budget": ...,
    "model_tier": ...,
}
```

Router 根据剩余预算和任务难度决定是否升级模型。

## 40.4 小企业 / 小团队是否适用？

适用，而且比“所有任务都调用最强模型”更符合成本受限的部署思路。

但要注意：**网页端 AI 不适合作为 Agent 后端的核心自动化执行器。**

网页端 AI 可以作为人工开发者的 Coding Copilot；真正进入 Agent 自动化链路的核心模型，优先使用可编程 API 或本地模型。原因是后端 Agent 需要：

- 可编程调用
- 可记录 Token / Cost
- 可控制权限
- 可审计
- 可接 Tool / MCP
- 可接测试与 CI/CD
- 可做模型自动路由

因此你的想法可以调整为：

```text
Strong API
  ↓
负责任务设计 / 复杂规划

Local 7B
  ↓
负责低成本分析 / 分类 / 摘要 / 简单 Debug

Coding Model / API
  ↓
负责主要代码实现

Test / Compile / Lint
  ↓
负责确定性验证

Strong API
  ↓
负责失败升级 / 复杂 Debug / Final Review
```

这比“网页 AI 写代码 + API 检查”更容易真正工程化。

## 40.5 新的项目创新点

项目可以新增一个明确的研究/工程问题：

> **Cost-Aware Adaptive AI Coding Agent：通过任务复杂度、错误类型、上下文规模和历史失败次数动态选择模型，在尽可能保持 Coding Success Rate 的同时降低 Token / API Cost。**

不要直接声称“省了多少成本”，必须通过实验验证。

### A/B 实验

准备同一批 Coding Tasks，例如 20–50 个。

**Baseline：**

```text
所有任务 → Strong Model
```

**Adaptive：**

```text
Local 7B + Cheap API + Strong API
          ↓
      Adaptive Router
```

比较：

```text
Task Success Rate
First-Try Success Rate
Average Attempts
Average Tool Calls
Average Tokens
Average API Cost
Average Time
Human Intervention Rate
```

最终目标不是单纯“省 Token”，而是证明：

```text
Adaptive Routing
       ↓
相近的 Task Success Rate
       +
更低的 Token / Cost
       +
更少的无意义 Strong Model 调用
```

这会比单纯“接了几个大模型 API”更像一个真正的 Agent 系统优化课题。

## 40.6 与当前开发节奏的关系

非常重要：**本节现在只作为架构设计，不改变当前实现顺序。**

当前仍然严格保持：

```text
search_code
 ↓
write / edit
 ↓
run_tests
 ↓
Planner
 ↓
Debug / Self-Correction
 ↓
Reviewer
 ↓
HITL
 ↓
Experience Memory
 ↓
Evaluation
 ↓
Model Routing
```

也就是说，Model Routing 是后期在已有 Coding Agent、Verification、Evaluation 都跑通之后再实现。

------------------------------------------------------------------------

# 41. 更新后的最终项目定位

最终项目不再只是：

> “一个能调用 LLM 写代码的 Agent。”

而是：

> **一个基于 LangGraph 的可检索、可执行、可验证、可纠错、可评测、可持续优化，并具备成本感知模型路由能力的 AI Coding Agent。**

完整故事：

```text
User Task
 ↓
Task Analyzer
 ↓
Code Retrieval + RAG
 ↓
Experience Retrieval
 ↓
Planner
 ↓
Model Router
 ↓
Coder / Editor
 ↓
Execute / Test
 ↓
PASS / FAIL
 ├── PASS → Reviewer
 └── FAIL → Failure Router → Debugger → Coder
 ↓
Experience Store
 ↓
Evaluation
 ↓
持续优化 Routing / Workflow / Knowledge / Prompt
```

其中：

```text
LLM：理解 / 推理 / 规划 / 生成 / Debug
Tools：搜索 / 编辑 / 执行 / 测试 / 验证
LangGraph：状态 / 路由 / 循环 / HITL
Memory：积累 Coding Experience
Evaluation：证明系统是否真的变好
Model Router：控制能力、速度与成本之间的平衡
```

------------------------------------------------------------------------

# 39. 新增：从 Knowledge Agent 到可编排 Agent 平台

前面的 AICoding 改造主要解决的是：

> **让 Agent 能够真正执行 Coding 任务，而不只是回答问题。**

但如果产品层面只是简单新增一个 `AICoding Agent`，用户看到的可能仍然只是：

```text
原来的 Knowledge Agent
        +
AICoding Agent
```

这样产品创新会比较弱。

因此，在原项目之上的进一步改进，不应该只增加一个新的 Agent，而应该改变**用户使用 Agent 的方式**。

## 39.1 核心改进

> **我可以创建 Agent、配置 Agent、修改 Agent、编排 Agent，让多个 Agent 协同完成任务。**

也就是说，把原来的：

```text
Knowledge Agent
↓
用户提问
↓
RAG
↓
回答
```

逐渐升级成：

```text
Agent Platform
        ↓
创建 Agent
        ↓
配置 Agent
├── Model
├── Prompt
├── Knowledge
├── Tools / MCP
├── Skills
└── Workflow
        ↓
编排 Agent
        ↓
多个 Agent 协同
        ↓
共同完成复杂任务
```

------------------------------------------------------------------------

## 39.2 用户使用流程的变化

### 原项目

```text
用户
 ↓
选择 Agent
 ↓
输入问题
 ↓
Agent 检索知识
 ↓
回答
```

### 改进后的平台

```text
用户
 ↓
选择 / 创建 Agent
 ↓
配置 Agent 能力
 ↓
选择 Knowledge / Tools / Skills
 ↓
设计 Workflow
 ↓
组合多个 Agent
 ↓
执行任务
 ↓
查看执行过程
 ↓
验证结果
 ↓
保存 / 更新 Agent
```

因此，改进的不只是 Agent 的能力，而是：

> **用户与 Agent 的交互方式发生了变化。**

从“使用一个已经做好的 Agent”，变成：

> **用户可以参与 Agent 的创建、配置、编排和持续优化。**

------------------------------------------------------------------------

## 39.3 Agent Builder / Agent 工作台

为了让这个改进真正体现在产品上，需要一个方便用户操作的界面。

可以增加一个：

> **Agent Builder / Agent 工作台**

例如：

```text
┌──────────────────────────────────────────────┐
│ Agent 工作台                                  │
├──────────────┬───────────────────────────────┤
│ 我的 Agents  │          Workflow              │
│              │                               │
│ Knowledge    │  用户需求                      │
│ Research     │      ↓                        │
│ Coding       │  Research Agent               │
│ Testing      │      ↓                        │
│ Review       │  Coding Agent                 │
│              │      ↓                        │
│              │  Testing Agent                │
│              │      ↓                        │
│              │  Review Agent                 │
├──────────────┴───────────────────────────────┤
│ Model │ Knowledge │ Tools │ Skills │ Logs     │
└──────────────────────────────────────────────┘
```

用户可以通过界面：

- 创建 Agent
- 修改 Prompt
- 选择模型
- 绑定知识库
- 添加 Tool / MCP
- 添加 Skill
- 调整 Workflow
- 连接多个 Agent
- 查看执行日志
- 测试 Agent
- 保存 Agent 配置

------------------------------------------------------------------------

## 39.4 Agent 可以被“修改”

例如已有：

```text
Code Review Agent
```

如果发现它经常遗漏安全问题，用户可以进入 Agent 配置：

```text
Code Review Agent
│
├── Prompt
├── Model
├── Knowledge
├── Tools
├── Skills
└── Workflow
```

然后增加：

```text
Security Review Skill
```

流程变成：

```text
Code Review
 ↓
代码质量检查
 ↓
Security Review
 ↓
性能检查
 ↓
输出 Review
```

因此 Agent 不再是一个固定的黑盒，而是：

> **可以被用户持续配置和修改的生产单元。**

------------------------------------------------------------------------

## 39.5 Agent 之间可以协同

进一步，可以让多个 Agent 共同完成一个任务。

例如软件开发任务：

```text
                    用户需求
                       ↓
                  Product Agent
                       ↓
                ┌──────┴──────┐
                ↓             ↓
         Research Agent   Coding Agent
                              ↓
                        Testing Agent
                              ↓
                        Review Agent
                              ↓
                           完成
```

不同 Agent 分工：

### Product Agent

负责：

```text
理解需求
拆解任务
定义验收标准
```

### Research Agent

负责：

```text
检索知识库
分析历史方案
查找相关文档
```

### Coding Agent

负责：

```text
分析代码
修改代码
生成 Patch
```

### Testing Agent

负责：

```text
生成测试
运行测试
分析测试结果
```

### Review Agent

负责：

```text
检查 Diff
检查需求
检查测试
检查潜在问题
```

这样 AICoding Agent 就不再是孤立的 Agent，而是：

> **Agent 协同体系中的一个执行节点。**

------------------------------------------------------------------------

## 39.6 AICoding Agent 在这个体系中的位置

因此，AICoding Agent 不应该被定义为：

> “新增的一个 Agent。”

而应该定义为：

> **一个能够操作代码仓库并执行软件开发任务的 Agent 能力。**

它可以被其他 Agent 调用。

例如：

```text
Research Agent
      ↓
找到相关技术方案
      ↓
Coding Agent
      ↓
修改代码
      ↓
Testing Agent
      ↓
验证
      ↓
Review Agent
      ↓
检查
```

也可以反过来由 Coding Agent 主动调用其他能力：

```text
Coding Agent
 ├── Code Retrieval
 ├── Knowledge Retrieval
 ├── Testing
 ├── Review
 └── Research Agent
```

------------------------------------------------------------------------

## 39.7 最终产品定位变化

因此，项目可以形成两层升级。

### 第一层：能力升级

```text
Knowledge Agent
      ↓
Task Agent
      ↓
AICoding Agent
```

解决：

> Agent 能不能真正完成任务？

### 第二层：产品形态升级

```text
单 Agent
   ↓
可配置 Agent
   ↓
Workflow
   ↓
Multi-Agent Collaboration
   ↓
Agent Platform
```

解决：

> 用户能不能创建、修改、组合和管理 Agent？

最终形成：

```text
                         Agent Platform
                               │
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
    Agent Builder          Workflow            Agent Registry
          │                    │                    │
          ↓                    ↓                    ↓
     配置 Agent          编排 Agent          管理 Agent
          │                    │
          └──────────────┬─────┘
                         ↓
                 Multi-Agent
                 Collaboration
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   Research Agent   Coding Agent    Testing Agent
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                   Task Completion
```

------------------------------------------------------------------------

## 39.8 面试时的核心表达

不要说：

> “我在原项目上增加了一个 AICoding Agent。”

更推荐说：

> **“原项目主要是一个以知识库 RAG 为核心的 Knowledge Agent。我的改进不只是增加一个 Coding Agent，而是进一步改变 Agent 的使用方式：让用户可以创建 Agent、配置 Agent、修改 Agent、编排 Workflow，并让多个 Agent 协同完成复杂任务。AICoding Agent 则作为其中一个具备实际执行能力的 Agent，可以操作代码仓库、修改代码、运行测试并根据反馈自修复。”**

最终可以浓缩成一句：

> **从“用户使用 Agent”，升级到“用户构建和编排 Agent”。**

这会比单纯增加一个 AICoding Agent 更能体现产品层面的创新。
