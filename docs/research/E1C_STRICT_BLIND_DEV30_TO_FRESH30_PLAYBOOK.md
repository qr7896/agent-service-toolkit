## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-09-25
- Verification Status: UNVERIFIED（这是后续执行计划，不是已完成实验）
- Version Label: e1c-strict-blind-playbook-v1

# E1-C 严格盲态：持续开发到同版 30/30，再做全新 Fresh30

> 执行对象：接手本仓库的 Codex/WebCodex 或人工研究者。先读 [简明 Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[当前交接](README.md)、[集中日志](PROGRESS_LOG_ARCHIVE.md)、[v4 原预注册](E1C_BLIND_REPRODUCER_V4_PREREG_AND_FRESH30_PLAN_2026-09-25.md) 和根目录 [AGENTS.md](../../AGENTS.md)。本文件是**未来严格协议的作业书**，不宣布 v4 已达标，不授权任何付费命令。

## 0. 目标、现状和不可跳过的顺序

目标分两层，不得合并：

1. **开发集目标**：同一个冻结代码/模型/提示/预算身份，在已有 E1-C DEV 30 题上，零人工逐题定位、修复端不消费公开测试断言，30/30 attempted 且 30/30 independent official resolved。只有这一结果可称“该版本在已见 DEV 30 上 30/30”。
2. **独立检验目标**：前者通过后，先冻全新且不重叠的 30 条任务身份，再准入、一次性运行；报告 official resolved/30。若也得 30/30，只能说“该冻结系统在这一批新 30 题上 30/30”，**不等于对所有未来问题完美**。

当前 E1-C 独立首次运行 1/30；同题 DEV 单版完整运行 4/30；跨版逐题 best-of 13/30；盲态 C4 baseline/treatment 0/6 对 0/6；v4 在已污染三条 Django DEV 上零模型复现 3/3。独立 v4 canary 未选、C5 未跑、Fresh30 未选。机器计划 [Fresh30 30-slot plan](../../data/e1c_fresh30_v4_prereg_plan.json) 为 gate_ready=false、new_task_tree_touched=false。

**必须先说明协议分叉：** 现有 v4 runner 会把原始 problem_statement 放进修复 payload，并存在从题面提取 inline test/assertion 的 witness。在本文件的严格定义下它不合格。应新建“strict-blind v5”候选协议/runner/gate/输出目录，保留 v4 冻结身份及结果；不得把 v5 产物伪装成 v4 canary 或写入 v4 硬编码结果路径。v5 名称只是计划标签，代码和命令目前**尚不存在**。

### 实验总卡

| 项目 | 冻结前的计划值 |
|---|---|
| 类型与假设 | Python 代码修复实验；严格盲态的通用复现/定位/编辑链有机会提升 official resolved，同时维持零泄漏、零人工逐题定位。假设尚未验证。 |
| 工作目录/环境 | 仓库根目录；Python 3.12–3.14、提交的 uv.lock、Docker Linux engine、官方镜像与 exact-base 源码。 |
| 运行入口 | 当前只有历史 v4 入口；strict-v5 的模块、精确命令和预算须在阶段 B–E 实现/预检后冻结，**现在无可执行 live 命令**。 |
| 输入 | 旧 DEV 30 manifest；独立三题 canary 的先冻元数据；Fresh30 仅在前置门槛通过后才冻结的元数据。题面/测试/Gold 的访问按第 2 节分域。 |
| 主要输出 | 每阶段的 identity/manifest SHA、零调用准入、provider ledger、逐题 trace/patch/grade、独立 audit、gate 判定；新结果只能写独立目录。 |
| 监控 | 每个 live run 预设 wall-time 上限，监控进程存活、provider started/completed/ambiguous、token 余额、Docker、磁盘与逐题完成数；中断只保存状态，不自动重试。 |
| 主要分析 | 配对 canary 先看 treatment-only official resolved；DEV/Fresh30 分别看完整分母的 official resolved/30，再看泄漏、定位、复现、失败分类和成本。 |

## 1. 研究问题和成功标准

**研究问题：** 给定公开 issue 的自然语言需求和精确 base 生产源码，任务无关的故障复现、自动定位、有限查看、精确编辑与盲态自检，能否在真实模型调用及独立官方判分下完成 E1-C DEV 30/30，并在从未参与调参的 Fresh30 上保留效果？

**主要指标：** official resolved/30，分母是已冻结的全部 30 题；弃答、越权拒绝、验证失败、基础设施故障都保留并单列。**并列硬约束：** assertion-leak=0、manual-file-selection=0、任务 ID/历史解答特例=0、最终配置同版、ledger/代码/数据身份可复核。

**次要指标：** 补丁前可信复现数、自动 top-1/top-3/top-5 文件定位（只在隔离审计侧用 Gold 判真）、源码读取字符/token、模型 calls/tokens、弃答、重复补丁、无效精确编辑、F2P/P2P、独立验证拒绝、provider unknown/ambiguous、预算和安全事件。窗口覆盖数不能替代定位正确率，pytest passed 不能替代 official resolved。

**重要限制：** 公开 issue/源码可能早已出现在模型预训练中；运行时隔离只能证明“本次执行没有把禁用材料送入修复端”，不能证明模型从未见过题目，也不能保证 30/30 可实现。

## 2. 四个信息域：先把“非公开断言”定义成可测契约

| 域 | 可见材料 | 绝不可做 |
|---|---|---|
| 选择/准入域 | 选题前只见 instance_id、repo、base_commit、image 等元数据；身份冻结后可由隔离准入程序读任务并执行 Base-Fail/Gold-Pass。 | 按题面难度、失败输出或模型结果替换任务。 |
| 修复域 | **经统一净化器处理后的自然语言 issue**、精确 base 的允许生产源码、通用源码索引、由这些材料自动生成的 probe 与其结果、受限 inspect 结果。 | 读 test.patch、公开/隐藏测试断言正文、题面内嵌可执行断言、原有测试源、官方 Base-Fail/grade 日志、Gold patch、历史候选或 outcome；实例 ID 只作账本键，不作提示特征。 |
| 验证/评测域 | 隔离容器可运行 frozen 自生成 probe、静态检查和官方 grader；评分端可持有 F2P/P2P 等 benchmark 材料。 | 把官方失败断言、测试代码、Gold 或评分结果回传给同题修复循环。 |
| 研究审计域 | 候选补丁冻结后可看官方成败、Gold 文件路径等后验标签并分析**聚合失败类别**。 | 按已知题目 ID/答案补专用定位规则，再称它是任务无关方法；对新 Fresh30 看结果后调参或换题。 |

题面若包含 `assert`、`self.assert*`、测试函数/代码块，不能仅禁用一个 witness：修复 payload 中的**原始题面本身**也必须替换成经确定性净化的自然语言投影。净化器需要保留与问题有关的自然语言、删除可执行断言/测试体，并对无法无歧义拆开的题目标 `assertion_projection_unsupported` 后弃答；不可由人逐题改写为答案提示。自生成的断言可以存在，但只能由允许的自然语言合同和生产源码经冻结的通用规则产生，记录完整 provenance，绝不能复制 benchmark 断言。禁止字段名、路径名、内容指纹和完整 prompt/trace 四层都要审计。

## 3. 阶段 A：盘点、封存和工作区可复现性（零模型）

1. 只读核对当前 Git HEAD/dirty status、已有 E1-C 30 题 manifest、B4/C4/v3/v4 artifact、provider ledger 与 SHA；给每条任务打“旧 DEV / 旧 canary / 仅元数据接触 / 已看题面 / 未接触”污染标签。正式 E1 Wave A/B、V3 pilot、E1-B 原 TEST 与 E1-C 替补候选也列入排除审计。
2. 复制**清单与哈希**到新的冻结记录；保留旧失败日志和模糊 provider 请求，不重算成零费用。当前仓库有大量未提交文件；在第一次新 live 前须人工审核差异并形成可定位的代码/配置快照，不能把未跟踪代码误称为已提交 HEAD。
3. 新 strict-v5 身份、输出目录、selector/gate schema 与旧 v4 完全分开；在文档里明确哪些旧函数可复用、哪些因断言泄漏必须替换。禁止修改旧 result/ledger/freeze manifest。

**交付物：** baseline inventory、contamination ledger、差异审计、旧 artifact SHA、v5 proposal manifest。**Gate A：** 旧事实与机器文件一致、没有任何旧产物被覆写；否则停止。

接手当天在仓库根目录可先执行下列**只读/零 provider**核对；v4 Fresh30 gate 此时预期返回状态码 2、ready=false，不能为得到 0 而改 artifact：

```powershell
git rev-parse HEAD
git status --short --untracked-files=normal
uv run --frozen pytest -q tests/test_e1c_blind_reproducer_v4.py tests/test_e1c_blind_repro_v4_selector.py tests/test_e1c_blind_repro_v4_runner.py tests/test_e1c_blind_repro_v4_reserve.py tests/test_e1c_fresh30_gate_v4.py tests/test_e1c_fresh30_plan_v4.py
uv run --frozen python -X utf8 -m evals.e1c_fresh30_gate_v4 gate
```

这些命令只是确认历史基线，不会生成严格 v5 结果。新 v5 模块完成后应先跑对应 focused pytest/Ruff，再跑全量 `uv run --frozen pytest -q`；遇环境超时和断言失败分开报告，不能拼接两次测试成“一次全绿”。

## 4. 阶段 B：修复端/评分端硬隔离（零模型）

1. 实现单一的 issue 自然语言投影入口；模型、lexical/semantic/structural 检索、probe 生成与补丁验证只能接收该投影，不能再从原始任务目录旁路读 problem_statement。
2. 修改 AgentView/文件读取门禁：repair 只读 exact-base 允许的生产源码；阻止测试目录、软链逃逸、路径穿越、测试 patch/Gold/grade/result 文件。评分进程独立目录及访问权限，评分完成前候选 patch 已冻结。
3. 对 prompt、工具响应、bundle、序列化 trace、probe 源码/输出运行同一泄漏审计；在测试 fixture 注入唯一的禁用断言片段和 oracle sentinel，若任一层出现即 fail-closed。
4. 建负面测试：题面内嵌 pytest/unittest/assert；test.patch 改名/大小写/绝对路径；Gold 值藏在字符串、嵌套对象、日志、symlink、tool-result；历史候选在缓存中；模型请求含旧 instance_id→路径映射。正面测试确认普通自然语言需求和生产源码仍可用。
5. 同一输入重复运行产生相同净化结果和 SHA；不确定净化时不“猜测保留”，标 unsupported 并计入分母。

**交付物：** strict-v5 boundary spec、净化器、信息流图、正负单测、实际 runner 级 sentinel 审计。**Gate B：** repair-visible prompt/bundle/trace 中 0 个禁用片段、测试路径读取 0、任何绕过都会导致测试失败；仅单元测试 guard 函数而不接入真实 runner 不算通过。

## 5. 阶段 C：把旧 30 题变成失败类型表，不变成答案表（零模型）

1. 对 C4 和历史 DEV 的 frozen artifact 逐条分类：`no_reproducer`、错误/不相关 probe、错文件/错符号、窗口截断、无效 old-match、重复 patch、空编辑、目标未修复、P2P 回归、provider 失败和预算中断。一个任务允许多个原因，但主因只按预先定义的优先级选。
2. 记录每类的任务数、导致的 calls/tokens/Docker 次数；研究审计侧可使用后验评分找瓶颈，但给工程实现的输入只能是**聚合机制缺陷**，不能是“某题应改某文件某行”。
3. 按影响范围和可验证性排队：先信息泄漏、无可信复现和错文件，再无效编辑、回归，最后提示词微调；每次只引入一个可证伪的通用机制。

**交付物：** 30 行 failure taxonomy CSV/JSON（审计侧）、聚合 Pareto 报告、下一机制假设卡。**Gate C：** 分母 30、每条都有可解释状态；不得用历史 best-of 作为新 runner 的运行时提示。

## 6. 阶段 D：任务无关的补丁前复现（先零模型）

1. 从净化后的自然语言需求抽取输入、操作、预期关系、错误类型与环境前提；基于 exact-base 生产 API/AST 生成**少量**候选 probe。优先用错误类型/返回值关系、属性不变量、前后状态关系和变形关系，不复制任何 benchmark 断言。
2. 每个 probe 固定源文本、依赖、运行命令、base_commit、环境、超时、网络关闭、输出 SHA。补丁前在独立容器执行；只有“确实在 base 失败、失败类型与自然语言合同相符、重复执行稳定”才标可信 `reproduced_failure`。环境/导入/测试装置错误一律单列，不计成功。
3. 绝不能用“官方 Base-Fail 中哪条断言失败”反推 probe；官方测试只可在隔离审计域后验验证相关性。没有可信 probe 时显式 `no_reproducer`，允许有界结构证据与弃答，但不能编造失败。
4. 用旧 DEV 做确定性回归和消融；若只在已见三条 Django 上有效，继续完善可跨 repo 的契约/环境抽象，不能宣称 v4 3/3 泛化。

**交付物：** candidate→冻结→执行→可信判定的逐题 trace，coverage 与 false-reproducer audit。**Gate D：** 合成负例、旧 DEV 回归与泄漏检查全过；独立 canary 后还要求至少 2/3 有可信补丁前复现（沿用当前 canary 的最小覆盖准入，未来改变须先改预注册）。

## 7. 阶段 E：全自动定位、受控编辑和盲态验证

1. 定位候选只来自净化 issue、生产源码词法命中、AST 定义/调用/导入关系及**自生成**可信 probe 的栈/覆盖。冻结融合/排序公式与权重；输出 path、symbol、range、origin、depth、source_sha、置信/弃答原因和每次读取成本。不得把 task ID、Gold 文件、公开测试 import 或人工观察到的目标路径作为规则。
2. 初始 top-k 不足时，模型最多做预注册次数的有界 inspect；只准看候选/安全生产路径的短窗口。提供不存在/越权路径时要明确拒绝，不自动扩成全仓库读取。
3. 候选补丁使用 exact-base、已展示的非测试源码和精确 old→new；重复补丁 SHA、old 文本不唯一、语法错误、路径越权直接拒绝。避免为了凑通过而把验证门禁调松。
4. 补丁前冻结自生成 probe；补丁后运行同一 probe、语法/lint 与预算内非 oracle 静态/行为检查。官方 grader 只在候选定稿后由评分域运行，结果不得用于同题第二轮修复；若允许模型第二轮，反馈只能来自上述盲态检查。
5. 研究审计域统计 top-1/top-3/top-5 与 Gold 路径的后验对应、实际源码读取数、编辑有效率、目标/回归失败。top-k 统计须保留找不到/弃答任务，不能只算生成 patch 的子集。

**交付物：** strict-v5 runner、定位 provenance、patch/verification trace、分类账本、针对跨文件/同名符号/伪成功 probe/空编辑/越权的回归。**Gate E：** 真实 runner 路径的泄漏/安全/预算/重复编辑测试通过；完整非模型回归与 Ruff 如实记录。不能把本阶段的窗口覆盖说成 official repair。

## 8. 阶段 F：每一版优化如何循环，避免“无限同题刷分”

每一轮使用下列同一张变更卡，旧版本只读封存：

| 字段 | 必须填写 |
|---|---|
| 问题 | 上一轮哪类失败占主导，证据是什么；不写具体题目的目标补丁 |
| 假设 | 单一通用机制预期改善哪项中间指标/official resolved |
| 变更范围 | 净化、复现、定位、编辑或验证中的哪一层；其余保持不变 |
| 身份 | 代码/提示/模型/manifest/预算 SHA、run_id、新目录 |
| 零调用门槛 | focused/full tests、泄漏审计、prompt reserve、Docker/source 可用性 |
| 小样本 | 预先冻结 canary 身份与 baseline/treatment、停止规则 |
| 成本 | 每请求/每臂/整批 calls 和 token hard ceiling，时间上限、无自动重试 |
| 结论 | 原始 denominator、失败分类、tokens、是否开放下一阶段 |

循环规则：先零模型修一个机制 → 新的**独立且不重叠** canary → 若有 treatment-only official gain 再完整 DEV 30。canary 失败必须保留负结果、重新分析并创建**新机制 + 新身份**，不能在同一三题上反复改到成功。DEV 30 未达标可以继续作为开发集优化，但后续任何独立 canary 用过的任务从 Fresh30 候选永久排除。若连续两轮机制不同的 canary 仍无净新增，暂停付费扩批，先审计失败和投入产出；若资源/预算不足，停在“未达标”，不伪造通过。

## 9. 阶段 G：独立三题 canary 的选题、准入与付费门槛

1. **先元数据、后题面：** 从可核验的外部任务树/固定 revision 读取元数据；排除 Formal E1、E1-B、V3 pilot、E1-C 原候选/替补/DEV/B4/C4/v3/v4 和所有已看内容或同源 issue/patch/commit。固定排序与恰好三条身份；冻结 manifest SHA 和污染审计。获取元数据失败（此前发生 DNS 错误）就停止，不把旧题重命名为新题。
2. **再准入：** 此时才 materialize 题面、exact-base 源码和官方镜像；核实镜像 digest、base 源树身份、Base-Fail、独立 Gold-Pass、净化后的 issue 可用性、probe 预检、模型提示 reserve、Docker 磁盘/网络。只有提前规定的环境性替补可按冻结顺序进行；不可按题意/难易或结果挑题。
3. **公平配对：** 同三题 baseline/treatment 使用相同模型、温度、输出/调用上限和结构证据；唯一差异是 treatment 可获得冻结的严格盲态 reproducer context。评分域独立执行 official grader。按现有 runner 模式最多 2 calls/arm，即三题两臂最多 12 calls；**这只是设计上限，实际 v5 数值须在零调用 reserve 后冻结**。
4. **准入后才展示精确 live 命令和预算给用户授权。** 根 AGENTS.md 要求每个真实模型实验有该精确命令授权；本计划、过去授权和“弹性预算”均不代替这一步。请求 ambiguous 不自动重放，不把未知 token 算 0。
5. **停止规则：** 全部三题、两臂完整；至少 1 条 treatment-only official resolved、0 baseline-only、0 身份/泄漏/安全/预算/基础设施异常，并通过独立 ledger/artifact 审计，才允许讨论 C5。未通过就是有效负结果，不继续同一身份。

三题 canary 的 1 条净新增只是**进入 DEV 30 的工程门槛**，样本量不足以证明广泛泛化；它不能直接作为 Fresh30 的替代成绩。

**注意：** strict-v5 代码和命令尚不存在；现有 v4 run-canary 命令**不满足本文件严格断言口径，不得拿它的结果替代 v5**。v5 gate 也须新建，不可把输出写进 v4 硬编码结果目录来“打开”旧 Fresh30 gate。

## 10. 阶段 H：同一版本的 DEV 30/30

1. canary 过关后先冻结 C5 的 DEV 30 manifest、strict-v5 代码 SHA、issue 投影、证据排序、probe 模板、模型 ID/温度、每题/整批调用与 token ceiling、补丁/验证规则、无重试规则和唯一 run_id。完整 preflight 必须显示 30/30 准入、旧结果只读、新结果目录不存在。
2. 对固定 30 题一次顺序运行；**不为某题人工选文件、换 prompt、提高预算或修改代码**。每题保留 prompt/可见 evidence 哈希、定位 trace、probe、calls/tokens、patch SHA、拒绝原因和独立 official grade；所有 30 条进入分母。
3. 完成后由独立 audit 对账 manifest/runner/model/ledger/patch/grade SHA；核实 30 attempted、无被漏掉的题、无泄漏/越权、provider uncertain 另列。成功门槛是**同一次冻结身份 official resolved 30/30**，不是累计多个身份的 best-of 30/30。
4. 若 0–29/30：结果照实封存，按阶段 F 的失败类型重新设计；可用旧 DEV 做分析，但下一个新版本仍需新的独立 canary。不能把同一旧运行“补跑缺题”伪装成一次干净 30/30。

**交付物：** C5 30 行结果、审计、逐题失败/成本、机制消融和是否达到 Fresh30 hard gate 的明确布尔值。未真达 30/30 前，Fresh30 task tree 保持未选择、未读取、未 materialize。

## 11. 阶段 I：全新 Fresh30 的选择、准入和一次性测试

只有严格 v5 canary 与同版 C5 30/30 均过关，**新的 v5 Fresh30 gate** 才能从 false 变 true；旧 v4 gate 不代替它。接着按下列顺序：

1. **预先封协议：** 固定任务来源及 immutable task-tree revision、发现顺序/确定性排序、所有排除 lineage、准入条件、替补顺序、软件 SHA、模型/提示/预算、总体分母及中断规则。此时不打开 Fresh30 题面、测试和结果。
2. **仅看元数据冻候选身份：** 先记录所有候选的 instance/repo/base/image 与污染匹配结果；保留选择和排除原因。不能因某题看起来难或模型可能失败而换题。
3. **再依固定顺序物化/准入：** 在独立目录核验 exact-base/source tree、官方 image digest、Base-Fail、Gold-Pass 与安全/预算预检；环境性失败保留日志，并仅按预冻结的客观条件/替补顺序在**看到模型 outcome 之前**补足 30。最终 30 条 manifest 冻结后不再换题。
4. **资源确认：** Docker 镜像/数据盘/网络、原始和结果目录、UTF-8 官方日志解析、provider credential/账本、预计下载与运行时间全部在零模型 dry-run 检查。不得自动 prune 旧镜像或删除产物来挤空间。
5. **精确授权后 one-shot：** 只用阶段 H 冻结的系统版本运行，不按 Fresh30 中间结果调参；每题 calls/预算受同一 guard 约束，provider ambiguous 不自动重试，基础设施失败留在冻结分母并单列。
6. **独立审计和报告：** 逐题核对 prompt 禁用材料、自动定位 provenance、patch/grade、ledger、calls/tokens、F2P/P2P、abstain、安全事件及所有失败；主结果是 official resolved/30，不能只报告“可评分题”的分数。

Fresh30 若为 30/30，可以报告“冻结版本在这次全新样本 30/30”；若少于 30，报告差距，不在此批上修补后仍把它当独立一次性证据。下一次独立验证须另冻完全新 cohort。

## 12. 预算、监控与中断规则

- 零模型阶段 A–E 优先用单测、旧 DEV 的离线诊断、Docker probe，不启动 DeepSeek。付费额度首先给独立 canary，过 gate 才给 DEV 30，DEV 30/30 后才给 Fresh30。
- 每次 live 前按真实 prompt reserve + provider tool/schema/输出额外成本冻结单请求、单臂/单题、整批 hard ceiling；`soft` 阈值只用作预警，`hard` 上限耗尽立即阻止**下一次**请求。旧 thinking 超限经验说明不能假定原子调用会被客户端在中途截断；真实 provider 用量仍须单独对账。
- 监控进程存活、最长 wall time、每题完成数、provider started/completed/ambiguous、token 余额、Docker grader 状态和磁盘。中断时先保存 state/ledger/最后完成题；只读审计后依事先冻结的恢复协议处理，不重放已完成或不确定的 provider call。
- 不放宽测试断言、不删失败题、不把失败改 skip、不在结果出来后补预算/改门槛。任何配置或预算变化都产生新 run identity；旧结果保持可追溯。

## 13. 每个阶段的交接记录模板

每次结束只往 [集中日志](PROGRESS_LOG_ARCHIVE.md) 追加一条，Roadmap 只改阶段状态。交接应包含：日期、stage、目的、输入 manifest/代码 SHA、零模型/付费命令、模型与预算、任务 denominator、已完成/失败/不确定 calls 与 tokens、official resolved、assertion-leak/manual-selection 计数、异常及保存路径、stop/gate 判定、下一步唯一允许的动作。**没有 result artifact 时写“未运行”，不能写成“0/30 失败”。**

## 14. 当前立即可做的第一批待办

- [ ] 核对 dirty worktree 与 v4 artifact，不提交/删除用户已有内容；创建 strict-v5 独立设计/身份文件。
- [ ] 把原始题面直传和 inline-assertion witness 标记为严格协议阻塞项；实现统一自然语言投影与 runner 级泄漏负面测试。
- [ ] 用旧 30 DEV 的现成 artifact 生成聚合 failure taxonomy，不向运行时注入题目答案。
- [ ] 在零模型条件下验证通用 probe + 自动 top-k 定位 + 受控编辑真实路径，记录专项/全量回归。
- [ ] 准备可核验的外部三题**元数据**来源；先冻结再读题。完成前不得运行新的 canary。
- [ ] 只有上述门槛通过、身份和预算冻结后，向用户展示**准确**的 strict-v5 live 命令请求授权。

本文件不是结果承诺。若实际研究始终无法使同版 DEV 30/30 成立，就应保留“未达标”结论；不能为凑出所谓完美结果牺牲盲态、自动定位、独立样本或分母完整性。
