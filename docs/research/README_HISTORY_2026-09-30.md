## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-09-25
- Verification Status: evaluation_2 DEV12 admission and one authorized probe pilot checked on 2026-09-29; trusted reproducer, repair efficacy, and independent generalization not demonstrated
- Version Label: E1-C current handoff v2

# E1-C 当前入口与下一道门槛

> **2026-09-29 更新：** 本页下方为 9 月 25 日历史快照。当前执行状态请先看 [Roadmap 2](../PROGRESS_RESEARCH_ROADMAP_2.md) 和 [evaluation_2 详细协议](E1C_CODING_AGENT_EVALUATION_2.md)：DEV12 官方 Base/Gold 双门槛 9/12、issue-only 自动定位输入 9/9。首次 probe pilot 用了 4 次调用、5,606 provider tokens；后续获授权 feedback pilot 实际只调用 1 次、2,013 tokens，随后因预算预留不足在第二次请求前封存。可选依赖诊断虽使旧 probe 补丁前失败可重复，Gold 区分却未通过，故 **trusted 0/12**。旧 canary、C5、Fresh30 未重新打开。

本页只做**当前入口和交接索引**，不复制逐轮流水。日期：2026-09-25。历史过程统一见 [集中日志](PROGRESS_LOG_ARCHIVE.md)；当前预注册协议见 [v4 canary 与 Fresh30 计划](E1C_BLIND_REPRODUCER_V4_PREREG_AND_FRESH30_PLAN_2026-09-25.md)；总体阶段见 [Roadmap](../PROGRESS_RESEARCH_ROADMAP.md)。旧版 `NEXT_SESSION_HANDOFF.md` 是 E1-B 历史交接，不是当前 E1-C 执行入口。

若按用户新增的**连题面内嵌断言也不消费**的严格口径继续，先读 [strict-blind DEV30→Fresh30 详细作业书](E1C_STRICT_BLIND_DEV30_TO_FRESH30_PLAYBOOK.md)：它是待实现的新协议分支，不代表 v4 已通过，也不改写 v4 的结果或 gate。

## 已核实的状态

| 层次 | 证据与结论 | 不能声称 |
|---|---|---|
| 原 E1-C 正式 30 题 | 1/30 official resolved，49 calls、65,801 provider tokens；之后同一批转 DEV | 不能把后续调参结果视为独立测试 |
| DEV 30 | v2.1 一次同版完整运行 4/30；跨版本逐题 best-of 13/30 | best-of 不是同版 13/30，更不是 30/30 |
| 盲态 B4/C4 | B4 baseline/structured 1/4 对 1/4；C4 baseline/treatment 0/6 对 0/6，12 calls、28,169 tokens，`expand_c5=false` | 不能说结构证据或 reproducer 已带来净增 official resolved |
| Reproducer v3/v4 | v3 最后 3 条 untouched unresolved DEV 零调用准入 0/3；v4 在这 3 条转为 contaminated 后零调用复现 3/3 | v4 3/3 不是 patch 成功率，也不是独立 canary |
| 独立 v4 canary / C5 / Fresh30 | canary 身份文件与结果均不存在；C5 结果不存在；Fresh30 30 个 slot 仍为空，`gate_ready=false`、`new_task_tree_touched=false` | 不能说新 30 已选题、准入或运行 |
| 其他实验 | Formal E1 Wave A 12 + Wave B 18 已执行并封存，合计 0/30 resolved（23/30 provider 基础设施失败）；原 E1-B 6 TEST 未执行但 fixture 保密性不再干净；E2 main 100 与 E3 未启动 | Formal E1 不是“未执行”，也不借 pytest 数量替代模型端到端结果 |

机器证据：C4 [result](../../.codex/e1c/e1c-blind-postb4-c4-v1/result.json)、v4 [零调用诊断](../../.codex/e1c/e1c-blind-reproducer-v4-dev-diagnostic-v1/result.json)、Fresh30 [预注册 30-slot plan](../../data/e1c_fresh30_v4_prereg_plan.json)。本次 focused v4/gate 回归为 **14 passed、4 warnings**；它只证明相应代码测试通过。此前两次独立全量回归分别为 **714 passed / 4 skipped** 和 **713 passed / 1 failed / 4 skipped**，后一失败是 Streamlit AppTest 冷启动 8 秒超时；两次不可合并，也不是修复率。

## “非公开断言、非人工定位”的严格定义与现存缺口

1. **信息盲态**：本交接按严格目标解释“非公开断言”——repair/model 只接触公开 issue 的自然语言需求、精确 base 源码与允许的非 oracle 元数据；不消费公开测试断言正文、题面内嵌的可执行断言、`test.patch`、隐藏测试、gold patch、official grade 或历史解答。现有 v4 `django_inline_issue_test_witness` 会从题面提取断言，**尚不符合这一严格口径**。新实验身份冻结前，须隔离/移除这一路径，并用自然语言合同或变形关系生成 probe，另以负面测试证明断言不会经 prompt、probe context 或 trace 流入 repair 侧；若改为允许题面断言，必须事先明示并改称较宽松协议，不能沿用本页的严格目标。
2. **零人工定位**：统一规则从允许的 issue/base 源码生成候选文件、结构关系和窗口，记录 top-k 命中、回退与文件读取预算；不允许任务 ID→文件表、人工挑文件、按已知 30 题加特例。旧 locator 在 DEV 30 上 30/30 有窗口，但只有 16/30 高置信路径，另外 14/30 词法回退；“有窗口”不等于正确定位。
3. **真实端到端成功**：在单一冻结代码/模型/配置身份下，每题自动生成候选 patch、通过盲态验证并由独立 official grader 判定 resolved；30 个任务全部入分母，失败/弃答/基础设施异常单列，不能跨版本 best-of。v4 的三类 Django witness 是面向已污染开发机制的实现，不足以证明跨 repo 通用性；目前最强的独立盲态模型结果仍为 C4 0/6。

“完美 30/30”是可检验目标，不是可以预先保证的交付日期或优化停止后自动成立的事实。即使 DEV 同版 30/30，也只能说明开发集表现；全新 Fresh30 一次性结果才提供独立泛化证据。

## 最短且可审计的后续顺序

1. **协议与代码身份冻结前的零调用工作**：按上述严格断言口径封堵题面内嵌断言路径，做 repair-side 数据流/trace 负面测试；审查 v4 witness 是否过度依赖 Django/已知任务；补充任务无关的自然语言合同、变形/属性 probe 与自动 top-k 定位质量审计。记录每一步输入来源，不改旧实验身份。先对现有 DEV 做零调用消融诊断，但只作为开发证据。
2. **独立 canary 身份先冻后读**：从外部官方元数据获取与所有既有 E1-C 身份不重叠的 3 条候选，仅使用 `instance_id/repo/base_commit/image` 冻结清单和哈希；随后才读取题面、base 树、官方镜像并做 Base-Fail/Gold-Pass。当前 Hugging Face 元数据访问出现 DNS 失败，真实 v4 canary manifest 尚未生成；不可把本地旧题改名为新 canary。
3. **零模型准入**：完成三题的盲态边界、reproducer 语义一致性、Docker/镜像、来源和 budget preflight。准入不过则停止；不得用同一 canary 反复改规则直到通过。
4. **一次预注册配对模型 canary**：在仓库 `AGENTS.md` 要求下，先向用户展示并取得**精确 live 命令**授权。只有 treatment-only official resolved ≥1、baseline-only=0 且无身份/安全/预算异常才开 C5；失败即保留负结果并另立新身份。
5. **C5 同版 DEV 30**：冻结规则、代码 SHA、模型、预算、manifest，一次完成 30 attempted / 30 official resolved 才满足当前 Fresh30 硬门槛。若达不到 30/30，报告真实失败分布并停止 Fresh30；可提出新版本与新独立 canary，但不能在旧身份上追逐 30/30 再把它当独立证据。
6. **Fresh30 新任务一次性测试**：只在前述 hard gate 打开后，从从未参与调参的官方元数据中先冻 30 条身份，再逐条 materialize exact-base 与官方镜像、完成 30/30 Base-Fail + 独立 Gold-Pass 准入；冻结协议/配置后 one-shot 运行，保留全部 30 条分母与审计轨迹。它现在**没有启动**。

执行脚本及 fail-closed 条件以 [v4 预注册计划](E1C_BLIND_REPRODUCER_V4_PREREG_AND_FRESH30_PLAN_2026-09-25.md) 和 `evals/e1c_fresh30_gate_v4.py` 为准，不从本页推断 live 命令已获授权。

## 工作区整理边界

本次只建立该索引，不移动、删除、重命名或覆盖现有源码、冻结文件、Docker 镜像和 `.codex/e1c/` 运行产物。检查时 `main` 在 `ad6426f`，已有 **11 个 tracked modified、326 个 untracked status entries**；其中含当前 v4 新代码/测试/计划，不能把这些未跟踪文件视为已提交、可复现的冻结身份。进入新 live run 前，应由维护者核对差异、分组提交或建立干净且已记录 SHA 的隔离工作树，并核查 `.codex/e1c/` artifact 哈希与备份；这一步不可通过清理命令自动完成。逐轮新过程只写入 [集中日志](PROGRESS_LOG_ARCHIVE.md)，此页和 Roadmap 只更新当前结论与入口。
