# Coding Agent 研究总览：成果、证据与边界

更新：2026-10-09。本文是项目总览；当前可执行待办只维护在 [Roadmap 2](PROGRESS_RESEARCH_ROADMAP_2.md)。

本项目基于 [JoshuaC215/agent-service-toolkit](https://github.com/JoshuaC215/agent-service-toolkit)，在 LangGraph、FastAPI、Streamlit 服务骨架上研究：**如何以受控成本获取代码证据，并让自动生成的故障复现真正支持软件修复？**

**当前：** [两来源issue-first新生成链](research/E1C2_FRESH_PAIR_RESULTS_2026-10-09.md)已按精确授权执行：Flash4calls/39,970tokens，配对执行门槛2/2，原冻结official修复**1/2**。Marshmallow新patch F2P1/1、P2P37/37；Scikit-learn原schema拒绝，独立零调用精确元字段解码后F2P1/1、P2P19/19。**两个库有官方通过补丁证据，但不是同版冻结2/2、30/30或独立泛化；full_issue_trusted仍false。**

新生成仅用fresh公开issue/自动生产窗口与自产probe反馈，不输入旧成功patch或官方答案；定位来源为前次零调用冻结产物。paid/zero原记录字节保全，无retry。下一步正式接通用精确兼容codec、补公开行为义务缺证、再冻结同版DEV12/九准入；不启用canary/TEST/Fresh30/E2。前次[单例成功/21合成变体](research/E1C2_COMPLETION_SUCCESS_2026-10-09.md)保留，不合并成新成绩。

此前2.19.3公开包对照与[原结果](research/E1C2_RELEASE_WITNESS_RESULTS_2026-10-08.md)/[原收据](../data/e1c_evaluation_2_release_witness_results.json)不改。**旧严格完整可信仍0；新两来源原系统1/2、后验另1/1，研究仍未完成**。不因official通过回填namespace意图/全部义务或旧repair_eligible，不拼多版最佳率。

所有旧分数、输入、源码、观察与失败保留；不将“候选”叫可信2/4，不best-of或改旧namespace。日志只在[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)，下表保留历史版本。

最新工程验证：1769 passed/4 skipped/33 warnings（65.46秒）；3新增审计专项/组合10/重点37/Ruff/合成compact preflight通过。[最新结果收据](../data/e1c_evaluation_2_fresh_pair_results.json)绑定paid/zero/seal/XML。[新链原readiness](../data/e1c_evaluation_2_fresh_pair_readiness.json)、[前次成功收据](../data/e1c_evaluation_2_completion_success.json)和旧XML不改；工程数不是可信复现或修复率。

## 1. 阅读入口

| 读者目的 | 入口 |
|---|---|
| HR / 工程师 / AI 快速了解项目 | 本页第 3、4 节 |
| 接手下一步开发与实验 | [Roadmap 2](PROGRESS_RESEARCH_ROADMAP_2.md) → [WebCodex 交接](research/NEXT_SESSION_HANDOFF.md) |
| 查看一周交付和验收 | [一周实验计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md) |
| 查原始过程、失败与演变 | [历史索引与保全记录](research/WORKSPACE_REORGANIZATION_2026-09-30.md) |
| 查看最新实验与下一步 | [两来源新生成/原成绩与零调用分账](research/E1C2_FRESH_PAIR_RESULTS_2026-10-09.md)；所有旧协议/负结果保留 |

## 2. 从启动到现在的主线

| 阶段 | 做了什么 | 现在如何理解 |
|---|---|---|
| 8 月末—9 月上旬：工程基线 | 服务；本地 BGE-M3；代码搜索、读写、测试；Planning、Reviewer、HITL；轨迹与经验；配置和工作流 | 已有实现和分项验收，不能等同于研究全部完成 |
| V0：规则证据获取 | 受控检索任务、Utility Gate 与静态策略比较 | 检索层原型收尾，不是自动修复率 |
| V1：学习排序与停止 | Decision Episode、LogReg ranker/stopper、冻结划分、动作消融 | 已冻结，小样本检索效率改善，未证明修复增益 |
| V2：扩展检索评估 | adaptive acquisition、SERBench Cal500 与 Test500 prediction-ready | 已冻结；Cal500 未优于词法基线，Test500 未获私有评分 |
| V3：经验复用 | 时间顺序隔离、6 条真实轨迹、3 组 OFF/ON 对照 | pilot 关闭；未观察到修复收益 |
| 9 月 20–23 日：Formal E1 / E1-C | 外部任务准入、预算账本、容器评分、完整实验封存 | Formal E1 0/30；原 E1-C 最终 1/30 |
| 9 月 24–27 日：DEV30 与严格复现 | 同版开发、盲态配对试验、source-contract、失败归因 | best-of 不作系统成绩；独立门槛失败暴露复现覆盖不足 |
| 9 月 28–30 日：evaluation_2 | DEV12 镜像、双准入、自动源码窗口、离线判别、独立 canary | 当前活动主线，详见 Roadmap 2 |

原文中“全部阶段已完成”只适用于当时的基础工程验收。E1-C 质量目标、E2 main、E3 并未完成。

## 3. 本分支的实质工作

上游提供 Agent 服务、客户端、UI 和基础框架。以下是本分支的研究与工程扩展；不将整个上游项目算作原创。

| 能力 | 实现 / 结果入口 | 可以支持的陈述 |
|---|---|---|
| 受控代码工具 | [code_tools.py](../src/agents/code_tools.py)、[test_tools.py](../src/agents/test_tools.py) | 路径、读取量、执行超时等边界 |
| 规划、审查与轨迹 | [coding_planner.py](../src/agents/coding_planner.py)、[reviewer.py](../src/agents/reviewer.py)、[trajectory.py](../src/agents/trajectory.py) | 可记录决策和失败轨迹 |
| 经验存储与复用 | [experience.py](../src/agents/experience.py)、[V3 结果](research/RESULTS_V3.md) | 已实现并做过真实小型对照；效果未获支持 |
| 统一证据接口 | [evidence_runtime.py](../evals/evidence_runtime.py)、[evidence_controller.py](../evals/evidence_controller.py)、[codegraph_adapter.py](../evals/codegraph_adapter.py) | lexical / semantic / structural、预算与 STOP 可追踪 |
| 学习型检索策略 | [V1](research/RESULTS_V1.md)、[V2](research/RESULTS_V2.md) | 冻结划分、检索成本指标、消融 |
| 请求预算与账本 | [model_budget.py](../src/agents/model_budget.py) | token 预留、硬上限、失败记账与中断边界 |
| 离线缺陷评测 | [evaluation_2](research/E1C_CODING_AGENT_EVALUATION_2.md)、[冻结清单](../data/e1c_evaluation_2_canary_v2_method_freeze.json) | 生成侧/grader 隔离、镜像/源码身份、固定分母、失败留档 |

研究假设：**固定 issue 的可观测行为约束，并限制执行反馈只能修正环境或构造过程，能否减少“测试失败但与 issue 无关”的假阳性？** 现有失败记录支持这个研究动机；效果与新颖性仍须通过消融和独立验证，不能提前称为已验证的新算法。

## 4. 已有结果与统计口径

| 实验 | 结果 | 限制 / 证据 |
|---|---|---|
| V1 frozen test，4 tasks | Recall 0.7812；tokens 122.5 → 87.0；tool calls 2 → 1.25 | 小型检索实验；[报告](research/RESULTS_V1.md) |
| V2 SERBench Cal500 | MSS@8 0.078；BM25 0.104；lexical 0.118 | 未胜出；[报告](research/RESULTS_V2.md) |
| V3 exploratory pilot | 6 trajectories；3 组 OFF/ON 结果相同；ON 多 369 tokens | 未观察增益；[报告](research/RESULTS_V3.md) |
| Formal E1 | 0/30 resolved；23 provider 基础设施失败 | 不能归因成纯模型能力；[汇总](../data/formal_e1_n30_summary.json) |
| 原 E1-C | 最终 1/30；49 requests；65,801 provider tokens | 含 selective salvage；[报告](research/E2_ENTRY_GATE_STATUS_2026-09-23.md) |
| 旧 DEV30 | 一次同版完整运行 4/30；跨版 best-of 13/30 | 不可相互替代；[历史](PROGRESS_RESEARCH_ROADMAP_2_HISTORY_2026-09-30.md) |
| B4 / C4 | B4 1/4 对 1/4；C4 0/6 对 0/6 | 没有 treatment 净新增修复；[历史](PROGRESS_RESEARCH_ROADMAP_HISTORY_2026-09-30.md) |
| evaluation_2 DEV12 | 双准入 9/12；v4 经审核可信复现 4/12 | 8 请求 / 25,424 tokens；含确定性路由；不是修复率 |
| canary v1 | 可信复现 1/3，低于 ≥2/3 | 独立负结果封存；[结果](research/E1C2_INDEPENDENT_CANARY_V1_RESULT_2026-09-29.md) |
| canary v2（传输修订） | 官方双准入3/3；可信复现0/3 | Flash三请求/13,783 tokens；输出回显、fixture错误和弃答；[负结果](research/E1C2_CANARY_V2_AMENDED_RESULT_2026-10-05.md) |
| DEV合同/控制器改进 | 新生成hybrid 3/12；修订控制器缓存4/12 | 开发证据，含语义审核；A/B、失败、成本分开报告；[结果](research/E1C2_DEV_CONTRACT_STUDIES_2026-10-05.md) |
| 独立hybrid canary v3 | 双准入2/3；可信1/3，未达门槛 | 3Flash请求/7280tokens，负结果封存；[报告](research/E1C2_HYBRID_CANARY_V3_RESULT_2026-10-05.md) |
| 最新旧DEV hybrid v3 | 新生成可信3/12，门槛失败 | 12Flash请求/24712tokens，未保留四条参考；[报告与下一步](research/E1C2_HYBRID_DEV_V3_RESULT_2026-10-05.md) |
| counterfactual旧DEV新生成 | 13Flash请求/26762tokens，Gold及人工行为审查4/12 | 保持四条参考，零调用先拒错误fixture；不是SOTA或修复率；[报告](research/E1C2_COUNTERFACTUAL_DEV_RESULT_2026-10-05.md) |
| 第4批独立canary | 双准入2/3，3Flash请求5596tokens，可信0/3 | 环境失败/窗口缺失/输入dtype丢失；[封存结果](research/E1C2_COUNTERFACTUAL_CANARY_V4_RESULT_2026-10-06.md) |
| Faithful input旧DEV | 源生成16Flash请求37593tokens；原验证INFRA_INVALID保留 | 不把环境故障记0/12；[原结果](research/E1C2_FAITHFUL_INPUT_DEV_RESULT_2026-10-06.md) |
| Faithful完整缓存回放 | 新provider0；9题执行、6候选、Gold5/12，四参考保留 | 人工行为审查5/12、机器trusted0，不是独立/修复；[结果](research/E1C2_FAITHFUL_REPLAY_RESULT_2026-10-06.md) |
| 第5批独立canary | 双准入2/3；3Flash请求9642tokens，可信0/3 | import/API窗口遗漏、未调用函数、源码身份失败；[封存结果](research/E1C2_FAITHFUL_CANARY_V5_RESULT_2026-10-06.md) |
| 旧DEV import/调用形态审计 | 新provider0；3题4个新增定义窗口，8份缓存候选中1份函数体未调用 | 结构诊断原型，不是新的复现分数；下一版DEV尚未付费 |
| 新版executable-import旧DEV | v1零调用原型保留；v2能力边界加固后真实试验3/12 | 不代表净提升；[协议/历史](research/E1C2_EXECUTABLE_IMPORT_DEV_V2_PROTOCOL_2026-10-06.md) |
| Executable新生成V2 | 12请求36689tokens；4候选Gold3/12 | 未保四参考；[真实结果](research/E1C2_EXECUTABLE_DEV_V2_RESULT_2026-10-06.md) |
| Controller-owned缓存V3 | 新provider0/无缺缓存；仍Gold3/12 | 输入echo仍拒绝，没有新模型收益 |
| Controller generation V4 | 14请求35889tokens；A源码格式5/5，5候选Gold2/12 | 格式改善、质量未提升；[真实负结果](research/E1C2_CONTROLLER_GENERATION_V4_RESULT_2026-10-06.md) |

DEV v4 底层 Gold 判别 JSON 中，4 份 `gold_discriminating=true`，而 `trusted_reproducer` 仍为 false。4/12 叠加了文档中的人工 issue 语义审核，不能说机器自动判可信，也不应回填旧 JSON。自动定位不等于完全自动语义验收。

工程测试结果见[验证记录](research/WORKSPACE_REORGANIZATION_2026-09-30.md)。pytest passed 数不代表 repair success。

## 5. E1、E2、E3

| 研究线 | 状态 | 下一条件 |
|---|---|---|
| E1 / E1-B | 正式结果封存；旧六条 TEST 未执行但保密性受损 | 旧六条不再作干净确认集 |
| E1-C evaluation_2 | 活动中，尚无新版 Agent 修复结果 | 独立 canary ≥2/3，再冻结修复对照 |
| E2 | operational Entry Gate 曾 PASS；main n=100 未启动 | 先满足新质量门槛；运行完整不代表质量达标 |
| E3 | 路线规划，未启动 | E2 后另立 30 → 100 → 300+ 与提前停止协议 |

## 6. 历史保全与维护

完整旧正文保存在同目录，原相对链接继续有效：

- [旧 Roadmap 全文](PROGRESS_RESEARCH_ROADMAP_HISTORY_2026-09-30.md)
- [旧 Roadmap 2 全文](PROGRESS_RESEARCH_ROADMAP_2_HISTORY_2026-09-30.md)
- [集中日志](research/PROGRESS_LOG_ARCHIVE.md)与[9 月 27 日续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)

以后只更新本页项目结论、Roadmap 2 当前状态；逐轮过程写集中日志。旧 freeze/result、失败记录、源码保持原路径。本地密钥、原始任务/评分材料和大文件缓存不作为公共展示材料。本轮整理不触碰 Docker 数据盘或 tunnel 配置。
