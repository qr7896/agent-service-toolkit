# AI Coding Agent 改造日志

> 基于 [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit) 的魔改项目
> 我的 fork：<https://github.com/qr7896/agent-service-toolkit>
> 最后更新：2026-09-15

---

## 0. 一句话现状

原项目（一个 LangGraph + FastAPI + Streamlit 的通用 Agent 服务骨架）已经在本地跑通，并且完成了两处真正的改造：**把 RAG 的向量模型从 OpenAI 换成完全本地的 BGE-M3**，以及**新增一个能自己查看代码仓库并给出带行号答案的 Coding Agent**。代码已推送到自己的 GitHub fork，历史干净（3 个提交）。

改造路线已升级到 **v3**（完整版见 [ROADMAP_v3.md](./ROADMAP_v3.md)，v2 见 [ROADMAP_v2.md](./ROADMAP_v2.md)）：整条路线拆成 21 个阶段（0–20），其中 **0–8 与 10 已完成**——阶段 6 `search_code` 验收 9/9（对照实验：工具调用 12→7、读取文件 9→4），阶段 7 `write_file` / `edit_file` 验收 11/11，阶段 8 `git_diff` 验收 8/8，阶段 10 `run_tests` 验收 9/9。参考仓库分工见 §3.3，每阶段过关题见 §3.4，v3 新增的可靠性原则与测试体系见 §3.6。

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

### 3.2 阶段表（对齐 v3 路线，共 21 个阶段）

> 完整版见 [ROADMAP_v3.md](./ROADMAP_v3.md)（v3 含十大顾虑与测试体系）；[ROADMAP_v2.md](./ROADMAP_v2.md) 保留为上一版对照。

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
| 9 | Planning | `src/agents/coding_agent.py` | Graph Routing | ⏳ |
| 10 | `run_tests` | `src/agents/test_tools.py` | Execution | ✅ 验收 9/9 |
| 11 | Debug Loop | `src/agents/coding_agent.py` | Conditional Loop | ⏳ |
| 12 | Reviewer | `src/agents/reviewer.py` | Subgraph / Agent | ⏳ |
| 13 | HITL | Graph | `interrupt()` | ⏳ |
| 14 | Trajectory | `trajectory` | Evaluation | ⏳ |
| 15 | Experience Memory | `src/agents/experience.py` | Store | ⏳ |
| 16 | Experience Retrieval | `src/agents/coding_memory.py` | RAG + Memory | ⏳ |
| 17 | Self-Correction | Graph | Experience-guided loop | ⏳ |
| 18 | Benchmark | `evals/` | Agent Evaluation | ⏳ |
| 19 | Sandbox | 后期 | 安全执行 | ⏳ |
| 20 | Docker | 后期 | 工程化 | ⏳ |

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
| `src/agents/coding_agent.py` | **新增** | 代码问答 Agent（异步图，目前接只读工具 + run_tests） |
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

### 5.3 本地数据（不进版本库）

| 路径 | 说明 |
|---|---|
| `D:\codex\working\models\bge-m3` | 本地向量模型（约 2.1 GB） |
| `src/chroma_db` | 向量库（3 个 chunk） |
| `src/checkpoints.db` | 会话记忆（SQLite） |
| `D:\codex\working\logs` | 服务与前端运行日志 |
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
- [x] 3 个提交推送到自己的 GitHub fork，且已 rebase 到上游最新

### 7.2 已知限制 / 待办

- [ ] 工具只能读，不能写（`write_file` / `edit_file` 未实现）
- [ ] 没有规划（Planning）：模型直接开查，不会先给"我要改哪些文件"的计划
- [ ] 没有测试循环（跑测试 → 失败 → 自修复）
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

### 9.1 已完成（阶段 6–8、10）

- **阶段 6 `search_code`**：验收 9/9，对照实验数据见 §4.7
- **阶段 7 `write_file` / `edit_file`**：验收 11/11，设计见 §4.8
- **阶段 8 `git_diff`**：验收 8/8，设计见 §4.8
- **阶段 10 `run_tests`**：验收 9/9，设计与过关题回答见 §4.9

### 9.2 当前任务（阶段 9）：Planning

**目标**：让 Agent **先出计划、再动手**——把"改哪些文件、为什么改、什么顺序、怎么验证"变成 State 里的结构化数据，而不是只打印给用户看。

**第一版必须支持**：

- 新增 `planner` 节点（可先放在 `coding_agent.py`，规模变大再拆 `coding_planner.py`）
- 计划输出为**结构化字段**并写入 State（新增 `plan` 字段），能在 `ainvoke` 的结果里读到
- 计划必须包含四要素：**要改的文件 / 每个文件为什么改 / 修改顺序 / 如何验证**
- 图结构变为：`START → planner → model(coder) → tools → model → ...`
- planner 阶段允许调用只读工具（`search_code` / `read_file` / `list_files` / `git_diff`）先把情况看清
- 缺信息时要显式说明"还需要确认什么"，而不是硬编一个计划

**验收标准**：

- [ ] 给一个需求，`ainvoke` 结果里存在 `plan` 字段
- [ ] `plan` 四要素齐全（文件 / 原因 / 顺序 / 验证方式）
- [ ] 计划先于任何执行动作（planner 不调用写工具）
- [ ] planner 能调用只读工具补充上下文
- [ ] 需求含糊时，计划里出现明确的待确认项
- [ ] 计划内容与实际仓库结构一致（引用的文件都真实存在）

**过关题**：Planner 的输出为什么应该进入 State，而不是只打印给用户？

**提交信息**：`feat(coding): add coding planner`

### 9.3 后续阶段（按 v3 顺序，不跳步）

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

**明确不做**（v2 §29）：整体复制 Open SWE、接 Slack / Linear / GitHub App、做 Dashboard、做 QLoRA / KTO、复杂云 Sandbox、多 Agent 大拆分、一次加 20 个工具。

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
