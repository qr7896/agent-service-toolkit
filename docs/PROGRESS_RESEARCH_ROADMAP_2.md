# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-07。当前唯一执行入口；背景见[Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，历史过程与旧页面原文见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

## 0. 最新结论

**期待门槛版Gold3/4，未保留前版4/4；machine trusted0、E1-C未封板。** 本轮9 Flash请求/30,477tokens、retry0；三个候选独立Gold区分，一项期待拒绝后弃答，不评分。[完整新结果](research/E1C2_EXPECTATION_RESULTS_2026-10-07.md)、[公开收据](../data/e1c_evaluation_2_expectation_results.json)。旧4/4不改，不best-of拼分；成本增加/覆盖下降，不能说效果提高。

零费诊断自动派生公开A normal，在两份缓存上各两次完成；实际上1task/1唯一程序/4次normal运行，不是Agent输出或额外成功题。期待门槛/公开对照grammar已实际接线，但比较报告如何形成有来源的行为假设仍待验证。工程1419 passed/4 skipped/33warnings（113.65秒），Ruff/预算V3/compact preflight过，不是repair rate。无新下载需求。

## 1. 已完成与尚未完成

| 环节 | 实际证据 | 边界 |
|---|---|---|
| DEV12基础设施 | 12镜像身份曾现场核验；双准入9/12 | 每次核验现场，异常留固定12分母 |
| 自动源码窗口/入口/guard | 公开issue与exact-base生产源、来源与SHA | 非人工选文件不等于语义正确 |
| 五批历史独立canary | 1/3、0/3、1/3、0/3、0/3封存 | 未达≥2/3；不再称独立调参 |
| 历史API/类型/codec版本 | Gold3/4、2/4、2/4保持 | 内部配置覆盖hook，效果归因不成立 |
| v1执行计划零费 | outer=true/inner=false；smoke/audit封存、付费0 | 原型负证据，不覆盖旧源 |
| v2真实完整执行链 | 五份旧probe零费5/5产物、1自身类型观测；新paid4/4产物 | 不将回放叫新生成；类型组件paid未触发 |
| v2四参考新生成 | 4请求11,909tokens；正常control与重复base失败、Gold4/4 | 固定12/九准入/screen4分账，不是完整DEV或独立成绩 |
| 前版witness grounding零费审计 | 全4审计，1项trace期待/公开guard未在失败trace观察到 | 其余也未获语义证书；组件未接live |
| 新期待门槛版 | 期待在lock前筛查、公开A/B/共享输入源绑定；Gold3/4 | 错误期待被拒，但新生成覆盖未保；unknown不trusted |
| 公开normal零费feasibility | 自动派生1程序、4次normal通过、Gold读取0 | 不是模型输出，未接live，不拼分 |
| 机器可信/Agent修复/E2 | machine0、新repair/official resolved未做 | 不报30/30，不开Fresh30 |

## 2. 当前瓶颈

前版数字4/4、本版3/4，问题已缩到**期待来源与公开比较事实的解释/传递**。trace/code不能充当期待；本轮模型反复选择code quote，被拒后认为没有期待而弃答，尚未生成真正公开A/B对照。

公共原文仍完整保留；两轮拒绝反馈没结构化带回已经可识别的比较关系，不是原文删除，也不能直接归因于反馈。零费实际运行已证明同一个自有输入下A normal可行，但A工作不证明B必须具备全部相同能力。下一版须把明确请求、回归报告、比较报告与unknown分账；比较形成的期待明确标推断研究假设，不冒充原文承诺/原报exact输入，不从Gold/原断言补答案。

## 3. 严格验收定义

1. 生成侧只用公开issue允许投影与exact-base生产源，不输入原测试断言/题面可执行答案/Gold/官方评分日志。
2. 定位规则无task-ID→文件表、无人工挑文件；保留来源、rank、窗口预算与SHA。
3. 两次有效normal control和两次稳定非setup目标失败；独立Gold消除不自动授予行为忠实性证书。
4. 新probe须对齐公开行为义务，unknown保持unknown；自动语义门槛尚未完成。
5. Agent补丁由独立官方评分判resolved。代码回归、可信复现和30/30 resolved是三个不同目标，不best-of合并。

## 4. 当前唯一执行顺序

| 顺序 | 下一步 | 放行证据 | 未过时 |
|---|---|---|---|
| 1 | 零费期待来源类型与prose锚 | 明确接口请求/公开回归/公开比较/unknown，trace/code不作期待 | 不造literal期待 |
| 2 | 比较报告推断合同先定协议 | inferred_from_public_comparative_report明确标签、源码scope与反例、公共literal约束 | 不暗改本轮标准追回4/4 |
| 3 | 比较事实结构化附回拒绝反馈 | 原prose引用/A-B关系有来源；让模型生成A/B同自有输入 | 派生normal仅feasibility，不当Agent输出 |
| 4 | 跨仓库正负例/工程→新冻四参考 | Gold/语义/报告机制分账，真实完整hook产物 | 原namespace不重跑，不best-of |
| 5 | 两gate过后同版九准入/native | 保留固定12分母，行为/cross-repo gate | 不把screen4当全12 |
| 6 | 新不重叠canary预注册一次 | 先冻完整方法后选，可信≥2/3且行为一致 | 封存回DEV |
| 7 | Agent patch/独立official grade | 同方法预算baseline/treatment小修复证据 | 无收益不扩批 |
| 8 | 同版旧DEV30→另授权Fresh30 one-shot→E2 | 单一冻结身份逐题resolved | 不保证30/30，不回调Fresh30 |

每个新付费实验先列精确命令/Flash/次数/≤100,000tokens，retry0、不Pro。expectation-reference-dev-v1和所有历史已started的smoke/freeze/run/Gold/audit禁止重跑/改旧源/账本，新方法另立namespace。本轮停止paid扩批，不抽第6canary；当前无新live/canary命令待执行。

## 5. 时间与停止条件

[原一周计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)保留原预注册，不承诺一周或30/30。本轮Gold覆盖下降、花费增加，没有新语义可信成绩；不要继续重复采样。先交付期待来源协议、结构化比较事实与跨仓库反例，再一次新冻结DEV实证，未过不抽新独立任务。

## 6. WebCodex与本机安全

云端可接源码、无模型单测和脱敏摘要，使用uv.lock；exact-base源码/镜像/私有.codex/凭证不会随Git同步。缺材料明确INFRA_BLOCKED；[接手说明](research/NEXT_SESSION_HANDOFF.md)给出安全检查命令。旧bridge白名单未扩，不假称新paid入口云端端到端已验证，不开裸Docker daemon。

本轮未下载/删除镜像或重启Docker，未改IPC/VHD/registry/proxy/tunnel/密钥。全部实验负结果和备份保留。sealed TEST/C5/Fresh30/SERBench私有Test500/Agent repair/E2仍关闭。

## 7. 更新纪律

本页只维护最新状态和可执行待办，逐轮日志只追加集中续档。此前本页及交接页的多份“当前/最新”快照已原文移入2026-10-07集中归档，Git历史也保留；不要按归档旧命令操作。原协议、结果、预算、response/state/ledger/seal均不回填。
