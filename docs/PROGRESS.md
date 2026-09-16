# AI Coding Agent 改造日志

> 基于 [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit) 的魔改项目
> 我的 fork：<https://github.com/qr7896/agent-service-toolkit>
> 最后更新：2026-09-15

---

## 0. 一句话现状

原项目（一个 LangGraph + FastAPI + Streamlit 的通用 Agent 服务骨架）已经在本地跑通，并且完成了两处真正的改造：**把 RAG 的向量模型从 OpenAI 换成完全本地的 BGE-M3**，以及**新增一个能自己查看代码仓库并给出带行号答案的 Coding Agent**。代码已推送到自己的 GitHub fork，历史干净（3 个提交）。

改造路线已升级到 **v5**（完整版见 [ROADMAP_v5.md](./ROADMAP_v5.md)；v3 见 [ROADMAP_v3.md](./ROADMAP_v3.md)，v2 见 [ROADMAP_v2.md](./ROADMAP_v2.md)）。v5 在原 21 个阶段（0–20）之外新增两个方向（详见 §3.7）：

1. **从 Knowledge Agent 到可编排 Agent 平台**：Agent Builder / 可配置 Agent / Workflow 编排 / Multi-Agent 协同；
2. **Cost-Aware Adaptive Model Routing**：Local 7B + Cheap API + Strong API + Failure Router + Budget-aware State。

**路线图全部阶段已完成**（v5 §40.6 要求顺序不跳步）：阶段 6 `search_code` 9/9（对照实验：工具调用 12→7、读取文件 9→4），阶段 7 `write_file` / `edit_file` 11/11，阶段 8 `git_diff` 8/8，阶段 9 Planning 10/10，阶段 10 `run_tests` 9/9，阶段 11 自修复闭环 11/11，阶段 12 Reviewer 8/8，阶段 13 HITL 8/8，阶段 14 Trajectory 7/7，阶段 15 Experience Memory 11/11，阶段 16 Experience Retrieval 11/11，阶段 17 Experience-Guided Self-Correction 7/7，阶段 18 Benchmark 已跑通（n=3，结论见 §4.19），阶段 19 Sandbox 8/8，阶段 20 容器化静态验收 11/11（镜像构建未验证，见 §4.21），阶段 21 基础成本控制 10/10（§4.22），阶段 22 可配置 Agent 9/9（§4.23）+ 工作流编排 10/10（§4.24）+ 并行 / 路由 / Builder 14/14（§4.25）。参考仓库分工见 §3.3，每阶段过关题见 §3.4，可靠性原则与测试体系见 §3.6。

---

## 1. 原始项目信息

### 1.1 项目是什么

`agent-service-toolkit`（MIT 协议）是一套用于运行 AI Agent 服务的完整框架，把"前端 UI、HTTP 接口、Agent 编排、模型接入、工具调用、记忆存储"全部串好，可以直接当底座做二次开发。

| 能力 | 说明 |
|---|---|
| Agent 编排 | LangGraph 1.x：`StateGraph`、`ToolNode`、条件边、`interrupt()`（Human-in-the-loop）、`Store`（长期记忆） |
| 服务层 | FastAPI，提供 `/invoke`、`/stream`（SSE）、`/history`、`/threads`、`/feedback`、`/info`、`/health`，另有 AG-UI 协议端点 |
| 前端 | Streamlit 聊天界面，支持切换 Agent、切换模型、流式输出、历史会话、反馈 |
| 记忆 | SQLite / PostgreSQL / MongoDB 三种 checkpointer（短期记忆）+ store（长期记忆） |
| 检索 | Chroma 向量库 + `langchain-chroma`，示例是"企业手册问答" |
| 工程化 | Docker、compose、pytest 测试、CI、LangSmith / Langfuse 追踪 |

**环境要求**：Python `>=3.12,<3.15`；依赖含 `langchain 1.3.x`、`langgraph 1.2.x`、`fastapi 0.139`、`streamlit 1.59`。

### 1.2 目录结构

```
project20260827/
├── src/
│   ├── agents/          # 所有 Agent 与工具（rag_assistant.py、tools.py、agents.py 注册表…）
│   ├── client/          # Python 客户端 AgentClient（前端用它调服务）
│   ├── core/            # settings（配置）与 llm（各厂商模型工厂）
│   ├── schema/          # 数据模型（消息、请求响应体、模型枚举）
│   ├── service/         # FastAPI 服务（service.py、agui.py、threads.py）
│   ├── memory/          # checkpointer / store 初始化
│   ├── run_service.py   # 服务启动入口
│   ├── run_client.py    # 客户端示例
│   └── streamlit_app.py # 前端
├── scripts/             # create_chroma_db.py 等工具脚本
├── data/                # 知识库原始文档（AcmeTech_Employee_Handbook.pdf）
├── tests/  docs/  docker/  compose.yaml  pyproject.toml  uv.lock
```

### 1.3 请求链路（Day 1 的核心认知）

```
用户在 Streamlit 输入
        ↓
AgentClient（client.py，Python 客户端）
        ↓  POST /{agent}/stream 或 /invoke
FastAPI（service.py）
        ↓  _handle_input() 组装 thread_id / user_id / model → get_agent()
Agent 注册表（agents.py 里的 dict）
        ↓  取出已编译的图（如 rag_assistant）
LangGraph 图执行
        ↓
guard_input（安全检查）→ model（LLM 决定要不要调工具）
        ↓  需要工具 ↓        ↓ 不需要
     tools 节点        END
        ↓  工具结果回 model（循环）
        ↓
SSE 流式返回 → Streamlit 逐字显示
```

### 1.4 rag_assistant 的图结构（读源码得到）

| 元素 | 代码位置 | 作用 |
|---|---|---|
| `AgentState` | `src/agents/rag_assistant.py:20` | 状态背包：`messages` + `safety` + `remaining_steps` |
| 建图 / 4 个节点 | `rag_assistant.py:96-101` | `model`、`tools`、`guard_input`、`block_unsafe_content` |
| `check_safety` 条件边 | `rag_assistant.py:105-116` | unsafe → 拦截；safe → model |
| `pending_tool_calls` 条件边 | `rag_assistant.py:126-135` | 有 tool_calls → tools；否则 END |
| 固定边 `tools → model` | `rag_assistant.py:122` | 工具执行完必须回到模型，形成循环 |
| `compile()` | `rag_assistant.py:137` | 编译成可执行的图 |

---

## 2. 本地环境与运行方式

### 2.1 环境

| 项目 | 状态 |
|---|---|
| Python | 3.12（系统 Python）+ 仓库内 `.venv` |
| uv | ❌ 不在 PATH（见 §6 的依赖管理提醒） |
| pip | venv 原本没有，用 `ensurepip` 装回 |
| Git | 2.53（Windows），凭据管理器 GCM 2.7.3 |
| 模型 Key | DeepSeek（聊天）+ 本地 BGE-M3（向量，无需 Key） |

`.env`（被 git 忽略，不进版本库）：

```
DEEPSEEK_API_KEY=...
DEFAULT_MODEL=deepseek-v4-flash
AGENT_URL=http://localhost:8080
EMBEDDING_MODEL_PATH=D:/codex/working/models/bge-m3
NO_PROXY=...            # 让本机请求绕过系统代理
```

### 2.2 启动方式（关键：工作目录必须是 `src`）

```powershell
# 1) 服务（必须用官方入口 run_service.py：它负责 load_dotenv + Windows 事件循环策略）
Start-Process .venv\Scripts\python.exe -ArgumentList 'run_service.py' `
  -WorkingDirectory 'D:\codex\working\project20260827\src' -WindowStyle Hidden `
  -RedirectStandardOutput 'D:\codex\working\logs\service.out.log' `
  -RedirectStandardError  'D:\codex\working\logs\service.err.log'

# 2) 前端
Start-Process .venv\Scripts\python.exe -ArgumentList '-m','streamlit','run','streamlit_app.py' `
  -WorkingDirectory 'D:\codex\working\project20260827\src' -WindowStyle Hidden `
  -RedirectStandardOutput 'D:\codex\working\logs\streamlit.out.log' `
  -RedirectStandardError  'D:\codex\working\logs\streamlit.err.log'

# 3) 关闭
Get-NetTCPConnection -State Listen | Where-Object LocalPort -in 8080,8501 |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

**为什么要强调工作目录**：项目里 Chroma 用的是相对路径 `./chroma_db`，SQLite 记忆库是 `checkpoints.db`，两者都相对于进程的当前目录。站在 `src` 启动，数据就落在 `src/chroma_db` 和 `src/checkpoints.db`。

- 服务：<http://localhost:8080>（`/health` 可探活）
- 前端：<http://localhost:8501>
- 启动会预热 BGE-M3（首次约 30–60 秒），完成后才会响应请求
- 日志：`D:\codex\working\logs\`

---

## 3. 改造目标：AI Coding Agent 路线

### 3.1 为什么选这条路线

原项目自带的能力（工具调用循环、向量检索、`interrupt`、SSE、记忆）恰好是 Coding Agent 需要的全部基础设施。改造的核心思路只有一句话：

> **把"知识库"从企业 PDF 手册换成"代码仓库"，把"回答问题"升级成"动手改代码"。**

### 3.2 阶段表（对齐 v5 路线，共 23 个阶段）

> 完整版见 [ROADMAP_v5.md](./ROADMAP_v5.md)（v5 = v3 + 成本感知模型路由 + 可编排 Agent 平台）；[ROADMAP_v3.md](./ROADMAP_v3.md)、[ROADMAP_v2.md](./ROADMAP_v2.md) 保留为历史对照。

| 阶段 | 功能 | 主要文件 | 学习重点 | 状态 |
|---|---|---|---|---|
| 0 | 原项目运行 | 全项目 | Service 架构 | ✅ |
| 1 | LangGraph 迷你图 | `lg_practice/` | State / Node / Edge | ✅ |
| 2 | 原始 RAG | `src/agents/tools.py` | Retriever | ✅ |
| 3 | 本地 BGE-M3 | `src/agents/tools.py` | Embedding | ✅ |
| 4 | `list_files` / `read_file` | `src/agents/code_tools.py` | Tool Calling | ✅ |
| 5 | Coding Agent | `src/agents/coding_agent.py` | Agent Loop | ✅ |
| 6 | **`search_code`** | `src/agents/code_tools.py` | **Code Retrieval** | **✅ 验收 9/9** |
| 7 | `write_file` / `edit_file` | `src/agents/code_tools.py` | Code Editing | ✅ 验收 11/11 |
| 8 | `git_diff` / patch | `src/agents/code_tools.py` | Patch | ✅ 验收 8/8 |
| 9 | Planning | `src/agents/coding_planner.py` | Graph Routing | ✅ 验收 10/10 |
| 10 | `run_tests` | `src/agents/test_tools.py` | Execution | ✅ 验收 9/9 |
| 11 | Debug Loop | `src/agents/coding_agent.py` | Conditional Loop | ✅ 验收 11/11 |
| 12 | Reviewer | `src/agents/reviewer.py` | Subgraph / Agent | ✅ 验收 8/8 |
| 13 | HITL | Graph | `interrupt()` | ✅ 验收 8/8 |
| 14 | Trajectory | `src/agents/trajectory.py` | Evaluation | ✅ 验收 7/7 |
| 15 | Experience Memory | `src/agents/experience.py` | Store | ✅ 验收 11/11 |
| 16 | Experience Retrieval | `src/agents/coding_memory.py` | RAG + Memory | ✅ 验收 11/11 |
| 17 | Self-Correction | Graph | Experience-guided loop | ✅ 验收 7/7 |
| 18 | Benchmark | `evals/` | Agent Evaluation | ✅ 已跑通（n=3） |
| 19 | Sandbox | `src/agents/workspace.py` | 安全执行 | ✅ 验收 8/8 |
| 20 | Docker | `docker/Dockerfile.service.local` + compose 覆盖层 | 工程化 | ✅ 静态 11/11（构建未验证） |
| 21 | Model Routing（成本感知） | `src/agents/model_router.py` | Cost-Aware Routing | ⏳ **v5 新增** |
| 22 | Agent 平台（Builder / 编排） | Agent 配置 + 服务层 + 前端 | Platform / Multi-Agent | ⏳ **v5 新增** |

### 3.3 三个参考仓库的分工（学什么 / 不学什么）

| 参考仓库 | 定位 | 学什么 | 明确不做 |
|---|---|---|---|
| [langchain-ai/open-swe](https://github.com/langchain-ai/open-swe) | **架构参考** | Agent assembly（model + prompt + tools + backend + middleware）、精选工具集、Prompt / Context engineering、Planning、Reviewer、Sandbox 思路 | 不整仓复制；不接 GitHub App / Slack / Linear；不做 Dashboard |
| [wusuiling-if/mini-code-agent-langgraph](https://github.com/wusuiling-if/mini-code-agent-langgraph) | **最适合局部重写** | Agent Loop、Executor、**Verification**（把验证结果绑定到具体 workspace 状态）、Trajectory、Memory store | 完整 Sandbox、HMAC receipt、完整 CLI、并发 Locking 暂不做 |
| [IoanRoume/self-improving-code-agent](https://github.com/IoanRoume/self-improving-code-agent) | **自进化创新参考** | Critic → Score → Retry → Memory 的循环设计 | 不做 QLoRA / KTO 微调；不宣称"Agent 自己训练自己" |

**核心原则**：参考的是**结构、State 字段设计、节点划分、条件边逻辑、返回结构**，不复制整套 runtime。每引入一个机制都要走完整流程：看源码 → 画 Graph → 解释 State → 自己重写 → 跑测试 → 制造一个失败案例 → 解释为什么失败 → 修复 → 写进 Git commit。

本项目把"自进化"定义为 **Experience-Guided Self-Correction（经验引导的自修复）**：把历史任务的成功/失败、错误原因、修复方式、验证结果存成结构化 Experience，在后续相似任务中检索复用，而**不是**去训练模型。

### 3.4 每阶段的过关题（答不出来就不进入下一阶段）

| 阶段 | 过关题 |
|---|---|
| search_code | `search_code` 为什么比 `list_files + read_file` 更适合 Coding Agent？ |
| Edit | 为什么 `edit_file` 比直接让 LLM 重写整个文件更安全？ |
| Planning | Planner 的输出为什么应该进入 State，而不是只打印给用户？ |
| Test | 测试结果如何重新进入 LangGraph State？ |
| Debug | Graph 如何判断 PASS / FAIL 并决定 END 还是回到 Coder？ |
| Memory | Experience 为什么不能只是聊天历史？ |
| Self-Improving | 你的 Agent 到底"进化"了什么——是模型参数变了，还是决策过程利用了历史经验？ |

### 3.5 能力分级（自评标准）

| 等级 | 含义 | 目前所处 |
|---|---|---|
| L1 看懂 | 别人写的代码我能解释 | — |
| L2 改动 | 按要求能改 | — |
| **L3 独立实现** | 需求 → 自己设计 → 自己写出来 | **当前目标**（LangGraph 已达） |
| L4 解释设计 | 能讲清 trade-off、评测与优化方向 | 长期目标 |

### 3.6 v3 新增：可靠性原则与测试体系

> 完整内容见 [ROADMAP_v3.md](./ROADMAP_v3.md)（十大顾虑 + 五层测试体系 + 自进化五层 + A/B 实验设计）。

**一句话总纲：不要让模型承担所有可靠性。**

| 角色 | 负责什么 |
|---|---|
| LLM | 理解 / 推理 / 规划 / 生成 / Debug |
| Tools | 操作真实世界（读文件、搜代码、改代码、跑命令） |
| Code Retrieval / RAG | 提供事实与上下文 |
| LangGraph | 状态与 Workflow（谁先做、失败往哪走、什么时候停） |
| Compiler / Test / Lint / CI | **验证事实**（编译、测试、类型、风格） |
| HITL / Permission | 风险控制（高风险动作先批准） |
| Experience Memory | 沉淀历史经验 |
| Evaluation | 证明系统是否真的变好 |

> 关键原则：**LLM 负责提出方案，确定性系统负责验证事实。** 不接受"我检查过了，应该没问题"这种自证。

**十大顾虑与应对（v3 §20–29）**

| 顾虑 | 应对设计 |
|---|---|
| 会不会只是"套了一个 Agent 壳" | 把 Coding 做成闭环：需求 → 检索 → 规划 → 修改 → 运行 → 测试 → 错误分析 → 自修复 → 复审 → 评测（衡量的是任务完成率，不是"生成的代码看起来不错"） |
| Code Repository 与 RAG 会不会重复 | 定位不同：**Code = "代码现在是什么样"（Implementation Ground Truth）**；**RAG = "应该怎么做"（规范 / 经验的 Knowledge Ground Truth）**。例：Code 找到 `retryPayment()`，RAG 给出"支付最多重试 3 次" |
| Agent 自己的代码与用户代码库是什么关系 | 必须有 Workspace Root / Path Validation / Permission Boundary。测试方式：让它改 `demo_project/login.py`，看它会不会误改 `coding_agent.py` |
| 为什么不直接用现成 Codex | 目标不是造更强的模型，而是学"把 Coding 模型放进可控、可验证、可扩展的 Agent 系统"；企业要控制的是代码、知识、权限、Workflow、CI、数据 |
| AICoding Agent 到底该做什么 | 六类任务：新功能 / Bug 修复 / 自动测试 / 重构 / Code Review / 研发流程自动化。**当前仍按顺序只做前几步** |
| 如何做到"准确" | 用 Compiler / Type Check / Lint / Unit + Integration Test / Security Scan / CI 代替模型自证 |
| 如何实现真正的自纠错 | 把 Generate → Execute → Observe → Reflect → Fix 显式建模成节点与条件边；State 逐步承载 `test_result` / `error` / `iteration` |
| 换个"很笨"的本地模型会不会失效 | 系统 = LLM + Retriever + Tools + Workflow + Test + Verification + Memory，弱模型只削弱理解 / 规划 / Debug，不摧毁确定性部分 |
| 不同模型能力不同怎么办 | Model Routing + 角色分工：强模型负责规划与 Review，本地模型干具体编码 |
| 怎么证明 Agent"真的进化"了 | 建立 Evaluation：Task → Trajectory → Evaluation → Experience，并用同一批任务做 A/B |

**五层测试体系（v3 §30）**

| Level | 测什么 | 回答的问题 |
|---|---|---|
| L1 代码正确性 | Compile / Type Check / Lint / Unit / Integration Test | 代码能不能跑？ |
| L2 功能正确性 | 输入输出对照（Input 100 → Expected 200） | 功能对不对？ |
| L3 任务完成率 | 批量真实任务的通过比例 | 成功率多高？（最核心指标） |
| L4 Agent 行为质量 | Tool Call 次数、重复搜索、无效修改、死循环、改错文件 | Agent 工作效率如何？ |
| L5 企业级安全 | 权限、敏感数据、越权访问、危险命令 | 是否安全可控？ |

**测试体系建设顺序（v3 §31）**：Tool Test → Node Test → Graph Test → 真实 Coding Task（20~50 个）→ Regression Benchmark。
本项目当前处于 **Stage 1（Tool Test）**：对 `list_files` / `read_file` / `search_code` 分别测正常输入、空输入、不存在文件、不存在关键词、超长输出、路径越界、编码异常——这正是 `lg_practice/day3_*_check.py` 与 `day5_*_check.py` 在做的事。

**"自进化"分五层，别一上来就微调（v3 §33）**：Prompt → Workflow → Tool → Knowledge/Experience → Model。
本项目只做前四层，**明确不做 QLoRA / KTO**。

**验证自进化有效性的 A/B 设计（v3 §32）**

| 指标 | Baseline（Agent + Retrieval + Tools + Test） | Improved（+ Experience Retrieval） |
|---|---|---|
| Task Success Rate | 待实验 | 待实验 |
| First-Try Success Rate | 待实验 | 待实验 |
| Average Attempts | 待实验 | 待实验 |
| Average Tool Calls | 待实验 | 待实验 |
| Test Pass Rate | 待实验 | 待实验 |
| Human Intervention | 待实验 | 待实验 |
| Token Cost / Task Time | 待实验 | 待实验 |

> 数字必须真实跑出来，不能提前编。只有当 Experience Memory 让"成功率↑、平均尝试次数↓、人工干预↓"时，才能说"经验引导的自修复有效"。

**可靠性自检七问（v3 §35，每加一个功能都过一遍）**

1. 能不能验证（有没有确定性测试）？
2. 失败怎么办（有没有 Error → Debug → Retry）？
3. 改错了怎么办（有没有 Diff / Rollback / HITL）？
4. Agent 会不会乱改（有没有 Workspace / Path Boundary）？
5. 换模型还能不能工作（Workflow / Tools / Verification 是否独立于模型）？
6. 怎么证明变好了（有没有 Benchmark / Baseline / A-B）？
7. 经验有没有真正起作用（有没有减少重复错误、提高成功率）？

### 3.7 v5 新增：两个方向（先做准备，不改变当前实现顺序）

> 完整内容见 [ROADMAP_v5.md](./ROADMAP_v5.md)：§40（成本感知模型路由）与最后一章（从 Knowledge Agent 到可编排 Agent 平台）。
> **v5 §40.6 明确：这两个方向不改变当前实现顺序**——先把 Coding Agent / Verification / Evaluation 做扎实，最后才做路由与平台化。

#### 方向一：从 Knowledge Agent 到可编排 Agent 平台

**现状（这也是我们要解决的缺口）**：原项目（含目前的改造）**只能通过改代码来新增 Agent**——`src/agents/agents.py` 是一个硬编码字典，每个 Agent 都是一个 Python 模块。所以用户只能"使用"已有 Agent，不能"创建 / 配置 / 编排"Agent。

| 层次 | 原来 | v5 目标 |
|---|---|---|
| 能力升级 | Knowledge Agent（RAG 回答） | Task Agent → **AICoding Agent**（真正执行任务） |
| 产品形态升级 | 单个固定 Agent | 可配置 Agent → Workflow → **Multi-Agent 协同** → Agent Platform |
| 用户角色 | 使用 Agent | **创建、配置、修改、编排** Agent |

对本项目架构的三点含义：

1. Agent 要逐渐从"硬编码模块"变成"**可配置的数据**"：Prompt / Model / Knowledge / Tools / Skills / Workflow 都能被配置——这是 Agent Builder 的前置条件；
2. AICoding Agent 的定位要从"新增的一个 Agent"变成"**一种可被其他 Agent 调用的执行能力**"（与上游已有的 Agent Registry + AG-UI 设计天然吻合）；
3. 面试表达（v5 §39.8）：**从"用户使用 Agent"升级到"用户构建和编排 Agent"**。

#### 方向二：Cost-Aware Adaptive Model Routing（成本感知自适应模型路由）

核心原则：**高能力模型负责高价值决策，低成本模型负责高频执行；确定性工具负责验证事实。**

| 模型层 | 职责 |
|---|---|
| Local 7B | 代码摘要、错误分类、检索结果重排、简单修改 / Debug、测试生成 |
| Cheap API | 常规 Coding、普通 Debug |
| Strong API | 任务拆解、复杂规划、架构决策、复杂 Debug、最终 Review |
| Deterministic Tools | Test / Compile / Lint / Type Check（**不交给 LLM 猜**） |

三条具体机制（v5 §40.3）：

1. **先检索再上强模型**：`search_code` → 符号 / 依赖过滤 → Local 重排 → Top-K → 才交给 Strong API（禁止默认把整个仓库塞给强模型）；
2. **Failure Router**：测试失败先分类（语法/类型 → Local；普通业务 → Cheap；架构/依赖 → Strong），并规定升级链 `Local → Cheap → Strong`；
3. **Budget-aware State**：State 增加 `llm_calls` / `estimated_tokens` / `budget` / `model_tier`，路由按剩余预算决定是否升级。

**必须用实验证明**（v5 §40.5）：同一批 20–50 个任务，比较 Baseline（全用 Strong）与 Adaptive（三层路由）的 Task Success Rate / First-Try Success Rate / Average Attempts / Tool Calls / **Tokens** / **API Cost** / Time / Human Intervention。目标不是"省 token"，而是"**成功率接近 + 成本明显更低**"。

**工程提醒**（v5 §40.4）：网页端 AI 不适合作为 Agent 后端（不可编程、不可计量、不可审计、不可路由）；后端链路要用可编程 API 或本地模型——这会影响我们后续的模型接入选择。

---

## 4. 已完成的工作

### 4.1 Day 1：跑通项目 + 追踪第一条请求

- 启动 FastAPI（8080）与 Streamlit（8501），实测普通聊天与知识库问答
- 定位并逐行读完 8 个核心文件：`pyproject.toml`、`run_service.py`、`agents.py`、`chatbot.py`、`rag_assistant.py`、`tools.py`、`service.py`、`client.py`
- 画出（并核对）请求链路图与 `rag_assistant` 图
- **过关验证**：能从记忆里复述请求链路（Streamlit → AgentClient → FastAPI → 注册表 → guard_input → model → tools → model → SSE），并说明"为什么 UI 不直接调 Agent"（分层解耦，任何客户端只需对接同一套 HTTP 接口）

### 4.2 关卡：LangGraph 三件套（练习成果）

在 `lg_practice/` 下亲手写了两个迷你图，把"看懂"变成"能写"：

| 文件 | 内容 | 对应原项目 |
|---|---|---|
| `day2_mini_graph.py` | 用字符串消息跑通 `model ↔ tool` 循环 | `rag_assistant.py` 的骨架 |
| `day2_mini_graph_v2.py` | 换成**结构化消息**（`AIMessage.tool_calls` / `ToolMessage` + `tool_call_id`）+ 官方 `ToolNode` | 与真实项目同构 |

关键认知：

- **State** 是全图共享的背包；节点只返回自己改的那一格（`{"messages": [msg]}`），`add_messages` 负责"追加"
- **条件边**只读不写；真实项目用结构化字段 `last_message.tool_calls` 判断，而不是文本约定
- **`tool_call_id` 是配对凭证**：AI 消息说"调 abc123"，工具结果必须带 `abc123` 回来
- **循环有边界**：工具节点若不产生新消息会死循环（LangGraph 默认 `recursion_limit=25` 兜底；原项目用 `RemainingSteps` 管预算）
- 模型自己"看不见"任何东西，是 `model` 节点每次把 SystemPrompt + 全部 `messages` 重新发过去

### 4.3 关卡：原始 RAG 实证（练习成果）

`day2_retrieval_probe.py` 直接调用项目真实的 Chroma 库，打印 Top-K 原文与相似度分数，对比三种问法：

| 问法 | rank1 分数 | 前三名顺序（p.0/p.1/p.2 是手册的分块） |
|---|---|---|
| `How many vacation days do employees receive?` | 0.4437 | p.1 → p.0 → p.2 |
| `我一年能休几天假？` | 0.4008 | p.1 → p.2 → p.0（后两名互换） |
| `What's the policy on time off?` | 0.4758 | p.1 → p.0 → p.2 |

实验结论（直接回答了"用户换一种说法怎么办"）：

1. **语料太小会让 Top-K 失效**：手册 PDF 只有 3 个 chunk，`k=5` 退化成"全给"，看不出检索失败
2. **切片粒度决定精度**：`chunk_size=2000 / overlap=500` 把远程办公、行为准则、休假政策混进同一块，rank1 预览看着"答非所问"，其实答案就埋在同一块后半段
3. **说法影响排序**：同一件事换个说法，分数和排名都会漂移
4. **原项目丢掉了可溯源信息**：`format_contexts()` 只拼 `page_content`，文件名、页码、分数全丢，所以模型无法给出引用

Chroma 一条记录 = `ids` + `embeddings` + `documents` + `metadatas`（分数是查询时算出来的，不存储）。

### 4.4 魔改一：本地 BGE-M3 替换 OpenAI Embeddings

**问题**：原项目 `tools.py` 写死 `OpenAIEmbeddings()`，没有 OpenAI Key 就检索不了——知识库问答直接 500。而 DeepSeek 官方没有可用的 Embedding 接口。

**方案对比**：先试轻量的 fastembed（ONNX），发现 0.8.0 的 `TextEmbedding` 已不支持 `BAAI/bge-m3`；最终选择官方推荐的 **sentence-transformers + BAAI/bge-m3**。

**改动**（commit `5224586`）：

| 文件 | 改动 |
|---|---|
| `src/agents/tools.py` | 新增 `get_embeddings()`（本地 BGE-M3，路径读 `EMBEDDING_MODEL_PATH`，`lru_cache` 缓存）；新增 `get_chroma_retriever()`（进程内单例 + 创建失败重试 3 次）；模块导入时 `load_dotenv()` 兜底 |
| `src/service/service.py` | 启动时预热 Chroma 检索器，避免"第一个请求必失败" |
| `scripts/create_chroma_db.py` | 灌库改用同一套本地 embeddings；支持 `CHROMA_DATA_DIR` / `CHROMA_DB_DIR`；修掉失效的 `langchain.text_splitter` import |

**模型**：`BAAI/bge-m3` 下载到 `D:\codex\working\models\bge-m3`，`pytorch_model.bin` 2165.9 MB，SHA256 与官方一致（下载过程见 §6）。

**灌库结果**：`src/chroma_db`（3 个 chunk）。验证：问"年假多少天"，回答 `15 days of Paid Time Off (PTO) per year`，连续多次稳定。

### 4.5 魔改二：Codebase Understanding + Coding Tools

这是第一个真正面向 AI Coding 的功能：让 Agent 学会"看"代码仓库。

**新增 `src/agents/code_tools.py`**（commit `4d70371`，111 行）——两条工具 + 三条设计原则：

| 工具 | 作用 | 设计约束 |
|---|---|---|
| `list_files(pattern, max_files)` | 列出仓库文件（跳过 `.git`/`.venv`/`__pycache__` 等噪音） | 路径限制在项目内；输出有上限 |
| `read_file(path, start_line, max_lines)` | 带行号读文件的一段 | 越权路径直接拒绝；不存在的文件/目录**优雅返回 `ERROR:`**，不抛异常炸图 |

设计原则：**① 限制在项目根目录内（安全边界）② 返回值必须带坐标（路径 + 行号）③ 输出必须有上限**，外加"工具要优雅失败"。

**验收脚本 `lg_practice/day3_code_tools_check.py`** 检查 6 项（能列文件 / 跳过噪音 / 遵守上限 / 带行号读文件 / 拒绝越权路径 / 不存在的文件优雅失败）→ **6/6 通过**。

**新增 `src/agents/coding_agent.py`** —— 与原 `rag_assistant` 同构的异步图（`model ↔ tools` 循环 + 一条条件边），两点关键差异：

1. 节点用 `async def` + `await model.ainvoke(...)`，不阻塞服务事件循环
2. 模型从 `config["configurable"].get("model", settings.DEFAULT_MODEL)` 取，支持前端切换模型

提示词要求：**先查再答、结论必须来自读到的文件、回答必须给"文件路径 + 行号"**。

**注册**：`src/agents/agents.py` 里加入 `"coding-agent"`（注册表从 10 个 Agent 变 11 个）。

**实测（服务端 `/coding-agent/invoke`）**：

- 问题："这个项目的 FastAPI 服务入口在哪里？它做了什么？" → 它依次调用 `list_files` → 并行 `read_file` → 用 `start_line` 翻页读了 5 个文件，最后给出带行号的答案；抽查 4 处引用（`run_service.py:31-37`、`service.py:131`、`service/__init__.py:1`、`agui.py:31`）全部准确
- 问题："AgentClient 是在哪里定义的？它负责做什么？" → 引用 `src/client/client.py:25` 等位置，抽查同样全部准确

### 4.6 发布：Git 历史与 GitHub

| Commit | 内容 |
|---|---|
| `5224586` | `feat(rag): use local BGE-M3 embeddings instead of OpenAI` |
| `bc18c83` | `chore: ignore local study scratch folder` |
| `4d70371` | `feat(coding-agent): add list_files/read_file tools and register the coding agent` |

发布流程里做的两件"专业动作"：

1. **先同步上游再推**：clone 时的基线是 `0c58abf`，推送时上游已到 `18d76e9`。先把上游 3 个新提交取下来，把本地 3 个提交 **rebase 到最新上游之上**（零冲突），再推 —— 保证代码不是过时快照。
2. **推送前查敏感信息**：确认提交历史里没有 API Key，`.env`、`chroma_db`、`checkpoints.db`、模型文件均被 git 忽略；仓库体积仅 1.1 MB。

Remote 配置：

```
origin   → https://github.com/qr7896/agent-service-toolkit.git      （自己的 fork）
upstream → https://github.com/JoshuaC215/agent-service-toolkit.git  （原作者）
```

---

### 4.7 魔改三：`search_code`（阶段 6 / Code Retrieval）

让 Agent 从"挨个翻文件"变成"先定位，再精读"。实现要点（`src/agents/code_tools.py`）：

- 支持关键词 / 函数名 / 类名 / 文件名搜索，输出 `路径:行号 + 命中行`
- 支持 `context_lines`（上下文行）、`case_sensitive`、`regex`、`path_glob`（限定范围）
- 预算护栏：`max_matches`（默认 50）、`max_files`（默认 200）、单文件 1 MB 上限、跳过二进制与噪音目录
- 安全与稳健：越权 `path_glob` 被拒；非法正则、读取异常都返回 `ERROR: ...` 而不炸图；0 命中明确返回 `no matches`

**验收**：`lg_practice/day5_search_code_check.py` 覆盖 9 项（搜类名 / 搜函数名 / 上限截断 / 上下文行 / 大小写 / 越权拒绝 / 非法正则 / 无命中提示 / 全仓库扫描健壮性）→ **9/9 通过**。

**对照实验**（`lg_practice/day6_search_vs_read_benchmark.py`：同模型、同提示词、同问题，唯一变量是工具集）

问题：`AgentClient 在哪里定义的？它负责做什么？`

| 指标 | Baseline（list_files + read_file） | Improved（+ search_code） |
|---|---|---|
| 耗时 | 17.1 s | 14.2 s |
| 工具调用次数 | 12（list_files ×3、read_file ×9） | 7（list_files ×1、search_code ×2、read_file ×4） |
| 读取文件数 | 9 | 4 |
| 答案带 `路径:行号` | 是 | 是 |

结论：工具调用 −42%、读取文件数 −56%、耗时 −17%，答案质量未下降。注意**耗时改善有限**——因为时间大头是 LLM 往返而不是工具执行；真正的收益是"少读文件、上下文更干净、结论可复核"。

**接入 Agent**：`coding_agent.py` 的 `TOOLS` 改为 `[search_code, read_file, list_files]`，提示词新增两条规则——"先定位、再精读"与"`no matches` 时换关键词重搜，不要盲读整个仓库"。

**过关题回答要点**（为什么 `search_code` 比 `list_files + read_file` 更适合 Coding Agent）：

1. 把"遍历"变成"定位"：线性扫描最坏要读 N 个文件，搜索一次就给出坐标
2. 定位责任从模型转移到工具：不需要模型"认出答案在哪一行"，工具直接给 `路径:行号`，可引用可复核
3. 省 token、少噪音：`read_file` 一次上百行大多无关，无关上下文越多越容易带偏模型
4. 有预算护栏：`max_matches` / `max_files` / `truncated` 防止把整个仓库塞进上下文
5. 失败模式清晰：`ERROR` / `no matches` 让模型能"缩小范围重搜"，而不是一路盲读
6. **它不是取代 `read_file`，而是重排顺序**：`search_code` 是 grep，`read_file` 是 cat——先 grep 定位，再 cat 精读

### 4.8 魔改四 / 五：安全写入 + 改动可见（阶段 7–8）

**阶段 7 `write_file` / `edit_file`（验收 11/11）**

| 设计 | 实现 | 为什么 |
|---|---|---|
| 只新建、默认不覆盖 | 已存在文件直接 `ERROR`，必须显式 `overwrite=True` | 覆盖是不可逆破坏，必须显式授权 |
| 唯一命中才修改 | 命中 0 处或多处**先 return，绝不写入** | 逼模型给出足够精确的片段，而不是赌一个位置 |
| 敏感文件边界 | `.env*` / `*.pem` / `*.key` / `*.p12` / `id_rsa*` / `.git/**` | 对应 v3 的 Permission Boundary |
| 返回坐标 | 成功返回 `rel_path:line_no` | 让后续 `git_diff` 与人工核查有落脚点 |

**阶段 8 `git_diff`（验收 8/8）**

| 设计 | 实现 |
|---|---|
| 看真实差异 | `git diff --no-color`，可选 `--cached`（暂存区）与 `-- <path>`（限定范围） |
| 看得到新文件 | `git diff` 天生看不到未跟踪文件，所以额外输出 `status:` 段（`git status --short`） |
| 输出可控 | `max_lines`（默认 400）截断并标记 `truncated` |
| 语义一致 | `staged=True` 时过滤掉未暂存条目，避免模型把"工作区改动"误读成"已暂存改动"——**这个瑕疵是接进 Agent 后由它自己暴露出来的** |
| 优雅失败 | 没装 git / 非 git 仓库 / 越权路径 → `ERROR: ...` |

**Agent 接线**：`coding_agent.py` 的 `TOOLS` 现在是 `[search_code, read_file, list_files, git_diff]`——**仍然只有只读工具**。`write_file` / `edit_file` 已实现但**故意没接**：按 v3 §13 / §37 的顺序，写权限要等 HITL（阶段 13）就位后再交出，先让 `run_tests`（阶段 10）提供"改得对不对"的确定性反馈。

**实测**：问 Agent"现在工作区有哪些改动？"，它依次调用 `git_diff({})` → `git_diff({'staged': True})` → 读两个文件核对，17 秒给出"2 个文件未暂存改动、暂存区为空"的结论。

### 4.9 魔改六：`run_tests`（阶段 10 / Test Execution）

**新增文件**：`src/agents/test_tools.py`（验收 9/9）

| 设计 | 实现 | 为什么 |
|---|---|---|
| 只跑 pytest | argv 自己拼装，`shell=False`；`path` 以 `-` 开头直接拒绝 | 不接受任意命令，也不给"选项注入"留口子 |
| 结构化结果 | 固定六字段：`command` / `exit_code` / `status` / `passed` / `summary` / `output` | 下游 Test/Debug 节点要能程序化解析，而不是读自然语言 |
| 状态可分辨 | `passed` / `failed` / `no_tests`(exit 5) / `timeout` / `error` | "没有测试可跑"不等于"测试失败" |
| traceback 保真 | 原样保留 pytest 输出（含 `文件名:行号`） | Debug 阶段必须能直接看到失败位置 |
| 超时不卡死 | `subprocess.run(timeout=...)`，到点返回 `status: timeout` | 无限等待会把整个图挂住 |
| 输出可控 | `max_lines`（默认 200）截断并标记 | 失败时 pytest 输出可能非常长 |

**验收脚本** `lg_practice/day9_run_tests_check.py` 的 9 项里包含三类真实场景：**故意失败的用例**（校验输出里有 `test_fail.py:2` 与断言信息）、**故意 sleep 10s 的用例 + timeout=5**（校验 5 秒返回 `status: timeout`，证明真的没卡死）、**空目录**（校验 `status: no_tests` / `passed: na`）。

**Agent 接线**：`TOOLS` 变为 `[search_code, read_file, list_files, git_diff, run_tests]`，提示词新增"涉及能不能跑通的问题，用 run_tests 真实执行，并按 status/summary 回答，不要用『应该没问题』这种说法"。

**实测**：问"tests/schema 这组测试现在能通过吗？"→ 15.9 秒，它调用 `run_tests(path='tests/schema')` 并给出带 `command / exit_code / status / summary` 的结论（10 passed in 6.45s）。

**阶段 7–8 过关题的回答要点（本人作答，已记录）**

1. **为什么 `edit_file` 比让 LLM 重写整个文件更安全**：全量重写等价于"改一个错别字就把整本书重印"——长文件容易被输出长度截断、模型会顺手重构无关代码（"均值回归"抹掉细节），几百行 diff 让人和 Reviewer 都分不清真实业务改动。`edit_file` 用 `old_text`/`new_text` 做**内容锚点**（不依赖脆弱的行号），匹配失败就返回结构化错误让模型自己纠错（而不是猜一个位置改），最终产出的 diff 极小、可审查、可回滚。**一句话：用确定性的工具逻辑去约束概率性的生成。**
2. **为什么改代码前必须先有"能看见改动"的机制**：Agent 的循环是"观察 → 思考 → 行动"，如果修改工具只回一句"修改成功"，Agent 就会基于错误前提继续 Test/Debug，一旦改动没生效或改错位置，后面全是猜谜；可信的 diff 是它的 **Ground Truth（单一事实来源）**。同时它也强化了"先计划后执行"——在落盘前看到 diff，等于给 Agent 与文件系统之间加了一道审批流；只有"看见"，才能真正做到"改错了能发现、能回滚"。

### 4.10 魔改七：Planning（阶段 9）

**新增文件**：`src/agents/coding_planner.py`（验收 10/10）

**三段式实现**：

| 阶段 | 做什么 | 关键约束 |
|---|---|---|
| ① recon 侦察 | 只用只读工具（`list_files` / `search_code` / `read_file` / `git_diff`），最多 3 轮 | planner 压根没绑定写工具，所以不可能"边规划边改" |
| ② plan 规划 | 把"需求 + 侦察结论"交给模型，要求输出**严格 JSON** | 四要素：`task` / `steps`(order+action+path+reason) / `verification` / `open_questions` |
| ③ validate 校验 | 用确定性代码核对计划与真实仓库 | `modify` 的文件必须存在、`create` 的文件必须不存在；不一致写进 `open_questions` |

**图结构**：`START → planner → coder → (tools → coder | END)`。`CodingState` 比 `MessagesState` 多一个 `plan` 字段；coder 每次调用都把 `plan` 作为 SystemMessage 上下文带上，并要求"要偏离计划先说明原因"——**计划只有被后续节点使用，才算真的进了控制链路**。

**踩坑（很有价值）**：原以为该用 `model.with_structured_output(Plan)`，但 DeepSeek 当前模型两条路都返回 400：

- 默认方式（`json_schema` 形式的 `response_format`）→ `This response_format type is unavailable now`
- `method="function_calling"`（强制 `tool_choice`）→ `Thinking mode does not support this tool_choice`

于是改成"JSON 提示 + 括号配平提取 + Pydantic 校验"，并把解析失败也当成可观察状态写进 `open_questions`，而不是让图崩掉。**这本身就是"LLM 提方案、确定性系统验事实"的一次实践**：模型给什么不重要，能不能被校验、被追问才重要。

**实测**（真实 LLM 运行）：

- 具体需求"给 coding agent 增加一个 planner 节点" → 4 步计划 + 3 条 verification，所有路径与仓库真实状态一致
- 含糊需求"帮我优化一下这个项目" → `open_questions` 非空，直接反问"优化指性能 / 代码质量 / 测试覆盖率 / 依赖刷新 / 功能补全？"
- 全图运行 → `state["plan"]` 存在（证明计划真的进了 State，而不是只打印）

**过关题回答要点（本人作答）**：计划只打印给用户，充其量是个"进度条"；写进 State 才是把计划变成 Agent 系统的**控制中枢**——后续节点能读它、校验它、按它执行，计划本身有问题时（文件不存在 / 已存在）还能提前暴露，而不是执行到一半才失败。

**回归测试**：改动 `code_tools` / `coding_agent` 之后重跑历史验收脚本，day5 9/9、day7 11/11、day8 8/8、day9 9/9、day10 10/10 全绿。

### 4.11 魔改八：Debug / Self-Correction（阶段 11）

**目标**：从"能改、能测"升级到"**改错了能自己修**"；这也是第一次真正开放写权限（受开关控制）。

**图结构**

```
START → planner → coder → (有 tool_calls ? tools → coder : tester/END)
                      ↑                              │
                      │                      PASS → END
                      │                      FAIL → debugger → coder
                      └───────────────       （attempts ≥ 3 → giveup → END）
```

**四个关键设计**

| 设计 | 实现 | 为什么 |
|---|---|---|
| 写权限默认关闭 | `allow_write` 从 config 传入，由 planner 节点写进 State；默认 False | 自我修复是高危能力，必须显式开启 |
| **两道闸门** | ① 不给模型绑写工具；② `tools` 节点（自实现 dispatcher，不是 `ToolNode`）再校验一次 | 只靠"没绑给模型"不够——越权调用会拿到 `ERROR: 当前模式不允许调用工具 write_file` |
| 重试上限 | `MAX_RETRIES = 3` + `attempts` 计数；`check_test` 三分支 pass / retry / giveup | 防"改→测→fail→改"死循环（v3 §23） |
| 不许假装成功 | `giveup` 输出 `[FAIL] 已尝试 3 次仍未通过…结论：本次任务没有完成` | 失败也必须是**明确、可观察**的结果 |

**为什么自己写 dispatcher 而不用 ToolNode**：工具白名单必须按运行模式**动态**决定，而 `ToolNode` 的工具列表在建图时就固定了。自己执行 `tool_call` 时再校验一次，等于加了第二道锁，而且让"越权调用"变成可测试的行为（测试项 2）。

**State 演化**：`messages` → `plan` → `test_result` → `attempts`（外加 `allow_write`），对应 v3 §18 建议的渐进式 State 设计。

**实测（真实 LLM + 真实改文件 + 真实跑测试）**

| 场景 | 结果 |
|---|---|
| 只读模式（默认）：沙箱里有 bug + 失败测试 | **文件未被修改**，也没有"测试通过"的假结论——Agent 只能给修改建议 |
| 写模式（`allow_write=True`）：同一任务 | 完整闭环：读 traceback → `edit_file` 最小修复 → 重跑测试 → `status: passed`（`attempts=1`，1 passed in 0.01s） |
| 重试上限 | `check_test` 在 `attempts ≥ 3` 时返回 `giveup`，消息明确写"本次任务没有完成" |

**验收**：`lg_practice/day11_self_correction_check.py` **11/11**（8 项确定性检查 + 图结构 + 2 次真实端到端运行）。回归：day7 11/11、day8 8/8、day10 9/10——那 1 项是 DeepSeek 流式超时（120s 无 chunk），单独复测通过（已记入 §7.2 已知问题）。

**过关题：Graph 如何判断 PASS / FAIL 并决定 END 还是回到 Coder？**

`tester` 把 pytest 的结构化结果（`status` / `exit_code` / `summary` / `output`）写进 `State.test_result`；条件边 `check_test` 是一个**只读 State 的纯函数**：`passed → END`、`failed 且 attempts < MAX_RETRIES → debugger → coder`、`failed 且 attempts ≥ MAX_RETRIES → giveup → END`。关键在于**判断依据是确定性字段，而不是模型的自述**——模型说"修好了"不算数，pytest 的退出码说了算。

### 4.12 魔改九：Reviewer（阶段 12）

**新增文件**：`src/agents/reviewer.py`（验收 8/8）

**职责边界**：Coder 负责改代码，Reviewer 负责**判断这次改动是否站得住**。Reviewer 只读——`REVIEWER_TOOLS` 里没有任何写工具。一旦它既能评审又能修改，"独立审查"就不存在了：它会倾向于替自己的改动辩护，而不是挑错。

**设计**

| 设计 | 实现 | 为什么 |
|---|---|---|
| 只读评审 | `REVIEWER_TOOLS` = git_diff / read_file / search_code / list_files / run_tests | 评审者不能同时是修改者 |
| 结构化裁决 | `{"approved", "score", "issues", "summary"}` 写进 `State.review` | 后续节点与人可程序化使用，也便于将来做评测 |
| 兜底不批准 | 解析失败 → `approved=False` + 说明 | 与 planner 同原则：宁可判"未通过"，也不默认放行 |
| 评审范围可控 | `review_path` 配置 > 计划里唯一目标文件 > 全仓库 | 真实仓库里常同时存在无关的未提交改动，全仓 diff 会误判 |
| 必须给证据 | 提示词要求 issues 引用 `文件名:行号` 或 diff 里的具体行 | 拒绝不能靠"感觉"，要能被人复核 |

**图结构**：`tester --PASS--> reviewer → END`（FAIL 仍走 `debugger → coder`）。

**实测**

| 场景 | 结果 |
|---|---|
| 正常修复（真实写模式闭环跑完） | `approved=True`，`score=1.0`，摘要指出"add 已正确返回 a + b、测试通过、改动与需求一致" |
| 改动与需求无关（diff 只有无关文件、目标文件仍是 `a - b`） | `approved=False`，issues 写明"`calc.py:2` 仍是 `return a - b`，与需求「修复 add 函数」直接矛盾" |
| 输出无法解析 | 兜底 `approved=False`（验收项 5） |

**一个很能说明设计价值的插曲**：第一次跑验收时，reviewer **拒绝了本该通过的修复**，理由是"diff 混入了与需求无关的 `coding_agent.py` / `reviewer.py` 改动"——它看到的正是我当时**未提交的本阶段代码**。这说明它确实在做独立判断而不是走形式。由此我加了"评审范围"（`review_path` / 计划单文件），让评审聚焦任务目标；同时在提示词里明确"不要因为文件是新增/未跟踪就否决"。

**过关题：为什么 Reviewer 不应该自己改代码？**

1. **独立性**：评审者一旦能改，就会为自己的方案辩护，审查退化成自我确认；
2. **可追责**：谁改的、谁批的要能分开，出问题才知道是"改错"还是"批错"；
3. **职责单一**：Coder 对"能不能跑通"负责，Reviewer 对"符不符合需求、有没有引入风险"负责；
4. **边界清晰之后才能换模型**（v3 §28 的 Model Routing）：强模型评审、本地模型编码，各司其职。

### 4.14 魔改十：Human-in-the-loop（阶段 13）

**目标**：把"写权限开关"升级成"**高风险动作先暂停、等人批准**"。

| 设计 | 实现 | 为什么 |
|---|---|---|
| 只在写操作前暂停 | `act` 节点在执行前检查本批 `tool_calls` 里是否有 `write_file` / `edit_file` | 只读动作（search / read / diff / run_tests）照常执行，体验不受影响 |
| **审批必须在副作用之前** | `interrupt()` 放在**第一遍纯判断**里，批准后才进入第二遍执行 | LangGraph 在 resume 时**从头重跑该节点**——若先执行再暂停，被批准的那批写操作会被执行两次 |
| 审批信息可决策 | payload 含：改哪个文件、`change` 预览（content 前 200 字 / old→new）、**计划里给的理由** | 人要知道"改什么、为什么"才能决定；reason 直接取自 `plan.steps` |
| 保守的判定 | `_is_approved`：只有明确同意（`True` / "批准" / "yes" / "approve"…）才算批准，**无法识别一律拒绝** | 安全默认：宁可多问一次，也不能误执行写操作 |
| 拒绝也要有结果 | 写操作被拒 → 返回 `ERROR: 用户拒绝执行这次写入…` 的 ToolMessage + State 记录 `approvals[{approved: False}]` | 让模型知道"没改"，改为给建议或询问，而不是假装改好了 |
| 开关可控 | `require_approval` 默认 **True**；自动化测试显式传 False | 生产默认安全，自动化闭环可显式关闭 |

图结构不变，只是 `act` 节点内部多了一道闸门：`coder → tools(act) → [有写操作?] → interrupt（等人批准）→ 执行 / 拒绝`。

**实测（真实 LLM + 真实文件 + `MemorySaver` checkpointer）**

| 场景 | 结果 |
|---|---|
| 写模式 + 默认审批 | 第一次 invoke **停在 `__interrupt__`**，payload 含 `path=_day13_sandbox/approve_me.txt` 与理由"…目标文件不存在，直接新建并写入单行文本 hello approval" |
| 暂停时的副作用 | **文件尚未创建**（证明审批确实在副作用之前） |
| `resume("批准")` | 文件被创建，内容正确 |
| `resume("拒绝")` | 文件**未被创建**，State 记录 `approvals=[{..., approved: False}]` |
| `require_approval=False` | 不中断，直接执行 |
| 只读模式 | 完全不触发审批 |

验收：`lg_practice/day13_hitl_check.py` **8/8**。回归：day11 11/11、day12 8/8（这两个自动化脚本现在显式传 `require_approval=False`）。

**过关题：哪些动作必须人工批准？为什么不是所有动作都批准？**

- **必须批准**：写/覆盖/删除文件、执行命令、安装依赖、`git push` 这类**有副作用且难以撤销**的动作；
- **不该批准**：search / read / diff / run_tests 这类只读或可重复执行的动作——它们没有破坏性，反复确认只会让人"闭眼批准"，HITL 反而失效；
- 判断标准可以概括成三个问题：**能不能撤销？会不会影响仓库之外？出错代价大不大？**

**工程细节**：`interrupt()` 依赖 checkpointer——服务端启动时会给注册表里的图挂上 SQLite checkpointer，验收脚本用 `MemorySaver`。

### 4.15 魔改十一：Trajectory（阶段 14）

**目标**：把每次任务的过程变成可分析的事实记录，为后续 Experience Memory 与 Evaluation 提供同一份可信输入。

图的所有收尾路径现在统一经过 `finalize_trajectory`：`reviewer → finalize_trajectory → END`、`giveup → finalize_trajectory → END`；只读任务也会收尾，因此不会只记录“成功案例”。每条 JSONL 记录含任务、计划、实际工具调用与计数、改动文件、测试轮数与结果、评审、审批、模型、耗时和最终状态。默认写入 `.codex/trajectories/coding_agent.jsonl`，该目录已加入 `.gitignore`；可用 `configurable.trajectory_path` 改为任意本地位置。

**安全边界**：工具参数只保存键名而非值（避免把写入内容塞进遥测）；字段名含 `api_key`、`secret`、`token`、`password` 或 `authorization` 的值会递归脱敏。记录失败不会篡改已经完成的任务结果，而是在 State 中标出 `persistence_error`。

**指标脚本**：`scripts/trajectory_metrics.py [--path <JSONL>]` 输出任务数、成功率、平均 attempts、平均工具调用数与平均耗时。验收 `lg_practice/day14_trajectory_check.py` **7/7**：成功持久化、字段完整、工具/改动/审批可追溯、脱敏、失败路径、聚合、图收口均通过。

**过关题：为什么 trajectory 是 evaluation 与 experience 的共同前置？** Evaluation 需要同口径的任务结果、耗时、尝试数和成功率，才能比较基线与改进；Experience 需要知道“哪种任务在哪一步失败、怎样修复后成功”，才能提炼而不是凭印象编造经验。Trajectory 正是两者共享的原始证据。

### 4.16 魔改十二：Experience Memory（阶段 15）

**目标**：把一次任务的轨迹沉淀成可审计的本地经验，为后续检索（阶段 16）与经验驱动的自修复（阶段 17）提供事实来源。

**派生规则**：经验只从 `trajectory` 派生，不采信模型自述。`succeeded → accepted`；失败按优先级分类为 `approval_denied`（人工拒绝）> `test_failed`（测试未过）> `review_rejected`（评审否决）> `unknown_failure`。`completed_read_only` 不入库——只读问答没有可复用的修复信号，进库只会污染后续检索。这一条在真实数据上验证过：本机唯一一条真实轨迹是只读问答，灌库结果是 `experiences_written: 0`。

**存储**：SQLite（`src/agents/experience.py`），默认 `.codex/experience/experience.db`。字段含 `trajectory_id`（唯一索引）、任务、`task_key`（小写分词特征）、outcome、failure_type、effective_steps、tools_used、changed_paths、attempts、test_summary、review_summary、approved、model、耗时。同一 `trajectory_id` 重复写入走 `ON CONFLICT DO UPDATE`，不会产生重复经验。

**两层安全边界**：① 经验只做白名单摘取（如计划步骤只取 `order/action/path`），不整份复制轨迹，轨迹里的 `api_key` 等字段没有机会进库；② 文本字段再过一遍 `redact`。密钥不落盘这条由验收脚本直接扫描数据库文件字节来证明。

**接线**：`finalize_trajectory` 默认顺带沉淀经验（`record_experience: False` 可关）。经验写入失败只记 `experience_error`，不会把一次已完成的任务变成失败任务。

**召回（阶段 16 的骨架）**：`ExperienceStore.recall()` 用 `task_key` 的确定性关键词重叠排序，空库、无重叠、任务键为空都返回空列表且不抛异常。向量检索留到阶段 16 接入 BGE-M3 + Chroma，本阶段不做，也不接进 Planner。

**工具**：`scripts/build_experience.py`（读轨迹 JSONL → 灌库 → 打印统计）。验收 `lg_practice/day15_experience_check.py` **11/11**：派生、分类、只读过滤、去重、统计、脱敏、召回、终态接线、CLI 均通过；阶段 14 的 7/7 同时回归通过（其脚本已显式传 `record_experience: False`，避免两次验收互相污染）。

**过关题：为什么经验不能直接把“上一次模型的回答”当作事实？** 模型回答是对当时上下文的自然语言解释，没有可验证的锚点：它可能本身就是错的，可能和实际改动不一致，也可能在测试没过时仍说“已修复”。经验要能在新任务里被信任，就必须绑定可核验的证据——改动了哪些文件、测试真的过没过、评审结论是什么、谁批准过。所以每条经验都回链 `trajectory_id`，而它背后是真实工具调用与真实测试结果。

### 4.17 魔改十三：Experience Retrieval（阶段 16）

**目标**：新任务开始时先检索相似历史经验，交给 Planner 当参考，把路线图 §26 的 `User Task → Experience Retrieval → Planner` 接上。本阶段只用本地 BGE-M3 + Chroma，不花任何 LLM 额度。

**为什么改嵌入内容（本阶段最有价值的一次实测）**：最初把「任务 + 结果 + 涉及文件 + 步骤」整段拿去向量化，检索几乎排不动——三条候选的相似度是 0.468 / 0.466 / 0.460，几乎并列。逐项拆开测（查询是改写过的提问，正确历史任务是“修复 FastAPI route registration 造成的 404”）：

| 被向量化的文本 | 相似度（正确 / 无关 / 失败） | 结果 |
|---|---|---|
| 任务 + 结果 + 相同文件路径 | 0.468 / 0.460 / 0.466 | 几乎并列 |
| 任务 + 结果标签 | 0.514 / 0.468 / **0.517** | 被失败经验反超 |
| **只嵌任务本身** | **0.515 / 0.468 / 0.505** | 正确项第一 |

两个结论：① 文件路径、步骤这类结构字段在所有经验里高度重复，会把任务语义稀释掉；② 结果标签会给“问题形状”的提问染上失败语义，把提问拉向失败经验——而它本来也不该决定“哪条任务相似”，只该决定“拿到之后怎么用”。所以被向量化的文本现在只有任务本身，结果/文件/摘要全部退到 metadata。

**另一次反超暴露的定性问题**：只嵌任务后，逐字提问的相似度≈1.0、改写提问≈0.53，而无关任务也有 0.43。BGE-M3 对中文短句的相似度集中在一个很窄的带里，所以**排序才是信号，绝对值不是**。因此 `experience_min_similarity`（默认 0.40）只当“防止注入近乎无关命中”的兜底下限，不假装它是质量闸门；真正的保护是提示词里“经验只是参考、以实际读到的代码为准”这条硬规则。

**接线与降级**：`planner` 节点在侦察后调用 `recall_experiences`，把结果渲染成提示词的最后一段，并把 `experience_hits`（含 `trajectory_id`、`outcome`、`similarity`、`retrieval` 模式）写进 State，最终进轨迹——阶段 18 做 A/B 时就是靠这个字段判断“这次到底有没有经验可用”。`build_plan_user_message(..., experience_context="")` 与阶段 15 之前逐字一致：**没有相关经验，行为就完全不变**。Chroma/BGE-M3 不可用时自动退回阶段 15 的关键词召回，并把模式标注成 `keyword`（同时 `logger.warning` 记录原因，避免静默降级再次掩盖故障——这条是被自己的验收脚本用出来的）。

**验收**：`lg_practice/day16_experience_retrieval_check.py` **11/11**——含真实 BGE-M3 的语义召回（“这个 endpoint 为什么找不到？”与历史任务无任何共同词，仍命中正确轨迹）、accepted/rejected 区分、无命中时提示词逐字不变、关键词降级、`top_k`/相关性下限、空库无命中。阶段 14 7/7、阶段 15 11/11 同步回归通过。

**过关题：为什么经验检索必须区分“这么做能成功”和“这么做会失败”？** 两种经验的用法正好相反：accepted 是“可以照这个思路做”，rejected 是“这条路走不通，别重复踩”。如果混在一起当正面示范喂给模型，等于把已知的坑重新推荐一遍——失败经验的价值恰恰在于它标出了不该走的方向，以及（配合轨迹）当时失败在哪一步。

### 4.18 魔改十四：Experience-Guided Self-Correction（阶段 17）

**目标**：阶段 16 只在“动手之前”用经验；本阶段把经验推进到“已经失败之后”——`debugger` 生成修复指令前先检索同类历史任务，按“后来被修好过”与“当时最终没修好”分组附在失败信息后面。

**为什么 debug 用的是任务而不是失败堆栈**：阶段 16 实测过“往被向量化的文本里塞额外字段会稀释语义”，而索引里存的文档就是任务文本。拿失败输出（`assert 3 == 4` 这类）去搜任务库属于跨分布查询，命中质量没法保证。所以 debug 期的查询仍然用当前任务，经验的价值体现在**同一个任务上别人走通了哪条路、哪条路走不通**。

**三条硬约束**：① 无命中时 `debugger` 的提示词与阶段 11 **逐字一致**（验收脚本直接比对整段字符串）；② 经验是附加段，原文一字不改，且经验不能覆盖真实测试结果——测试说没过就是没过；③ `MAX_RETRIES` 与 `giveup` 逻辑完全没动，经验不会变成“再试一次”的借口。

**可观测**：debug 期命中写进 State 的 `experience_hits`，标 `phase="debug"` 与 `retrieval`（vector / keyword），并**追加**在规划期命中之后而不是覆盖——阶段 18 做 A/B 时，能直接看出某次任务是规划期就有经验、还是失败后才有。

**验收**：`lg_practice/day17_debug_experience_check.py` **7/7**（无命中逐字不变、有命中追加不改原文、可回链、State 累积、debug 措辞区分、关键词降级）。阶段 14 7/7、阶段 15 11/11、阶段 16 11/11 同步回归通过。

**过关题：为什么“失败经验”要配上“后来怎么修好的”才真正有用？** 只知道“这样会失败”只能排除一条路，却不知道往哪走；配上后来成功的改动，经验才从“警示牌”变成“绕行路线”。这也是为什么经验条目要同时存 `outcome` 和 `changed_paths`，并且两类经验在提示词里分组呈现。

### 4.19 魔改十五：Coding Benchmark（阶段 18）

**设计**：`evals/coding_benchmark.py` 用**同一批任务跑两遍**——第一遍冷启动（`experience_top_k=0`），把这些轨迹沉淀成经验；第二遍热启动（同一个经验库、开启检索）。两遍的模型、提示词、任务完全一致，唯一变量是“有没有经验可查”。

三个口径上的讲究：① **独立判分**——跑完自己再执行一次 pytest，不信 Agent 自报的结论；② 基线臂**仍然记录经验**（否则处理臂没有东西可查，实验从设计上就废了），只是不检索；③ 记录每次运行命中的经验条数，用来证明处理臂真的查到了东西。

**实测结果（n=3，每臂 3 次真实 LLM 任务）**：

| 指标 | Baseline | +Experience |
|---|---|---|
| 独立判分通过率 | 1.000 | 1.000 |
| 首次通过率 | 0.667 | 0.333 |
| 平均 attempts | 1.33 | 1.67 |
| 平均工具调用 | 27.0 | 23.0 |
| 平均耗时 | 103.7 s | 64.2 s |
| 命中经验的运行数 | 0 / 3 | 3 / 3 |

逐条明细（两个臂都 3/3 修对）：

| 任务 | 基线 attempts / 工具调用 | 处理臂 attempts / 工具调用 / 命中 |
|---|---|---|
| `stats_mean_empty` | 1 / 22 | 1 / 25 / 3 |
| `stats_median_even` | 1 / 34 | 2 / 23 / 6 |
| `math_safe_divide` | 2 / 25 | 2 / 21 / 6 |

**怎么读这组数（不许包装）**：

- **可以通过管道验证的**：整条链路在真实任务上跑通，包括经验检索真的触发（处理臂 3/3 命中）；工具调用数 −15%、耗时 −38%，说明有经验时探索更省。
- **不能声称的**：任务太简单，两臂都是 3/3，成功率撞到天花板，**无法区分好坏**；而且首次通过率反而下降（0.667 → 0.333）、平均 attempts 上升（1.33 → 1.67），方向和“经验减少试错”的预期相反。
- **统计上不许说的话**：n=3，任何单个任务翻转都会改变 33 个百分点，这只能算方向性观察，不能宣称显著性，也不能下“经验有用/没用”的结论。

**这次跑出来的两个真问题**（比数字更有价值）：

1. **沙箱文件必须 `git add -N`**：第一轮里 Agent 明明改对了（独立 pytest 2 passed），Reviewer 却判 `review_rejected`——因为新建的沙箱文件未被 git 跟踪，`git_diff` 看不到改动，评审员只看到“diff 里没有目标文件”。这正是阶段 12 加“评审范围”时踩过的同一类坑。
2. **递归上限不能拍脑袋定**：最初设 `recursion_limit=40`，一次正常的 25 次工具调用就会触发 `GraphRecursionError`。改成 80（与 day12 一致）后全部正常收敛。另外给 planner 加了 `planner_recon_steps` 配置（默认 3，本次基准用 1，两臂一致），因为需求里已经点名文件时多轮侦察纯属浪费调用。

**成本提醒**：一轮 12 次运行的基准会消耗大量 API 额度（本次中途就遇到过 402）。所以最终把规模收敛成 3 任务 × 2 臂，宁可样本小、口径清楚，也不拿一次跑不完的实验充数。

**过关题：为什么 Benchmark 必须用“同一批任务跑两次”，而不能用“加了经验之后挑几个成功案例”来证明变好了？** 挑案例是在已经知道结果的前提下选证据，任何系统都能挑出漂亮样本；只有固定任务、固定模型、只改一个变量、并且失败样本也照实计入，才能把“变好了”归因到经验本身。这也是本次即使结果不利于假设、也必须照原样记录的原因。

### 4.20 魔改十六：任务级工作区隔离（阶段 19）

**目标**：把“路径必须落在项目内”升级成“任务根本不跑在你正在开发的仓库里”。前者保证 Agent 不跑到仓库外面去，但它默认**要改的就是你的真实工作区**——模型判断失误时，被改坏的是开发者自己的代码。

**实现选择**：整树复制 + 以副本为工作目录运行（`src/agents/workspace.py` + `scripts/sandboxed_task.py`），没有把 `PROJECT_ROOT` 改成可注入的函数。理由很实在：后者要动 20 处引用、还得保证 15 个已通过的验收不变；而整树复制**不用改任何现有代码**——`PROJECT_ROOT` 是从 `__file__` 推出来的，副本里的解析结果自然就是副本。这是路线图“先做路径限制 + git diff，再考虑 Docker / WSL2 / Worktree”里的中间那一步。

**关键设计**：

| 设计 | 实现 | 为什么 |
|---|---|---|
| 隔离真实工作区 | 复制到 `.codex/sandboxes/<name>/`，任务在副本里跑完连副本一起删 | 失败任务的全部残留可以被一次性回收，不需要逐个回滚文件 |
| 复制时排除重物 | `.git` / `.venv` / `models` / `.codex` / `chroma_db` / 各类缓存 | 副本只需要“能跑起来”，不该带上 2 GB 模型和版本库 |
| 回收接口自己设防 | `reclaim_sandbox` 拒绝删除沙箱根目录之外的路径 | 一个删目录的工具，最该防的是自己被误用 |
| 同名重建是干净起点 | `create_sandbox` 先清同名目录 | 避免上一次失败任务的半成品污染下一次运行 |
| 换根不换约束 | 副本内 `../escaped.txt` 依然被拒 | 隔离与路径约束是两层，不是互相替代 |

**验收**：`lg_practice/day19_sandbox_check.py` **8/8**——副本内容与排除项、工具在副本内运行且 `PROJECT_ROOT` 指向副本、**主工作区零写入**、越权路径仍被拒、回收完整、回收接口拒绝误删真实目录、同名重建无残留。全程不调用 LLM。

**过关题：为什么“路径必须落在项目内”这条约束不足以代替真正的沙箱？** 因为这条约束只回答了“能不能越界”，没回答“越界以内的破坏怎么办”。Agent 在合法路径上写错内容、改错文件、跑坏配置，同样会污染正在开发的仓库；而且失败任务留下的中间状态需要人工逐个清理。沙箱把“破坏范围”本身变小，也让回收变成一次删除而不是一次代码考古。

### 4.21 魔改十七：容器化（阶段 20）

**先说清楚验证边界**：本机**没有安装 Docker**，所以镜像构建与容器启动**没有验证过**。这一阶段只做能确定性验证的部分（配置文件正确性、挂载点与代码真实路径是否一致、镜像内路径推导是否正确），并在验收脚本里把“未验证”写成一条显式结论。不把没跑过的东西写成跑过了。

**上游已有容器配置，缺的是这个 fork 的现实约束**：仓库自带 `compose.yaml` 与 `docker/Dockerfile.service`，所以本阶段改造成 `docker/Dockerfile.service.local` + `compose.local-models.yaml`（覆盖层），而不是另写一套——覆盖层能让同步上游时保持干净，也把“这个 fork 多了什么”集中在一个文件里。

**最重要的一个发现**：上游镜像把 `src/` **拍平**复制到 `/app/`（`/app/agents/code_tools.py`），而这个项目的路径是从 `__file__` 往上推两层算出来的：

| 镜像 | `code_tools.py` 位置 | `PROJECT_ROOT` 推导结果 | 默认模型路径 |
|---|---|---|---|
| 上游 `Dockerfile.service` | `/app/agents/code_tools.py` | **`/`** ← 失准 | `/models/bge-m3` |
| 本 fork `Dockerfile.service.local` | `/app/src/agents/code_tools.py` | **`/app`** ✅ | `/app/models/bge-m3` ✅ |

`PROJECT_ROOT` 变成 `/` 意味着 Coding Agent 的工作区根成了容器的根目录——`list_files` / `write_file` 的路径约束虽然还在，但约束的边界已经不是项目了。所以本地镜像**保留 `src/` 层级**，让所有由 `__file__` 推导出的路径与本地运行一致。这条判断不是推理出来的，是脚本解析 Dockerfile 的 `COPY` + `WORKDIR` 算出来的（见 `scripts/check_container_config.py`）。

**另外两处真实缺口**（同样是从代码里查出来的，不是猜的）：

1. **`sentence-transformers` / `torch` 不在 `uv.lock` 里**——它们是历史上用 pip 装进 venv 的。上游镜像跑 `uv sync --frozen` 不会带它们，容器里的 RAG 会直接报错。本地镜像显式补装，并且用 CPU 版 torch 索引避免拉进 CUDA 运行库。
2. **`git` 命令缺失**——`git_diff` 工具依赖它，`python:slim` 默认没有。本地镜像用 apt 补上（顺带装 `curl` 给 compose 健康检查用）。

**挂载策略**（三样都不进镜像）：

| 宿主机 | 容器内 | 为什么不能打进镜像 |
|---|---|---|
| `models/bge-m3`（约 2.3 GB） | `/app/models/bge-m3`（只读） | 镜像体积与重新下载成本；模型与代码的发布节奏也不同 |
| `src/chroma_db` | `/app/src/chroma_db` | 它是灌库产生的数据，服务用相对 CWD 的 `./chroma_db` 读取 |
| `.codex` | `/app/.codex` | 轨迹 / 经验库 / 任务沙箱，属于运行期数据，重建容器不该丢 |

还有一个容易踩的坑：`.env` 里的 `EMBEDDING_MODEL_PATH` 是 Windows 绝对路径（`D:/codex/working/models/bge-m3`），`env_file` 会把它原样带进容器，导致 RAG 报“路径不存在”。覆盖层里显式改成 `/app/models/bge-m3`。

**验收**：`lg_practice/day20_container_check.py` **11/11**（文件齐备、COPY 源存在、上游失准 / 本地正确、覆盖层指向、三处挂载、环境变量覆盖、两个依赖缺口、静态校验整体通过、Docker 缺失这条如实记录）。

**过关题：为什么模型权重、向量库、经验库这三样东西不该打进镜像里？** 三样都是**数据**而不是**代码**：模型权重体积大且与代码发布节奏无关，打进镜像会让每次改一行代码都重新搬运几 GB；向量库和经验库是运行期产物，会随每次任务不断变化，固化进镜像等于每次运行都从过去的快照开始，容器一重建就把新积累的经验丢掉。把它们挂载出来，镜像才只承载“可复现的运行环境”这一件事。

### 4.22 魔改十八：基础成本控制（阶段 21）

**范围**：只做最基本的成本控制，不做花哨的分层策略。v5 §40 的完整设想里有 Local 7B + Cheap API + Strong API 三层加 Failure Router，本项目**明确不引入更贵的模型档位**——最高档就是 `deepseek-v4-flash`，所以阶梯只有 `local（若配置）→ cheap(flash)`。

三件具体的事：

1. **账面可见**：每次 LLM 调用累加 `llm_calls` 与 `estimated_tokens`，写进 State 和轨迹。以前只能凭感觉说“这个任务挺贵的”，现在每条轨迹都能直接读出调用次数与估算 token。
2. **能用免费档就用免费档**：只有真正配置了本地模型（如 Ollama）时才把它放进阶梯，简单任务优先走本地；复杂任务（计划超过 3 步或存在未决问题）直接上 flash，不在关键处省错地方。没配本地模型时阶梯只有一档，不假装有一台不存在的模型。
3. **预算超了冻结升级**：`budget_tokens` 用尽后不再从免费档换到付费档。重试次数仍由 `MAX_RETRIES` 决定——**成本控制不越权去改任务终止条件**。

**一条硬约束**：`model_routing` 不在 config 里时，`route_model()` 原样返回今天用的 `model`，行为逐字不变。不启用就等于不存在，这条由验收脚本直接断言（三个角色都返回 `fixed-model`）。

**成本估算的现实说明**：`estimated_tokens` 用的是「字符数 ÷ 3」的粗估，只适合比较同一条链路里的相对消耗，不是账单。写这句话是为了避免以后拿它当计费数据用。

**验收**：`lg_practice/day21_model_routing_check.py` **10/10**，全程不调用 LLM——路由是纯决策逻辑；节点接线用打桩模型验证（stub 记录“实际被以什么名字创建”，所以证明的是接线真的生效，而不只是函数返回值对）。阶段 14 7/7、15 11/11、16 11/11、17 7/7 同步回归通过。

**过关题：为什么成本控制不应该顺手去改“任务什么时候放弃”？** 因为那是两件性质不同的决定：成本控制的目标是“在给定质量下少花钱”，而放弃任务的目标是“确定不再有收益”。把两者混在一起，会出现“因为省钱所以把任务判失败”这种说不清责任的行为——用户看到的是任务失败，原因却是预算策略。所以这里预算只影响用哪档模型，重试与放弃仍旧归 `MAX_RETRIES` 和 `giveup` 管，两者互不越权。

### 4.23 魔改十九：可配置 Agent（阶段 22）

**先说清楚做到了哪一步**：v5 对 Agent 平台的完整设想是「Agent 配置化 + Agent Builder 界面 + Workflow 编排 + Multi-Agent」。本阶段完成的是**第一块地基——把 Agent 从写死的 Python 模块变成可校验的数据**；界面与编排没有做，也不该在这一步假装做了。理由：`agents.py` 原本是一个写死的字典，每个 Agent 都是独立的 Python 模块，想改系统提示词、换工具集合、调模型都要改代码，这时候加一个配置界面只是在给硬编码套壳。

**数据形态**（`config/agents/*.yaml` → `src/agents/agent_config.py`）：

| 字段 | 作用 | 校验 |
|---|---|---|
| `key` / `description` | 注册表键与给人看的说明 | 必填、同目录内不得重名 |
| `system_prompt` | 这个 Agent 的角色与规则 | 必填（空提示词的 Agent 没有意义） |
| `tools` | 允许使用的工具名（白名单） | **未知工具名当场报错并列出可用工具** |
| `model` | 可选，不填则用运行时传入的模型 | — |
| `max_tool_rounds` | 工具循环上限（1–50） | 越界被 Pydantic 拒绝 |

**编译**（`src/agents/declarative_agent.py`）：配置被编译成一张最小的通用图 `START → model ⇄ tools → END`。两个细节是踩过坑才写对的：

1. **不在“工具还没执行”的状态下结束**：循环上限的检查放在 `tools` 之后。如果写在 `model` 之后截断，最后一条消息会是“要调工具但没人执行”的残缺消息——这正是项目踩坑记录里第 4 条（DeepSeek 400）的同类问题。验收脚本专门断言了收尾时最后一条消息是 `ToolMessage`。
2. **白名单校验两次**：加载配置时拦一次，运行时再拦一次；越权调用只得到一条 ERROR 的 `ToolMessage`，不会真的执行。

**平台化的第一版只开放只读工具**（`search_code` / `read_file` / `list_files` / `git_diff`）。把写权限交给配置文件是另一个量级的风险，需要先有审批与沙箱兜底——而这两样分别在阶段 13 与阶段 19 才有，所以这里刻意不开。

**合并策略**：配置型 Agent 与内置 Agent 合并进同一个注册表，`key` 冲突直接报错，不允许悄悄覆盖内置实现。没有配置文件时 `_configurable_agents()` 返回空字典，行为与以前完全一致（`CONFIG_AGENTS=0` 可以整体关闭）。当前注册表 11 个内置 + 1 个配置型 = 12 个，`DEFAULT_AGENT` 仍是 `research-assistant`。

**为什么配置错误要“启动就炸”**：配置系统里静默降级比启动失败更贵——你会以为那个 Agent 还在，直到线上才发现它少了一个工具或者根本没注册。所以缺字段、未知工具、key 重名都会带着文件名抛错。

**验收**：`lg_practice/day22_agent_config_check.py` **9/9**，全程不调用 LLM（工具循环用打桩模型驱动）。覆盖：示例配置解析、未知工具报错带可用清单、缺字段报错带文件名、重名拒绝、目录缺失返回空、图结构正确、循环上限生效且收尾合法、注册表合并、白名单不含写工具。

**过关题：Agent 平台化为什么必须先把 Agent 变成可配置数据，而不能靠加一个配置界面解决？** 界面只是数据的编辑器；如果底层仍是写死的 Python 模块，界面能改的东西只能是它背后已经存在的那几个参数，改提示词、换工具、调模型依旧要动代码。先把 Agent 表达成「提示词 + 模型 + 工具 + 上限」这样一份可校验的数据，界面才有东西可编辑，编排才有东西可组合，校验与权限（比如只读白名单）也才有落点。

### 4.24 魔改二十：工作流编排（阶段 22 第二块）

**做到哪一步**：只做**线性串联**——上一步的输出成为下一步的输入。分支、并行、条件跳转都没做，也不该现在做：那三样都需要先有可靠的失败传播与回滚设计，硬做出来只会得到一个看起来很强、实际上没人能解释清楚执行路径的图。

**形态**（`config/workflows/*.yaml` → `src/agents/agent_workflow.py`）：

```yaml
key: explain-then-summarize
steps:
  - agent: repo-explainer        # 引用已有 Agent 的 key
    name: locate
    input_template: "{input}"
  - agent: chatbot
    name: summarize
    input_template: |
      以下是代码定位结果，请整理成一段说明并保留文件路径与行号：
      {previous}
```

两个占位符：`{input}` 是最初需求（每步都能拿到），`{previous}` 是上一步输出。渲染用字符串替换而不是 `str.format()`——否则模板里任何其它花括号都会被当成字段名而报错。

**校验与注册**：引用的 Agent 必须存在（加载时校验一次、构建图时再校验一次）；步骤不能为空；key 不能与已有 Agent 重名。编译出来的图是 `START → step_1 → step_2 → … → END`，并且**以 Agent 身份注册进同一个注册表**，所以服务端不需要为"工作流"新增一套接口——它就是一个 Agent。当前注册表 11 内置 + 1 配置型 + 1 工作流 = 13 个。

**已知边界**：延迟加载（lazy）的 Agent 不能放进工作流，因为工作流在启动时就要拿到图，而延迟加载的图那时还不存在——这条会在加载时报错，不会留到运行期才发现。

**验收**：`lg_practice/day23_workflow_check.py` **10/10**，全程不调用 LLM。关键一条是**用打桩图验证真的串起来了**：第一步收到的 prompt 是原始需求，第二步收到的 prompt 里确实嵌着第一步的输出（`看这个：A:找一下 FastAPI 入口 / 原需求：找一下 FastAPI 入口`），这比断言"返回值不为空"能说明问题得多。

**诚实记录**：编排机制用打桩图验证完毕；**真实端到端跑一次工作流需要 LLM 额度，尚未执行**。这一点写在验收脚本的最后一条检查里，而不是留给我们自己记。

**过关题：为什么工作流的第一版应该只做线性串联？** 因为编排的复杂度不在"怎么连"，而在"出错时怎么办"：并行分支要回答部分失败如何回滚，条件跳转要回答状态不一致如何判定，多 Agent 要回答谁对最终结果负责。线性串联只有一个失败方向（当前步失败就整条停），语义清晰、可解释、可回收；等失败传播有了确定设计，再往上加分支才不是空中楼阁。

### 4.25 魔改二十一：并行编排 / 多 Agent 路由 / Agent Builder（阶段 22 收尾）

上一节说"第一版只做线性串联"，这一节把另外两种基本形态和界面补上了。**三种模式现在都在配置里选**（`mode` 字段）：

| 模式 | 语义 | 失败语义 |
|---|---|---|
| `sequential` | 上一步输出成为下一步输入 | 当前步失败即整条停 |
| `parallel` | 所有步骤拿同一个输入并行跑，输出按声明顺序汇总 | 任一失败即整条失败 |
| `router` | 一个 supervisor 在候选里**选一个**执行 | 选谁执行谁；解析不出就退回第一个候选 |

**并行模式为什么只用一个节点**：把图摊成扇出扇入会让失败语义变模糊（"三个分支成了两个"时调用方还得自己判断完整性）。用一个节点包住 `asyncio.gather`，失败就整条失败，一句话能说清。验收脚本直接断言了图里只有 `parallel` 一个节点。

**路由模式按最小实现做**：`routing_prompt` 写选人规则，模型只回复候选 key，代码用**子串匹配白名单**确认（不信任模型自由发挥出来的名字），匹配不上就退回第一个候选。验收里两种情况都测了：模型答"选 b"→ 执行 b；模型答一段没提任何候选的话 → 退回 a，不会造出一个不存在的 Agent。

**Agent Builder 界面**（`src/agent_builder_app.py`，独立入口 `streamlit run src/agent_builder_app.py`）：列出现有配置、编辑提示词/工具/轮数上限、保存与删除。**逻辑全在 `agents/agent_builder.py`**，那一层不依赖 Streamlit，所以可以离线测——这也是为什么验收里能断言"逻辑层源码里没有 streamlit"，界面只是薄壳，不存在"只有点开页面才能验证"的死角。

两个写入上的约束：保存前先校验（未知工具拒绝落盘，半成品不进 `config/` 目录，避免下次启动直接崩）；删除只按 key 推导文件名并拒绝非法字符，不接受任意路径。

**验收**：`lg_practice/day24_platform_check.py` **14/14**，全程不调用 LLM（编排用打桩图、路由用打桩模型）。注册表现在是 11 内置 + 1 配置型 + 3 工作流 = 15 个。

**过关题：为什么 Agent Builder 的逻辑层要和界面分开？** 因为界面是数据的编辑器，而"什么配置算合法"是业务规则。规则一旦长在按钮的回调里，就只能靠人点开页面来验证，改一次要重新点一遍，也做不到回归测试。把规则抽到不依赖框架的模块，界面只剩渲染与收集输入，逻辑才能被脚本反复验证——本节的 14 项验收里，Builder 那 4 项就是这么来的。

### 4.26 补账：基准的成本口径（阶段 18 的回填）

**为什么要补**：阶段 18 的 A/B 只报成功率、首次通过率、attempts、工具调用与耗时——**没有成本**。而这一阶段真正要验证的主张是"成功率接近 + 成本更低"，缺了成本口径，基准就证明不了"更省"。阶段 21 加的 `llm_calls` / `estimated_tokens` 正好补上这一块：轨迹里有，基准把它读出来就行。

**改了什么**：`evals/coding_benchmark.py` 的每行记录新增 `llm_calls` / `estimated_tokens` / `model_used`，`summarize()` 新增 `avg_llm_calls` / `avg_estimated_tokens` / `total_estimated_tokens`，运行时的进度行也把 token 估算打出来。

**顺手修掉一个真问题**：改 `summarize()` 时加了向后兼容断言，结果立刻抓到它对 `agent_status` 用的是直接下标——**旧报告或残缺行会让汇总直接崩**。已改成全部 `.get()` 取值。用真实的历史报告验证过：旧 JSON 能正常重算，且旧行的成本显示为 0（那些运行发生在阶段 21 之前，本来就没有记账）——这个 0 是事实，不是缺失。

**验收**：`lg_practice/day25_benchmark_cost_check.py` **4/4**（成本汇总正确、与成功率口径互不干扰、缺字段不崩、源码里确实从轨迹读成本字段）。不调用 LLM。

### 4.27 补账：平台功能第一次真跑（阶段 22 的回填）

**为什么要跑**：§4.23–§4.25 全部用打桩验证机制，一次真实的 LLM 调用都没发生。打桩能证明"接线对"，不能证明"端到端能用"。真跑之后发现了一个打桩**永远发现不了**的 bug。

| 场景 | 结果 | 耗时 | 关键观察 |
|---|---|---|---|
| `parallel-review` | ✅ | 8.5 s | 定位路读到 `src/run_service.py:84-86` 的真实代码，清单路给出 5 条检查项 |
| `route-to-specialist` | ✅ | 2.1 s | 选中 chatbot，答出正确的 REST API 解释（87 字） |
| Builder 新建 Agent | ✅ | 1.6 s | 保存 → 注册 → 真实调用 → 返回问候 → 自动清理配置 |

**找到的真 bug（核心收获）**：工作流的输入来自 `state["workflow_input"]`，而**服务端只会传 `messages`**。于是通过服务调用工作流时，Agent 收到的是**空输入**——首次真跑时并行那一路抱怨"输入里没有内容"，路由那路只吐出 13 个字的寒暄。为什么打桩没发现：我的 day23/day24 用例**每次都显式传了 `workflow_input`**，等于绕开了这个路径，测试通过反而掩盖了缺陷。

修复：新增 `user_input(state)`，优先用显式传入的 `workflow_input`，缺省时从最后一条 `HumanMessage` 取。并补了一条**只传 messages** 的回归用例（day24 从 14 项变成 **15/15**）——把"测试恰好绕开的那条路"补成常规用例，这类 bug 才不会复现。

**另外两处真跑才暴露的质量问题**（都靠改配置解决，正好演示平台的可配置性）：

1. **路由把通用问题派给了代码 Agent**：问"什么是 REST API"，supervisor 选了 `repo-explainer`。改法是把判断规则写死进 `routing_prompt`——"先问用户是否点名了本仓库的具体文件/函数，否就一律选 chatbot"。重跑后正确选中 chatbot 并答对。
2. **`repo-explainer` 在没读到文件时长篇推测**：它输出了一大段"我没有权限/没搜到"的解释。改法是在系统提示词里加一条硬规则：两次搜索都没读到文件就直说"没找到"并列出试过的关键词，不要输出推测长文。

**一个操作层面的坑（值得记）**：我一开始用 `python -c` 内联跑真实验证，PowerShell 把中文输入搞成了乱码，模型于是返回了一段**完全无关的数学解答**。看起来像模型崩了，实际是输入被破坏。结论：真实验证一律走 UTF-8 脚本文件并把输出重定向到文件读取，不要用内联命令传中文。

**验收**：`lg_practice/day26_platform_live_check.py` **3/3**（真实 LLM，约 12 秒 + 少量调用）。阶段 22 至此从"机制已验证"变成"端到端已验证"。

---

## 5. 文件清单

### 5.1 对项目的改动（已提交）

| 文件 | 类型 | 说明 |
|---|---|---|
| `src/agents/tools.py` | 修改 | 本地 BGE-M3 + retriever 单例/重试 |
| `src/service/service.py` | 修改 | 启动预热 Chroma |
| `scripts/create_chroma_db.py` | 修改 | 本地 embeddings + 路径参数化 + 修 import |
| `src/agents/code_tools.py` | **新增** | `list_files` / `read_file` / `search_code` / `write_file` / `edit_file` / `git_diff` |
| `src/agents/test_tools.py` | **新增** | `run_tests`（只允许 pytest，结构化结果） |
| `src/agents/coding_planner.py` | **新增** | Planning：只读侦察 → JSON 计划 → 确定性校验 |
| `src/agents/reviewer.py` | **新增** | Reviewer：只读独立评审 + 结构化裁决 |
| `src/agents/trajectory.py` | **新增** | JSONL 轨迹构建、脱敏、持久化与聚合 |
| `src/agents/experience.py` | **新增** | 轨迹→经验派生 + SQLite 经验库（回链 / 去重 / 脱敏 / 召回） |
| `src/agents/coding_memory.py` | **新增** | BGE-M3 + Chroma 经验检索、接入 Planner、关键词降级 |
| `evals/coding_benchmark.py` | **新增** | 阶段 18 基准：同批任务跑两遍 + 独立判分 + 指标汇总 |
| `src/agents/workspace.py` | **新增** | 任务级工作区隔离：整树复制、回收自防、沙箱环境变量 |
| `src/agents/model_router.py` | **新增** | 基础成本控制：调用/估算记账、免费档优先、预算冻结升级 |
| `src/agents/agent_config.py` | **新增** | Agent 配置数据定义与校验（含工具白名单、重名拒绝） |
| `src/agents/declarative_agent.py` | **新增** | 把 Agent 配置编译成 `model ⇄ tools` 图 |
| `config/agents/repo-explainer.yaml` | **新增** | 示例配置型 Agent（只读代码讲解） |
| `src/agents/agent_workflow.py` | **新增** | 线性工作流编排：配置校验 + 编译成链式图 |
| `config/workflows/explain-then-summarize.yaml` | **新增** | 示例工作流（定位 → 总结） |
| `src/agents/agent_builder.py` | **新增** | Agent Builder 纯逻辑层（列出 / 保存 / 删除，不依赖 Streamlit） |
| `src/agent_builder_app.py` | **新增** | Agent Builder 界面（薄壳，独立 Streamlit 入口） |
| `config/workflows/parallel-review.yaml` | **新增** | 并行编排示例（两路同时跑，汇总输出） |
| `config/workflows/route-to-specialist.yaml` | **新增** | 多 Agent 路由示例（supervisor 选一个执行） |
| `scripts/sandboxed_task.py` | **新增** | 在隔离副本里跑一次任务（`--no-agent` 只验隔离） |
| `docker/Dockerfile.service.local` | **新增** | 保留 src/ 层级的服务镜像：补 git、CPU torch、sentence-transformers |
| `compose.local-models.yaml` | **新增** | compose 覆盖层：挂载模型 / 向量库 / .codex，覆盖 Windows 模型路径 |
| `scripts/check_container_config.py` | **新增** | 容器配置静态校验（含镜像内 `__file__` 路径推导） |
| `scripts/build_experience.py` | **新增** | 把轨迹 JSONL 灌进经验库并输出统计 |
| `src/agents/coding_agent.py` | **新增** | Coding Agent 图：planner → coder ↔ tools，`allow_write=True` 时接 tester/debugger/giveup 自修复闭环；写操作前有 HITL 审批闸门 |
| `src/agents/agents.py` | 修改 | 注册 `coding-agent` |
| `.gitignore` | 修改 | 忽略个人练习目录 `study_test11/` |

### 5.2 练习与验证脚本（`lg_practice/`，不进版本库）

| 文件 | 用途 |
|---|---|
| `day2_mini_graph.py` | LangGraph 迷你图（字符串版） |
| `day2_mini_graph01.py` | 同上，早期版本 |
| `day2_mini_graph_v2.py` | 迷你图（结构化消息 + 官方 `ToolNode`） |
| `day2_retrieval_probe.py` | RAG 检索实证（Top-K + 分数对比） |
| `day2_retrieval_probe.bak` | 初版（曾静默退回 mock 数据，留作反面教材） |
| `day3_code_tools_check.py` | `code_tools` 的 6 项验收脚本 |
| `day4_coding_agent.py` | 把 code_tools 接到 Agent 的练习版 |
| `day5_search_code_check.py` | `search_code` 的 9 项验收脚本 |
| `day6_search_vs_read_benchmark.py` | search_code 与 read_file 的对照实验 |
| `day7_edit_tools_check.py` | `write_file` / `edit_file` 的 11 项验收脚本 |
| `day8_git_diff_check.py` | `git_diff` 的 8 项验收脚本 |
| `day9_run_tests_check.py` | `run_tests` 的 9 项验收脚本 |
| `day10_planner_check.py` | Planning 的 10 项验收脚本 |
| `day11_self_correction_check.py` | 自修复闭环的 11 项验收脚本（含两次真实端到端运行） |
| `day12_reviewer_check.py` | Reviewer 的 8 项验收脚本（含两次真实评审） |
| `day13_hitl_check.py` | HITL 的 8 项验收脚本（暂停 / 批准 / 拒绝 / 关开关 / 只读不打扰） |
| `day14_trajectory_check.py` | Trajectory 的 7 项验收脚本（持久化 / 脱敏 / 失败路径 / 聚合） |
| `day15_experience_check.py` | Experience Memory 的 11 项验收脚本（派生 / 去重 / 回链 / 脱敏 / 召回 / 接线） |
| `day16_experience_retrieval_check.py` | Experience Retrieval 的 11 项验收脚本（真实语义召回 / 无命中不变 / 降级 / 下限） |
| `day17_debug_experience_check.py` | 经验驱动自修复的 7 项验收脚本（注入 / 无命中逐字不变 / State 累积 / 降级） |
| `day19_sandbox_check.py` | 工作区隔离的 8 项验收脚本（零污染 / 越权仍拒 / 回收自防 / 重建无残留） |
| `day20_container_check.py` | 容器化的 11 项静态验收脚本（挂载 / 路径推导 / 依赖缺口 / 未验证如实记录） |
| `day21_model_routing_check.py` | 成本控制的 10 项验收脚本（零影响 / 阶梯 / 记账 / 预算冻结 / 打桩接线） |
| `day22_agent_config_check.py` | 可配置 Agent 的 9 项验收脚本（校验 / 图结构 / 循环上限 / 注册表合并） |
| `day23_workflow_check.py` | 工作流编排的 10 项验收脚本（串联传递 / 模板 / 校验 / 注册） |
| `day24_platform_check.py` | 并行 / 路由 / Builder 的 14 项验收脚本（打桩图与打桩模型，零 API 调用） |
| `day25_benchmark_cost_check.py` | 基准成本口径的 4 项验收脚本（含旧报告重算不崩） |
| `day26_platform_live_check.py` | 平台功能真跑脚本（并行 / 路由 / Builder，真实 LLM，3/3） |

### 5.3 本地数据（不进版本库）

| 路径 | 说明 |
|---|---|
| `D:\codex\working\models\bge-m3` | 本地向量模型（约 2.1 GB） |
| `src/chroma_db` | 向量库（3 个 chunk） |
| `src/checkpoints.db` | 会话记忆（SQLite） |
| `D:\codex\working\logs` | 服务与前端运行日志 |
| `.codex\trajectories\coding_agent.jsonl` | 阶段 14 的任务轨迹（JSONL） |
| `.codex\experience\experience.db` | 阶段 15 的经验库（SQLite） |
| `.codex\experience\chroma` | 阶段 16 的经验向量索引（Chroma） |
| `.codex\sandboxes\<name>` | 阶段 19 的任务隔离副本（运行期间存在，结束即回收） |
| `.env` | Key 与配置（git 忽略） |

---

## 6. 踩坑记录（也是面试素材）

| # | 现象 | 根因 | 解决 |
|---|---|---|---|
| 1 | 知识库问答必然 500 | `tools.py` 写死 `OpenAIEmbeddings()`，没有 OpenAI Key | 换成本地 BGE-M3 |
| 2 | 换了模型仍 500，说"路径不存在" | 直接 `python -m uvicorn ...` 启动不会执行 `load_dotenv()`，`os.getenv` 读不到 `EMBEDDING_MODEL_PATH` | 改用官方入口 `run_service.py`，并在 `tools.py` 里补 `load_dotenv()` 兜底 |
| 3 | 第一次检索必崩，报 `'RustBindingsAPI' object has no attribute 'bindings'` | chromadb 1.5.9 首次创建客户端时的生命周期缺陷，且原代码每次工具调用都新建客户端 | retriever 进程内单例 + 失败重试 3 次 + 启动预热 |
| 4 | 追问时报 `tool_calls must be followed by tool messages`（DeepSeek 400） | 之前失败运行留下的 checkpoint 里只有"AI 要调工具"，没有配对的工具结果 | 用新的 `thread_id`（UI 里点 New Chat） |
| 5 | 老脚本"跑得通"但结果是假的 | 脚本 `except ImportError` 后静默退回内置 mock 数据，把失败藏了起来 | 去掉静默兜底，让失败直接暴露 |
| 6 | 大模型文件下载反复卡死 | HuggingFace / 镜像 / ModelScope 对大文件连接不稳，卡在 47 MB / 686 MB / 742 MB | `curl -L --retry 50 --speed-limit --speed-time -C -` 限速重连续传，下完用 SHA256 校验 |
| 7 | `list_files` 能列出项目外目录 | `Path.glob("../*")` 不受项目根约束 | 工具入口加同一套 `_resolve_inside()` 安全闸门 |
| 8 | `read_file` 遇到目录会崩 | 只判断了"存在"，没判断"是文件" | `is_file()` 检查 + 目录单独报 `ERROR` |
| 9 | `uv` 不在 PATH，venv 无 pip | 环境不完整 | `python -m ensurepip` 后用 pip 装依赖 |
| 10 | 服务启动报 `ImportError: cannot import name 'coding_agent'` | 编辑器里把 `code_tools.py` 的内容保存进了 `coding_agent.py`，Agent 图代码被整段覆盖，导致 Agent 注册表导入失败 | 先把误存内容备份到仓库外，再 `git restore --source=HEAD -- src/agents/coding_agent.py` 恢复 |

> 依赖管理提醒：`sentence-transformers` / `torch` 等是用 pip 装进 venv 的，**没有写进 `pyproject.toml`**。如果以后执行 `uv sync --frozen`，这些包会被移除，RAG 会重新报错。届时需要把 `sentence-transformers` 加入 `pyproject.toml` 并重新 lock。

---

## 7. 当前进度

### 7.1 已完成

- [x] 原项目跑通（FastAPI + Streamlit + DeepSeek 聊天 + 知识库问答）
- [x] 认全请求链路与 `rag_assistant` 图结构
- [x] LangGraph 三件套：能自己写 StateGraph（含结构化 tool_calls 与 `ToolNode`）
- [x] RAG 全链路理解 + 真实检索实证
- [x] 魔改一：本地 BGE-M3 替换 OpenAI（无需任何外部 Key）
- [x] 魔改二：`list_files` / `read_file` 工具 + 能看仓库的 `coding-agent`（已注册、已实测）
- [x] 魔改三：`search_code`（验收 9/9 + 对照实验数据：工具调用 12→7、读取文件 9→4）
- [x] 魔改四：`write_file` / `edit_file`（默认不覆盖、唯一命中才替换、敏感文件黑名单，验收 11/11）
- [x] 魔改五：`git_diff`（改动可见：status 段看新文件、`--cached` 看暂存区、超长截断，验收 8/8）
- [x] 魔改六：`run_tests`（结构化测试结果、失败带文件名行号、超时不卡死、只允许 pytest，验收 9/9）
- [x] 魔改七：Planning（`coding_planner.py`：只读侦察 → JSON 计划 → 确定性校验 → 写入 State，验收 10/10）
- [x] 魔改八：Debug / Self-Correction（写权限受控开放 + tester/debugger/giveup 闭环，验收 11/11）
- [x] 魔改九：Reviewer（只读独立评审 + 结构化裁决 + 评审范围可控，验收 8/8）
- [x] 魔改十：HITL（写操作前 `interrupt()` 等人批准；拒绝也会留下记录，验收 8/8）
- [x] 魔改十一：Trajectory（统一终态收口 + JSONL + 脱敏 + 基础聚合，验收 7/7）
- [x] 魔改十二：Experience Memory（轨迹→经验派生 + SQLite 经验库 + 回链去重，验收 11/11）
- [x] 魔改十三：Experience Retrieval（BGE-M3 + Chroma 语义召回 + Planner 注入 + 无命中零影响，验收 11/11）
- [x] 魔改十四：Experience-Guided Self-Correction（debugger 检索同类经验并按成败分组，验收 7/7）
- [x] 魔改十五：Coding Benchmark（Baseline vs +Experience 同批任务两遍跑，独立判分，n=3 见 §4.19）
- [x] 魔改十六：Workspace Sandbox（整树复制 + 副本内执行 + 完整回收，主工作区零污染，验收 8/8）
- [x] 魔改十七：容器化（保留 src/ 层级的镜像 + compose 覆盖层 + 静态校验 11/11，构建未验证）
- [x] 魔改十八：基础成本控制（记账 + 免费档优先 + 预算冻结升级，最高档 flash，验收 10/10）
- [x] 魔改十九：可配置 Agent（YAML 定义 + 编译成图 + 只读白名单 + 注册表合并，验收 9/9）
- [x] 魔改二十：工作流编排（线性串联 + 模板占位符 + 以 Agent 身份注册，验收 10/10）
- [x] 魔改二十一：并行编排 + 多 Agent 路由 + Agent Builder（配置里选 mode，验收 14/14）
- [x] 3 个提交推送到自己的 GitHub fork，且已 rebase 到上游最新

### 7.2 已知限制 / 待办

- [ ] DeepSeek 偶发流式超时（`No streaming chunk received for 120.0s`）会让单次规划/回答失败；后续需要加超时与重试配置（如 `stream_chunk_timeout`）
- [ ] 没有评测（benchmark）与指标（成功率 / 测试通过率 / 迭代次数 / 延迟 / token 成本）
- [ ] 知识库仍只有 3 个 chunk（手册太小），检索效果不具代表性
- [ ] `format_contexts()` 丢弃 metadata，答案无法溯源到页码（Citation 未做）
- [ ] 服务无鉴权（未设 `AUTH_SECRET`），仅限本机使用
- [ ] `/history` 对不存在的 thread 返回 500（上游边界问题，暂未修）
- [ ] 依赖用 pip 安装，与 `uv.lock` 不一致（见 §6 提醒）

---

## 8. 复现步骤（从零到可用）

```powershell
# 1) 克隆自己的 fork
git clone https://github.com/qr7896/agent-service-toolkit.git
cd agent-service-toolkit

# 2) 建虚拟环境并装依赖（等价于 uv sync）
python -m venv .venv
.\.venv\Scripts\python.exe -m ensurepip --upgrade
.\.venv\Scripts\python.exe -m pip install -e .          # 或按 pyproject 安装
.\.venv\Scripts\python.exe -m pip install sentence-transformers

# 3) 准备本地向量模型（放在 D 盘工作目录）
#    BAAI/bge-m3 官方权重 -> D:\codex\working\models\bge-m3

# 4) 配置 .env（在仓库根目录）
#    DEEPSEEK_API_KEY / DEFAULT_MODEL / AGENT_URL / EMBEDDING_MODEL_PATH / NO_PROXY

# 5) 灌知识库（必须站在 src 目录，这样库会建在 src/chroma_db）
cd src
$env:CHROMA_DATA_DIR='../data'; $env:CHROMA_DB_DIR='./chroma_db'
..\.venv\Scripts\python.exe ..\scripts\create_chroma_db.py

# 6) 启动服务与前端（见 §2.2）

# 7) 验证
#    GET  http://localhost:8080/info                 -> agent 列表含 coding-agent
#    POST http://localhost:8080/coding-agent/invoke  -> 问"AgentClient 在哪里定义的？"
```

---

## 9. 下一步

### 9.1 已完成（阶段 6–13）

- **阶段 6 `search_code`**：验收 9/9，对照实验数据见 §4.7
- **阶段 7 `write_file` / `edit_file`**：验收 11/11，设计见 §4.8
- **阶段 8 `git_diff`**：验收 8/8，设计见 §4.8
- **阶段 9 Planning**：验收 10/10，设计与踩坑见 §4.10
- **阶段 10 `run_tests`**：验收 9/9，设计与过关题回答见 §4.9
- **阶段 11 Debug / Self-Correction**：验收 11/11，设计与过关题回答见 §4.11
- **阶段 12 Reviewer**：验收 8/8，设计见 §4.12
- **阶段 13 HITL**：验收 8/8，设计与过关题回答见 §4.14
- **阶段 14 Trajectory**：验收 7/7，设计与过关题回答见 §4.15
- **阶段 15 Experience Memory**：验收 11/11，设计与过关题回答见 §4.16
- **阶段 16 Experience Retrieval**：验收 11/11，设计与过关题回答见 §4.17
- **阶段 17 Experience-Guided Self-Correction**：验收 7/7，设计与过关题回答见 §4.18
- **阶段 18 Coding Benchmark**：已跑通，结果与局限见 §4.19；报告在 `.codex/benchmark/report.json`
- **阶段 19 Workspace Sandbox**：验收 8/8，设计与过关题回答见 §4.20
- **阶段 20 容器化**：静态验收 11/11，设计与“未验证”边界见 §4.21
- **阶段 21 基础成本控制**：验收 10/10，设计与过关题回答见 §4.22
- **阶段 22 可配置 Agent**：验收 9/9，设计与“做到哪一步”的边界见 §4.23
- **阶段 22 工作流编排**：验收 10/10，设计与边界见 §4.24
- **阶段 22 并行 / 路由 / Builder**：验收 14/14，设计与过关题回答见 §4.25

### 9.2 后续（路线图全部完成，剩下的是两笔待补的账）

路线图 §22 的 20 个阶段已经走完（阶段 18 Evaluation 已完成，因此 v5 里“排在 Evaluation 之后”的两个新方向现在才轮到）。

**21 · 基础成本控制**：已完成（§4.22）。最高档只到 `deepseek-v4-flash`。

**22 · Agent 平台**：三块全部完成——§4.23 数据化、§4.24/§4.25 三种编排模式（线性 / 并行 / 路由）、§4.25 Builder 界面。注册表 15 个 Agent，全部走同一套注册与校验。

**两件待补的账**（不隐藏；"平台功能没真跑过"这一笔已在 §4.27 结清）：

- **阶段 18 的样本量**：n=3 只能算方向性观察，成功率和首次通过率都还不足以下结论。要写进简历或答辩，需要扩充任务数并提高任务难度，让成功率不再撞天花板。**成本口径已在 §4.26 补上**，重跑时每行会带 `llm_calls` / `estimated_tokens`。
- **阶段 20 的构建验证**：本机没有 Docker。有 Docker 的环境里应补一次 `docker compose -f compose.yaml -f compose.local-models.yaml up --build`，确认服务能起来、能回答普通问题，并确认重启后 `.codex` 数据仍在。
- ✅ **平台层的真实调用**（已结清，见 §4.27）：并行、路由、Builder 新建 Agent 三项各真跑一次，3/3 通过，并因此发现并修掉了"工作流通过服务调用时收到空输入"的 bug。

**过关题**：如果下一步要做 Agent Builder 界面，为什么必须先给配置加“工具白名单 + 权限分级”，而不是先把界面做出来？

**提交信息**：`feat(platform): add an agent builder UI`

### 9.3 后续阶段（按 v5 顺序，不跳步）

| 阶段 | 交付物 | 关键约束 |
|---|---|---|
| 7–8 Code Editing / Diff | `write_file` / `edit_file` / `git_diff` | 只做局部 patch，禁止让模型重写整个文件；改完必须能看到 diff |
| 9 Planning | `planner` 节点 | 计划必须进 State（不是只打印）：改哪些文件、为什么、什么顺序、怎么验证 |
| 10–11 Test / Debug | `test_tools.py` + 条件边 | 返回结构化结果（command / exit_code / stdout / stderr / passed）；`MAX_RETRIES = 3` 防死循环 |
| 12 Reviewer | `reviewer.py` | 只评审不改代码，输出 verdict + score + issues |
| 13 HITL | 图上的 `interrupt()` | 高风险动作（删文件、装包、执行命令）先暂停等批准 |
| 14–17 Trajectory / Experience | `trajectory` + `experience.py` + `coding_memory.py` | 记录 task / errors / attempts / test_result；经验先存 Store 或 SQLite，第二阶段再接 BGE-M3 + Chroma 做检索 |
| 18 Benchmark | `evals/` + 20~50 个任务 | 对比 Baseline 与 "+Experience" 的成功率、平均尝试次数、工具调用数、测试通过率 |
| 19–20 Sandbox / Docker | 隔离执行环境 | 先做路径限制 + git diff，再考虑 Docker / WSL2 / Worktree |
| 21 **Model Routing**（v5 新增） | `src/agents/model_router.py` | ✅ 验收 10/10：最高档只到 `deepseek-v4-flash`，只做记账 + 预算冻结升级（见 §4.22） |
| 22 **Agent 平台**（v5 新增） | `agent_config.py` + `declarative_agent.py` + `agent_workflow.py` + `agent_builder.py` + `agent_builder_app.py` | ✅ 验收 9/9 + 10/10 + 14/14：配置化 / 三种编排模式 / Builder 界面齐备，见 §4.23–§4.25 |

**明确不做**（v2 §29）：整体复制 Open SWE、接 Slack / Linear / GitHub App、做 Dashboard、做 QLoRA / KTO、复杂云 Sandbox、多 Agent 大拆分、一次加 20 个工具。

**v5 补充说明**：上面 21–22 两个方向**排在 Evaluation（18）之后**——v5 §40.6 明确要求"先有能跑通的 Coding Agent、Verification 与 Evaluation，再谈路由与平台化"。所以它们现在只作为架构设计记在 §3.7，**不影响阶段 13 起的实现顺序**。

---

## 10. 命令速查

```powershell
# 开发循环
git add <file>; git commit -m "feat(xxx): ..."; git push

# 同步上游更新（把本地提交重新叠到最新上游上）
git fetch upstream; git rebase upstream/main; git push

# 查看历史 / 差异
git log --oneline -10
git diff upstream/main --stat

# 服务探活与调用
Invoke-WebRequest http://localhost:8080/health
Invoke-RestMethod http://localhost:8080/info

# 查看服务日志
Get-Content D:\codex\working\logs\service.err.log -Tail 40
```
