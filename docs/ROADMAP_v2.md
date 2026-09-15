# AI Coding Agent 魔改总路线（LangGraph 深入学习版）

> 基于 `JoshuaC215/agent-service-toolkit` 的现有魔改项目继续推进。\
> 本文档用于把当前项目与三个参考仓库对照，明确：**看什么、抄什么、不抄什么、移植到哪里、先做什么、每一步如何验收**。\
> 更新时间：2026-09-15

------------------------------------------------------------------------

# 0. 当前项目基线

## 0.1 原始项目

主项目：

-   `JoshuaC215/agent-service-toolkit`
-   自己的 fork：`qr7896/agent-service-toolkit`

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

  -----------------------------------------------------------------------------------------------------------------------------------
  参考仓库                                   主要学习什么                                                   在你的项目中的定位
  ------------------------------------------ -------------------------------------------------------------- -------------------------
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

-   Planning / investigation
-   isolated sandbox
-   code modification
-   validation
-   PR delivery
-   reviewer
-   analyzer
-   chat
-   scheduler
-   subagents
-   middleware
-   repository instructions
-   GitHub / Slack / Linear 等触发入口

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
  ----------------- ---------------------- --------------------------------------------
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
  -------------- ------------------ ---------------------
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

### 第一版

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

  ----------------------------------------------------------------------------
  你的文件             Open SWE            mini-code-agent   self-improving
  -------------------- ------------------- ----------------- -----------------
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
  ----------------------------------------------------------------------------

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
  ------ ---------------------- -------------------- ------------------------ ----------
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

### Baseline

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

-   Open SWE: `https://github.com/langchain-ai/open-swe`
-   Open SWE Customization:
    `https://github.com/langchain-ai/open-swe/blob/main/docs/CUSTOMIZATION.md`
-   mini-code-agent-langgraph:
    `https://github.com/wusuiling-if/mini-code-agent-langgraph`
-   self-improving-code-agent:
    `https://github.com/IoanRoume/self-improving-code-agent`

本文中的参考仓库能力判断以 2026-09-15
检索到的仓库内容为准；这些项目仍在变化，因此真正开始移植某个模块时，应再次查看对应仓库当前版本源码。
