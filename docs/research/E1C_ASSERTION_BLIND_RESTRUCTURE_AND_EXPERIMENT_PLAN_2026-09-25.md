# E1-C 盲态重整与实验安排（2026-09-25）

状态：**原计划已冻结；2026-09-25 已实际执行至 B4，并按预注册停止条件封板。以下 §1–§6 保留原计划语义，执行结果只追加在 §7，不用事后结果改写准入规则。** 当前事实和逐轮记录分别见 [Roadmap](../PROGRESS_RESEARCH_ROADMAP.md) 与 [集中日志](./PROGRESS_LOG_ARCHIVE.md)。现有 30 题是反复调参的 DEV；跨版本逐题 best-of 13/30，不是同版 13/30。**B4 结果不支持扩展到 B5/B6；30/30 仍只是历史开发目标，不是结果或承诺。**

## 1. 核心问题与边界

上一轮 v5.0 把 `test.patch` 的新增断言加入模型证据，3 题、6 次调用、0 新解。v1 定位器读取官方 base-fail 日志；v2 还使用 `FAIL_TO_PASS` selectors 和失败测试 import。它们对现有 DEV 的诊断有价值，但不符合“模型未见新增测试”的盲态实验。30/30 有窗口、20/30 有明确候选路径只表示**证据覆盖**；Sphinx9230 的覆盖探针也只能提示执行路径失配，不能给出故障真值。

本路线的盲态定义是：修复端只能看 issue statement、精确 base 版本的仓库及其中原本存在的测试，以及它自己在 base 上按统一规则生成/运行的探针。不能看到 benchmark 的 `test.patch`、`FAIL_TO_PASS`/`PASS_TO_PASS` 选择器、官方 Base-Fail/grade 日志、gold patch、历史 DEV 候选/失败反馈；也不能用任务 ID、手工路径表或已知答案来选文件。准入/评测端可以持有这些 oracle 材料，但必须与修复端物理隔离，最终判分只作一次性评测结果，不能回流到同次修复决策。

这只能控制**运行时信息泄漏**；不能消除模型预训练可能见过公开 issue/仓库的污染。独立批次仍要报告来源、时间和这一限制。

## 2. 重整组件：复用、改造、隔离

| 现有部分 | 处理 | 理由与验收 |
|---|---|---|
| exact-base 物化、安全路径 guard、SHA 锚定编辑、预算账本、官方 Docker grader | 复用为底座；grader 留在隔离评测侧 | 源身份、预算、无模糊编辑与最终权威判分仍必要；修复侧不得读 grader artifact。 |
| v1 `e1c_failure_guided_evidence.py` | 拆出只依赖 issue/base 的词法、AST 窗口部分；禁用官方 base-fail 输入 | 从盲态输入生成路径/符号候选，保留 origin、rank、窗口行号、源码 SHA；无候选时 abstain。 |
| v2 `e1c_failure_guided_evidence_v2.py` | 不能原样接入盲态 runner | 当前测试路径发现依赖 base 日志与 `FAIL_TO_PASS` selectors；只能重写为从原有测试目录/issue 自行发现，不得消费新增测试。 |
| v5.0 `e1c_public_test_evidence.py` 和既有 DEV outcome/patch 库 | 盲态推理侧禁用，仅留历史诊断 | 不把公开新增断言或旧候选改名后当“自主定位”。 |
| CodeGraph/AST/词法/语义检索、已有测试运行与受控 ACI | 经输入审计后按需复用 | 所有 query 从 issue、base 源码或盲态自生成失败派生；记录 provenance 和读取成本，不按 task ID 配置。 |
| 自动缺导入/候选合并 | 仅作通用、可证明安全的候选后处理 | 不用旧 DEV patch 作素材；每次修改仍要过原 base 精确命中、安全 guard 与回归。 |

## 3. 固定的任务无关修复链

1. **合约提取**：从 issue 生成独立可检查的行为义务（输入、输出、边界、应保持的不变量）；标记题面不足之处，不凭空补 hidden-test 预期。
2. **预补丁复现**：在原 base 上用固定模板生成最小复现/属性/变形测试，冻结探针文本与 SHA，记录“确因题面所述行为而失败”的可重复证据。若不能构造有效复现，记 `no_reproducer`，转保守的 issue+源码检索；不能伪造成功复现。
3. **独立审计探针**：用不同生成种子/模板（必要时不同模型角色）在补丁前生成并封存少量互补检查。修复模型不能看其源码或结果；审计探针只用于候选选择，不成为下一轮提示。任何生成测试都不是官方真值。
4. **定位**：把 issue 符号、原有测试、盲态复现 traceback/覆盖、AST 定义/调用/导入关系合成有 provenance 的候选路径和短源码窗口。覆盖仅用于过滤或排序，不能直接宣称 bug location；定位无充分证据时 abstain。
5. **编辑/验证**：只允许原 base 已展示路径上的 exact-range/hash-anchored 编辑；拒绝模糊替换、测试文件/保护路径写入。每个候选按固定顺序跑解析/lint、复现、原有回归、封存审计探针，记录 patch hash、失败类型与成本；没有有效候选时明确失败而非空补丁冒充完成。
6. **最终评测**：冻结候选与 trace 后，隔离端才运行官方 grader。其输出可供 DEV 轮后诊断，但不得反向改变该轮补丁、定位窗口或同一身份中的选择。

## 4. 阶段、入口门槛与实验

| 阶段 | 工作与最小交付 | 通过/停止门槛 | 模型/官方测试 |
|---|---|---|---|
| B0 口径封板 | 冻结 30 DEV 清单、历史身份、污染源清单；新建修复端 allowlist 和评测端 denylist | 历史 formal/DEV/best-of 口径不变；E1-B sealed、E2 不混入 | 0/0 |
| B1 信息隔离 | 实现 agent-view 投影、两侧独立 artifact 目录/权限和泄漏单测；对 `test.patch`、selectors、官方日志、gold、旧 patch 注入哨兵 | 哨兵 100% 被修复侧拒绝；prompt/工具输出/trace 无 oracle 字段；不影响官方准入/判分 | 0/0 |
| B2 复现与定位 | issue 合约、预补丁探针、`no_reproducer`、短窗口与 provenance；合成跨库用例、DEV 离线审计 | 同输入确定性、生成测试先在 base 跑、错误归因可审计；无手工 task→path；abstain 可观测 | 优先零调用；若生成器需要模型，另冻身份 |
| B3 安全闭环 | 接 exact edit、预算、现有测试与封存审计探针；保留官方 grader 隔离 | 源身份/越权/重复 patch/超预算/ambiguous 请求 fail-closed；focused+完整非模型回归如实报告 | 0 provider；合成验证可用本地测试 |
| B4 小样本对照 | 从历史 17 条未解 DEV 中按原 manifest 顺序预选前 4 条，披露 outcome-selected 性质；跑同模型/同修复预算的简单盲态基线与“+复现/结构化定位”臂，额外生成成本单列 | 至少能产出可审计定位、有效补丁/abstain 和官方结果；若实验臂无净新 resolved 或安全/预算异常，停下归因，不扩批 | 付费前独立预检与**精确命令授权** |
| B5 同版完整 30 DEV | 仅在 B4 说明新机制确有净收益后，冻结软件、prompt、模型、预算、选择规则和 SHA；一次完整运行 30 条 | 报同版 30 题 resolved/attempted、调用/已知与未知 tokens、定位证据、错误分类；历史 best-of 只作旁注 | 付费 + 官方 grade，不能逐题改协议 |
| B6 未见任务 one-shot | 在看新任务题面前冻结 protocol 和 cohort 选取/替补规则；排除一切已开发/已准入/已物化的任务与 E1-B sealed TEST，零模型 admission 后一次运行 | 不因结果挑任务、不重跑调参；报告完整分母、失败、成本及与 B5 差距。若污染/资源/协议失败则停，不能宣称独立泛化 | 另立精确命令和预算，不沿用 B5 授权 |

B4 建议采用低成本顺序：先 4 题配对、每修复臂每题至多 2 次请求；生成探针的调用另计。**具体 provider-token 单题/整批软硬上限、模型输出上限、镜像与命令在 B3 预检后单独冻结**，不能把旧 v2.1 弹性额度自动当成本路线的限额。任何 provider ambiguous/超限请求保留账本、停止自动重试，未知计费单列。若 B4 失败，优先零调用失败归因与缩小机制，不靠同质付费重抽。B5 的“30/30”只有该同版完整运行达到才能写；未达到也照实结束并进入下一决策，不以无限迭代为停止条件。

## 5. 指标与消融口径

- **主要结果**：每个冻结身份的官方 resolved / attempted，含有效 grade 与安全/基础设施/预算失败分层；B6 为唯一新任务泛化检查。
- **定位诊断**：窗口/路径候选覆盖、abstain、执行覆盖与来源、最终 patch 路径命中；仅在轮后用隔离真值作回顾评估，不进 prompt。覆盖率不等于定位准确率。
- **复现诊断**：有效预补丁失败比例、`no_reproducer`、复现与审计探针一致性、候选对原有回归的影响；生成测试 pass 不等于官方 resolved。
- **成本/可靠性**：provider completed/ambiguous 请求和已知/未知 tokens、生成器额外成本、Docker grade 次数、无效编辑/重复 patch、越权阻断、总耗时。
- **必要对照**：简单盲态基线、+issue-derived 复现、+trace/结构化定位、+独立审计探针。消融用同 cohort/同模型/同修复预算；组件增量成本单列，不把历史 v5.0 结果直接当配对对照。

## 6. 当前可立即执行的零调用待办

1. 写 `agent_view`/`evaluator_view` 数据契约与泄漏测试；证明旧 v1/v2/v5.0 不能意外作为盲态输入。
2. 只从 issue/base/original tests 建一个最小复现与定位原型；先用合成案例和 4 条预选 DEV 做离线回放，不看官方 grade 反馈选路径。
3. 接入现有 exact-edit、预算、异常账本；运行 focused 与完整非模型回归，保持 Streamlit 全量时限失败单列。
4. B3 通过后发布 B4 的冻结配置、精确运行命令、上限和停止规则，再决定是否支付模型调用。

参考实现方向：[AutoCodeRover](https://arxiv.org/abs/2404.05427) 的结构/运行时定位、[Agentless](https://github.com/OpenAutoCoder/Agentless/blob/main/README_swebench.md) 的定位→修复→验证分层、[SWT-Bench](https://arxiv.org/abs/2406.12952) 的生成测试筛选。它们是设计参考，不是本项目的效果证据。

## 7. 2026-09-25 执行结果（post-run addendum，不改写原预注册）

- B0/B1：repair/evaluator information boundary 已实现；oracle/test.patch/selectors/official log/gold/历史 patch-outcome sentinel fail-closed。
- B2/B3：issue + exact-base source excerpt 的 blind locator、SHA provenance、bounded exact-edit 与 provider ledger 已接入；B4 封板后又以**零调用**补齐 issue contract、original-test probe / `no_reproducer`、AST definition provenance 与 deterministic evidence freeze。该 post-run 工程补齐不进入 B4 效果比较，也没有触发重跑。blind 专项最终 28 passed，Ruff clean；全量非模型回归最终 703 passed / 4 skipped / 33 warnings。
- B4：final admitted manifest 前 4 条做 baseline/structured 配对，共 8 provider calls、15,277 tokens、0 over-budget。Baseline=1/4 resolved；Structured=1/4 resolved；net new=0；lost=0。
- structured arm token=8,912，baseline=6,365；两条产生 patch 的任务在两臂 patch SHA 完全一致，因此本轮没有观察到 structured evidence 带来的 patch 或 official resolved 增量。
- **预注册停止条件触发：`expand_b5=false`。B5 30 DEV 与 B6 unseen one-shot 均未运行，也不应在本身份下继续扩批。**
- 该结论只适用于 outcome-selected 的 4-task DEV canary；不能解释为 structured localization 普遍无效，也不能作为独立泛化、统计显著性或 30-task Autonomous Repair Rate 证据。
- **样本选择偏离与干预限定（后验审计）：** 上文 B4 表格写“17 条历史未解中前 4”，实际 `e1c_blind_runner._canary_rows()` 和冻结 identity 使用 final manifest 前 4 条，包含已有历史解的 pytest-5631；因此不能把 1/4 当作未解题 canary 的估计。实际 structured 臂只把同一个词法检索器的窗口上限由 2 增到 4；合约/原有测试探针/AST provenance 是 B4 后的零调用补充，未进入该对照。原结果与停止规则保留，不事后改写。后续机制与新 30 题门槛见 [B4 后优化计划](./E1C_BLIND_POST_B4_OPTIMIZATION_AND_FRESH30_GATE_2026-09-25.md)。
