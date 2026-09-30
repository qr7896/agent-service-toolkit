# E1 / E2 快速完成进度安排表

## Material Passport

- artifact: `experiment_execution_plan`
- created: `2026-09-20`
- last_updated: `2026-09-24`
- status: `ACTIVE_PLAN_NOT_LIVE_AUTHORIZATION`
- scope: `E1-B 12-task pilot → formal E1 minimum 30 tasks → E2 minimum 100 tasks`
- current live state: `Formal E1 n=30 sealed at 0/30; E1-C n=30 completed at 1/30 with 49 calls / 65,801 tokens; E2 main not started`
- governing protocols: `E1B_REPLACEMENT_HELDOUT_PROTOCOL.md`, `E1B_REPLACEMENT_PILOT_PREREGISTRATION.md`, `E2_E3_EVALUATION_PROTOCOL.md`
- claim boundary: this plan schedules experiments; it does not authorize a provider call or guarantee a favorable result.

## 1. 当前阶段

V0 closed，V1/V2 frozen，V3 pilot closed。Formal E1 n=30 已完成并封存（0/30），E1-C 独立运行验证已完成（1/30），预冻结的 E2 运行可靠性 Entry Gate 已通过。当前工作转向 E2 的独立 amendment/preregistration、100-task cohort 与零调用多 arm dry-run；E2 真实模型调用尚未获单独精确命令授权。下表状态优先于本文件较早的 E1 操作日程；历史步骤保留为原计划，不当作待重新执行的命令。

| 工作包 | 当前状态 | 完成定义 |
|---|---|---|
| E1 plumbing smoke | DONE | 4-task deterministic plumbing 与 grader 跑通；不作为 autonomous repair efficacy |
| E1-B replacement pilot | INDEPENDENT HELD-OUT | 与已封存 Formal E1 和 E1-C 分开，不能把现有结果当作其完成证据 |
| Formal E1 minimum | DONE, SEALED | 30 个 clean 任务完成；0/30 resolved，原失败留在分母 |
| E1-C operational gate | DONE, PASS | 独立 n=30：1/30 resolved；artifacts 100%、critical safety 0、infra 0/30 |
| E2 Main | PROTOCOL ONLY | 100 个新任务完成 paired multi-arm evaluation、统计与盲审 |
| E3 External | FUTURE | E2 解释完成且达到预冻结 go gate 后再启动 |

## 2. 快速完成原则

1. 不继续扩 v10 机制；现有 runtime、editor、grader、artifact contract 只修复可复现缺陷。
2. E1 使用最低正式规模 `n=30`；E2 使用协议下限 `n=100`。
3. 先冻结再调用。任务选择规则、arm、预算、分析脚本和停止规则必须先写哈希。
4. E1 分两波执行：现有 Wave A=`12`，新增 Wave B=`18`。Wave B 必须在读取 Wave A outcome 前冻结选择规则，并承诺无论 Wave A 好坏都执行；禁止用 Wave A 调 prompt/policy。
   - Wave B deterministic curator selection procedure 已在 `E1_WAVE_B_SELECTION_PROTOCOL.md` 于 Wave A outcome 可见前冻结；其文件 SHA-256=`7bd230c46102a014da039c2981a36a01918ab5f47457e2be7b57e981987118f5`。后续任何 selection-rule 变更都必须产生新 identity 并披露。
5. Wave A 与 Wave B 分别报告。只有 editor/runtime/model/budget/analysis identities 一致时，才额外给出预声明的 pooled `resolved/30`。
6. E2 的 100 个主任务不得与 E1 outcome-driven tuning 混用；E1 任务只用于冻结 E2 配置，不进入 E2 主结论。
7. 所有 provider/model/infrastructure failure 留在分母；不重试、不追加预算、不删除难题。
8. 用任务批次做容错，不做逐批调参。批次之间只允许修复阻止执行的基础设施错误；任何修复必须生成新身份并完整披露。

## 3. E1 详细安排（目标：5–8个工作日）

| 顺序 | 时间 | 工作 | 模型调用 | 产物 / 通过门槛 | WebCodex 可做 |
|---:|---:|---|---:|---|---|
| E1-0 | 0.5天 | 同步工作区；确认 Roadmap、预注册、package 与测试基线可见 | 0 | `git diff --check`；非模型 focused tests 通过；不读取 sealed 内容 | 可以 |
| E1-1 | 0.5–1天 | 桌面执行已冻结 12-task Wave A one-shot | ≤12 | 五件套齐全；账本/summary/outcome 对账；exact `resolved/12` | Web 环境通常不可以；桌面执行 |
| E1-2 | 0.5天 | 审计 Wave A，不改配置；生成独立结果表 | 0 | 12/12 denominator；F2P/P2P、calls、tokens、failure taxonomy | 可以，前提是产物已同步 |
| E1-3 | 2–4天 | 独立 curator 按同一选择规则新增18条 clean task；不向 tuning context 暴露 fixture/gold | 0 | 18/18 Base-Fail + independent Gold-Pass；overlap/duplicate audit；新 manifest hash | WebCodex 可管理 metadata，不应读取 sealed 内容 |
| E1-4 | 0.5天 | 冻结 Wave B package；复用 Wave A exact editor/runtime/model/ceilings | 0 | admission + dry-run；0 calls/0 tokens；分析脚本提前冻结 | 可以做 metadata admission；live 仍需授权 |
| E1-5 | 0.5–1.5天 | 单次运行 Wave B 18 tasks | ≤18 | 五件套有效；不重试；所有18条留在分母 | 由能访问 sealed assets/API key 的执行主机完成 |
| E1-6 | 0.5–1天 | E1 封板分析与20%成功 patch盲审抽样 | 0 | 分波结果；若身份一致再报告 pooled `resolved/30`；Claim Ledger更新 | 可以 |

### E1 预算与停止规则

- Wave A：已冻结上限 `12 calls / 26,400 tokens`。
- Wave B：建议复用 `1 call/task / 2,200 tokens/task / 600 output tokens / thinking off / no retry`，因此上限 `18 calls / 39,600 tokens`。
- Formal E1 合计上限：`30 calls / 66,000 tokens`。
- E1 的完成是“协议有效并完整报告”，不是必须达到某个事后挑选的成功率。
- 建议 E2 operational gate（需在 Wave A live 前或至少在查看 outcome 前冻结）：artifact completeness=100%；critical safety violation=0；基础设施失败率≤10%。未达到时先修复基础设施并建立新实验身份，不把失败任务悄悄重跑。

## 4. E2 快速但仍可辩护的设计（目标：3–5周）

### 4.1 样本与主比较

- 使用协议下限 `n=100`，全部为 E1 主结论之外的新任务。
- repository/commit grouped split；同 issue/patch lineage 不跨任务；按 bug/feature/refactor、文件数、跨模块深度、测试类型分层。
- 先冻结两个 primary paired comparisons：
  1. `V0 Utility Gate` vs `Fixed-K lexical`；
  2. `frozen V2` vs `V0 Utility Gate`。
- `V3 Experience ON` vs `OFF` 只在 strict-past eligible 子集上报告，子集规则和最小数量在第一次 E2 call 前冻结。
- V1 与 V0 Evidence Gate 保留为全量机制基线，避免只比较挑中的赢家。

### 4.2 快速执行矩阵

| 类型 | Arms | 任务数 | 预计 task-arm runs |
|---|---|---:|---:|
| 全量主矩阵 | Fixed-K、V0 Evidence、V0 Utility、V1、V2 | 100 | 500 |
| Experience paired | V3 ON / OFF | 预注册 eligible subset，建议30–100 | 60–200 |
| 诊断消融 | No-RAG、lexical-only、semantic-only、No-CodeGraph | 同一分层30-task subset | 120 |
| 合计 | 去除配置哈希完全相同的重复 control | — | 约680–820 |

`No-Experience` 如果与冻结的 V3 OFF 配置哈希完全一致，可预声明为共享 control，不重复付费；若不完全一致则必须单独运行。不能在看到结果后为了省预算合并 arms。

### 4.3 E2 工作包与日程

| 周期 | 工作包 | 主要动作 | 完成门槛 |
|---|---|---|---|
| 第1周 | E2-DATA | 独立 curator 分仓库建立100-task cohort；Base-Fail/Gold-Pass、去重、污染审计 | 100/100 executable；manifest sealed；tuning context只见metadata |
| 第2周前半 | E2-FREEZE | 冻结镜像、模型、editor、所有policy/arm hash、预算、分析脚本、primary comparisons与盲审规则 | admission通过；所有arm zero-call dry-run通过；package不可变 |
| 第2周后半 | E2-PREFLIGHT | 用synthetic fixtures验证调度、断点账本、配对完整性、统计脚本；不跑真实任务 | 0 provider calls；故障注入与artifact reconciliation通过 |
| 第3周 | E2-LIVE | 按25-task固定批次执行；建议安全验证后最多4并发；批间不看效果改配置 | 680–820 task-arm rows；无静默重试；每批哈希一致 |
| 第4周 | E2-AUDIT | 账本/任务/arm全对账；paired bootstrap 95% CI、effect size、失败与安全事件 | exact denominators；缺失/失败保留；统计脚本可复现 |
| 第4–5周 | E2-REVIEW | 随机盲审≥20%成功patch；完成主表、成本表、failure taxonomy和claim audit | 盲审记录；结果报告；E3 go/no-go决策 |

### 4.4 E2 预算

- 若沿用 E1 的 `2,200 tokens/task-arm` ceiling：
  - 680 runs：最多约 `1,496,000 tokens`；
  - 820 runs：最多约 `1,804,000 tokens`。
- 不建议用 outcome-driven early stopping 节省费用，因为它会破坏 paired denominator。可在第一调用前把固定运行矩阵缩小，但不能执行中途因结果不好而删 arm。
- 真正节省时间的方式是：任务 curation 分片、配置等价 control 去重、固定30-task消融子集、批量环境缓存，以及在验证隔离后使用有限并发；不是减少失败任务或放宽 grader。

### 4.5 E2 分析与 E3 gate（第一次 E2 call 前冻结）

推荐主报告使用 paired resolved-rate difference、bootstrap 95% CI、pass@1、F2P/P2P、calls/tokens、files read、irrelevant-read proxy 与 safety events。建议预冻结以下 E3 go 条件之一：

1. **Efficacy path**：候选最终 arm 相对 `V0 Utility` 的 paired resolved-rate delta 为正，且95% CI下界高于0；或
2. **Efficiency path**：相对 `V0 Utility` 的 resolved-rate 非劣界限不低于 `-5 percentage points`，同时 median tokens 或 files read 至少降低20%，且无新增 critical safety violation。

这些阈值目前是执行计划建议，不是已授权的 frozen E2 protocol。WebCodex 必须在第一条 E2 provider call 前将最终选择写入 preregistration 和 freeze manifest；不得看到 E2 outcome 后再改门槛。

## 5. WebCodex 接手顺序

1. 先读 `WEBCODEX_HANDOFF_2026-09-20.md`、本文件、E1-B preregistration、E2/E3 protocol。
2. 检查当前工作区是否包含本地未提交文件；如果只连接远端仓库，先停止并要求用户同步，不要从旧版 Roadmap 推断状态。
3. 先执行 E1-0 的非模型检查。不要调用 provider。
4. WebCodex 若无法访问桌面 curator 目录和 `DEEPSEEK_API_KEY`，不得重建或解压 sealed cohort；由桌面 Codex 执行 E1-1/E1-5。
5. 收到五件套后，按冻结分析脚本审计；不重跑失败任务。
6. 日志只追加到 `PROGRESS_LOG_ARCHIVE.md`；Roadmap只维护当前状态、下一门槛和结果链接。
7. E1 完成后先冻结 E2 amendment/preregistration，再开始100-task curation和zero-call preflight。

## 6. E3 分阶段路线（当前不执行，可提前停止）

E3 用于外部有效性，不是继续调参。只有 E2 完成并满足预冻结 go gate 才启动。E3 固定为一个 E2 winner 加两个预声明基线，默认每个任务3个task-arm runs；禁止逐仓库prompt tuning。为避免一次投入300+任务，采用预注册的累计 `30 → 100 → 300+` 阶段设计。

| 阶段 | 累计任务数 | 新增task-arm runs | 目的 | 允许的决定 |
|---|---:|---:|---|---|
| E3-0 Entry Gate | 0 | 0 | 检查E2 efficacy/efficiency gate、污染风险与冻结身份 | E2未过gate则不启动E3，直接封板负结果/局限 |
| E3-A Feasibility | 30 | 90 | 验证外部仓库安装、grader、artifact与安全边界 | 只可因安全/基础设施门槛失败而停止；不可据好结果宣称外部有效 |
| E3-B Futility | 100 | +210 | 评估是否仍有继续到300的价值 | 可按预冻结futility rule停止；不可调prompt、删任务、换winner |
| E3-C Confirmatory | 300+ | +600以上 | 完成外部有效性主分析 | 完整报告winner与两基线、跨仓库异质性及污染风险 |

建议提前停止规则必须在 E3 第一条调用前冻结：

1. **Entry stop**：E2 未满足已冻结 efficacy path 或 efficiency path，不启动 E3。
2. **Safety/operations stop at 30**：critical safety violation > 0，或 artifact completeness < 95%，或 infrastructure failure > 10%；停止并修复基础设施，旧结果保留且不混入新身份。
3. **Futility stop at cumulative 100**：winner 相对强基线的 resolved-rate delta 不为正，且 efficacy delta 的95% CI上界≤0；同时也未满足预冻结 efficiency non-inferiority path，则停止。具体统计式和多重比较处理必须写入 E3 preregistration。
4. **No early success claim**：30/100阶段即使结果很好，也只能决定“继续”，不能替代300+主分析。
5. **Denominator integrity**：每阶段全部任务与provider failure留在分母；不重试、不补预算、不因仓库困难删除任务。

E3 token 粗上限（若继续沿用2,200 tokens/task-arm）：30阶段约198,000；累计100约660,000；累计300约1,980,000。实际开始前应按E2真实token分布重新做保守预算，但不能用E3 outcome调预算。

建议时间：E2封板后第1–2周完成外部cohort与污染审计，第3周freeze/preflight，第4周E3-A；通过后第5周到E3-B；只有未触发停止才在第6–8周完成E3-C与报告。

## 7. 给 WebCodex 的直接执行指令

> 按 `docs/research/E1_E2_FAST_COMPLETION_PLAN.md` 接手。优先级固定为：E1快速封板 → E2保质量快速结束 → E3按30/100/300阶段推进并允许按预注册规则提前停止。先完成所有zero-call检查，不得自行启动provider调用。E1-B真实12-task只能在能访问冻结sealed assets的主机上，使用已记录的exact command并获得单独授权后执行。E1 Wave B必须无条件新增18条、同配置且不依据Wave A outcome调参。E2取n=100，主矩阵保持全量，节省只来自配置等价control去重、30-task诊断消融子集和有限并发。E3不得在E2 gate前启动，也不得用30/100的好结果提前声称外部有效。日志只写 `PROGRESS_LOG_ARCHIVE.md`，Roadmap只保留当前状态、下一门槛与结果链接。
