# E1-C 盲态 B4 后优化与全新 30 题门槛（2026-09-25）

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: plan
- Origin Date: 2026-09-25
- Verification Status: PARTIALLY VERIFIED（C0–C4 已执行；C5/C6 因预注册 gate 未通过而未启动）
- Version Label: e1c-blind-post-b4-plan-v1

## 1. 已核对的现状

本计划接续 [原盲态 B0–B6 协议](./E1C_ASSERTION_BLIND_RESTRUCTURE_AND_EXPERIMENT_PLAN_2026-09-25.md)，**不修改 B4 旧身份、结果或停止规则**。原 E1-C 正式完整运行 1/30；同题 DEV v2.1 完整运行 4/30；跨身份逐题 best-of 13/30，不是一次运行。Formal E1 n=30 和 E1-B 6 条 TEST 保持原 sealed 边界。E2 main n=100、E3 均未启动。

盲态 B4 身份 `e1c-blind-canary-v1` 的 `result.json` 与 provider ledger：4 题×2 臂、8/8 completed calls、15,277 provider tokens、0 over-budget；baseline=1/4，structured=1/4，net new=0，lost=0，`expand_b5=false`。两题双臂 abstain；另两题出 patch，但各题两臂 patch SHA 相同。structured 用 8,912 tokens，baseline 用 6,365（+2,547，约 +40%）。因此 B4 **已按自己的停止规则封板**，不能把它续跑成 B5，也不能称 blind 30-task repair rate。2026-09-25 专项测试重新核对为 28 passed / 4 warnings；文档记录的最近全量非模型回归是 703 passed / 4 skipped / 33 warnings，本文未再跑全套。

**协议偏离须透明披露：** 原 B4 计划表写“从历史 17 条未解 DEV 中按 manifest 顺序选前 4”，但实际 runner 的 `_canary_rows()` 使用 final manifest 的**前 4 条**，其中 `pytest-dev__pytest-5631` 已有历史解。实跑 identity 固定了这 4 条并可复现；但不能称样本选择严格符合那一行预注册描述，也不能用 1/4 推断 17 条未解任务的成功率。后续新 canary 必须在调用前让计划、selector 代码、identity 三者一致。

**B4 实际干预很窄：** `e1c_blind_runner.blind_payload()` 的 structured 臂仍调用同一个 `e1c_evidence_v2.excerpts()`，只是把最多 2 个词法窗口改为最多 4 个；它没有消费 original-test probe、issue contract 或 AST definition provenance。后者在 B4 后才加入 `e1c_blind_evidence.py`，目前 `freeze_blind_evidence()` 未被 blind runner 调用；`discover_original_test_probes()` 只排名已有测试文件，**还没有实际执行测试或生成稳定失败复现**。因此 B4 只能反驳“更多同类词法窗口在这 4 题带来收益”，不能反驳完整的复现/结构化定位路线。

边界实现也尚需加固：`AgentView` / `assert_agent_path()` 目前主要由单测使用，runner 未调用；repair 与官方 `grade()` 仍在同一 Python 进程中。现有字段/路径/trace guard 降低意外泄漏风险，但不能等同于物理隔离或对任意内容的泄漏证明。下一轮要把**实际运行路径**纳入审计，不能只看哨兵单测。

资源快照：Docker Linux engine 29.8.0 当前可连接，41 镜像约 63.49 GB，D: 可用约 41.8 GiB。全新 30 题的镜像准入可能受磁盘与下载限制；不自动 prune 现有镜像或删除实验资产。

## 2. 研究问题与可证伪假设

研究问题：在修复端**完全不读取 benchmark 新增断言/官方失败日志/历史答案**、不按 task ID 人工选文件的条件下，真实执行的 issue→原有测试/自生成复现→结构化源码定位→受控编辑/验证链，能否比同预算的简单盲态基线提高**同一运行身份**的官方 resolved，同时控制额外 token 与安全失败？

假设 H1（待检验）：有稳定的 pre-patch issue-derived 失败复现时，失败栈/覆盖与 AST 定义/调用关系可以改善候选源码排序；其效果要通过实际 patch/official resolved 而非窗口覆盖数判定。假设 H2：在相同修复调用上限下，有界 inspect→edit 比一次给更多静态窗口更能减少 `abstain`、`invalid_edit`。生成测试/覆盖只能作证据和候选筛选，不是 hidden-test 真值。

## 3. 下一轮优化顺序与硬门槛

| 阶段 | 任务无关改动 | 零调用/付费验证与门槛 |
|---|---|---|
| C0 结果与泄漏审计 | 冻结 B4 ledger、identity、patch/grade hash；记录上述样本选择偏离。让 runner 真正通过 `AgentView` 读取 exact-base，所有文件访问走 allowlist；修复端与评测端分目录、分进程，评测输出在候选冻结前不可读。 | 零调用：恶意 oracle 文件名、字段、文本和路径穿越的端到端哨兵；prompt、工具输出、修复 trace 均无 benchmark 新增测试/官方日志/历史结果。失败即停。 |
| C1 可执行复现 | 从 issue 合约和原有测试自动选运行目标；在补丁前运行，记录命令、环境、失败类型和 SHA。只有可重复且与题面相关的失败才是 reproducer；否则显式 `no_reproducer`。自生成探针在补丁前冻结，另留独立审计探针。 | 零调用先做合成案例/已有 DEV 离线测试；不把 official Base-Fail 或 `test.patch` 反向当作生成器输入。不得把“找到测试文件”写成“复现成功”。 |
| C2 真结构化定位 | 将 C1 的**盲态** traceback/覆盖与 issue AST 符号、定义/调用/导入关系融合，输出 `path, symbol, range, origin, depth, source_sha, abstain_reason`；允许至多一次有界 inspect 请求补证。 | 用同一组任务比较 top-k 候选与后验目标路径、`abstain`、窗口成本；后验标签只在隔离审计端使用。路径覆盖不冒充准确率。 |
| C3 精确编辑和验证 | 模型仅编辑已展示原 base 范围；候选经解析/lint、复现、原有测试与补丁前冻结的独立审计探针筛选；拒绝重复 patch、越权路径、模糊 old 匹配。 | 零调用模拟多文件、失败回滚、预算、provider ambiguous；完整非模型回归如实记录。只有 C0–C3 过关才新建付费 identity。 |
| C4 新的 DEV 配对 canary | 从原 30 中、排除 B4 4 题后，按冻结 manifest/仓库分层规则选 6 条历史未解任务；baseline 与真正接入 C1–C3 的 treatment 用同模型、同修复请求/输出上限。 | 先冻结 selector、代码 SHA、模型/预算/停止规则，再给出精确命令。观察至少 1 个 treatment-only 官方 resolved、0 baseline-only regressions，且无泄漏/安全/预算异常，才讨论完整 30；无净新则停下归因，不同质重抽。该小样本只用于机制准入，不声称统计显著。 |
| C5 同版完整 30 DEV | C4 通过后另冻一次运行身份，30/30 attempted，同一协议、每题无人工选文件/无逐题改 prompt。 | 报 resolved/30、有效 grade、abstain、定位/编辑失败和全部成本；历史 best-of 仅供诊断。**只有一次同版 run 真的 30/30，才能说“该开发集同版 30/30”。** 未达成则按新机制缺陷和预算做有限下一轮，不把 17 个旧解拼进去。 |
| C6 全新 E1-C 30 one-shot | 严格按用户要求，C5 真正 30/30 后才启动；在看新任务题面前冻结代码/模型/prompt/预算/停止规则、候选来源与固定替补顺序。 | 从固定 SWE-bench task tree 构造候选池，排除所有已 materialize/admission/DEV/人工看过的 instance 和 E1-B sealed TEST；先做零模型 source identity、镜像 digest、Base-Fail/Gold-Pass 准入。凑齐预定 30 后一次性运行，不根据结果换题或调参；报告 30 题全分母与成本。 |

省额度规则：C0–C3 优先零 provider calls；C4 先以 2 条预定任务作执行/泄漏哨兵，再完成其余 4 条；每臂每题建议最多 2 次修复请求，生成探针额外成本独立记账。**具体 soft/hard token 上限和批次上限只在 C3 的 prompt reserve 与 provider 行为核验后冻结**，不得沿用旧版弹性预算。任何 ambiguous 请求不自动重放；官方 grader 结果不能回流到同一任务的修复循环。仓库 `AGENTS.md` 要求真实模型实验具备用户对**精确命令**的授权；本文件不是运行授权。

## 4. 30/30 与独立测试的结论边界

“非公开断言”指运行时没有给修复端 benchmark 新增测试及官方 grader 反馈；不是模型从未在预训练中见过公开 issue，也不是自生成测试等同 hidden tests。“非人工定位”要求每题候选路径/窗口都由冻结通用规则与模型的有界工具动作产生，不能在 DEV 中把人工看过的路径写进规则表。必须保留完整 abstain 和失败分母。

30/30 目前**无法保证**，并且在已反复开发的 30 题上达到也不证明新任务泛化。若 C4 连续两个**机制不同且各自预注册**的小样本仍无净新 resolved，应暂停付费扩批，报告瓶颈与累计成本；不能以“直到成功”为由无限重复相同任务/提示。用户要求的严格顺序意味着未获得 C5 同版 30/30 时，C6 暂不运行；从研究效度考虑，另一个可选决策是在有稳定、显著更好的冻结方法后提前做独立 one-shot，但需用户明确改变这一顺序。

当前状态：**C0–C3 已实现并通过专项验证；C4 已完成并按停止规则封板；C5/C6 未启动。全新 30 题尚未选择/准入/运行，Fresh30 gate 明确记录 `new_task_tree_touched=false`。**

## 5. 2026-09-25 Post-run Addendum：C0–C4 实际执行结果

本节只记录执行事实，不改写 §3 的预注册门槛。

C0–C3 已落到真实运行路径，而不再是 B4 后“有模块但 runner 未消费”的状态：repair-side 统一经 `AgentView` / `assert_agent_path()` 读取 exact-base；加入内容级 sentinel 审计；issue Python snippet 与 original exact-base tests 在 `--network none` Docker 中执行；只有失败类型/题面契约一致的 probe 才记 `reproduced_failure`，否则明确 `no_reproducer`。Evidence v3 将 issue title terms、AST definition、caller relation、explicit-path suffix match 与 lexical windows 合并并冻结 `origin/depth/source_sha256`。新 runner 允许每臂至多一次 bounded inspect，候选 patch 经 exact replacement、AST parse、pre-frozen reproducer/original-test verification 后，才交给独立 evaluator 子进程 official grade。Fresh30 gate 代码在 C5 未同版 30/30 前 fail-closed。

C4 selector 不再取 manifest 前 4 条，而是排除历史 best-of 已解任务及旧 B4 四题后，对剩余 15 条 unresolved DEV 按 final manifest 中仓库首次出现顺序做 repo-stratified round-robin，冻结 6 条：`sympy-18211`、`sphinx-9230`、`astropy-7671`、`django-15563`、`matplotlib-24570`、`sympy-14711`。身份 selector SHA 为 `8035b9f323d752a3d7ced8638ae7936e870a383f7e58b45c26e1dcc65b8ce0a7`。

Prep 阶段 6 条中只有 `sympy-18211` 得到可靠 `reproduced_failure`，其余 5 条为 `no_reproducer`。这不是把失败隐藏掉，而是 C1 的 fail-closed 结果：错误类型不符、原有测试不构成题面失败或题面片段不足时不冒充复现成功。

授权命令 `.venv\Scripts\python.exe -X utf8 -m evals.e1c_blind_postb4_runner run-canary` 最终完成 **12/12 provider calls、28,169 tokens、0 over-budget**。结果：baseline **0/6**，treatment **0/6**，treatment-only resolved=0，baseline-only resolved=0，`net_new_resolved=0`，`expand_c5=false`。逐题主要状态：`sympy-18211` baseline patch 被 frozen reproducer 拒绝、treatment 因 exact-old 非唯一被拒；`sphinx-9230` 两臂 abstain；`astropy-7671` 两臂生成相同 patch 但被 original-test regression guard 拒绝；`django-15563` treatment patch 进入 official grader、valid log 但 unresolved；`matplotlib-24570` treatment patch 进入 official grader、valid log 但 unresolved；`sympy-14711` 两臂 patch 均未修复 frozen reproducer。

因此 C5 gate 返回 `ready=false / C4_stop_rule_not_met`，C4 result SHA=`537c35cae1f20a982ef365af43380206f6e06a8f25cc8ce112451fd1b8bb43d2`。Fresh30 gate 同样返回 `ready=false / C4_stop_rule_not_met`，并明确 `new_task_tree_touched=false`。**本计划到此按协议停止：不运行同版 30 DEV，不选择/查看全新 30 题，不通过同质重抽寻找正结果。**

当前最明确的新瓶颈不是“缺少 AST 模块”，而是 **blind reproducer coverage 仅 1/6**。下一机制版本若继续，必须以题面派生的环境初始化/最小 executable slice/原有测试目标选择与语义匹配为核心，并另立预注册 canary；只有新 canary 达到 §3 C4 gate，才允许重新讨论 C5。

最终工程验证：post-B4 专项 **31 passed / 4 warnings**，Ruff clean。工具层重复启动的两个全量 pytest 作业分别为 **714 passed / 4 skipped / 33 warnings** 与 **713 passed / 1 failed / 4 skipped / 33 warnings**；后者唯一失败是既有 Streamlit AppTest 8 秒冷启动超时。该差异作为环境噪声保留，不删除失败记录，也不把通过数解释为修复效果。

