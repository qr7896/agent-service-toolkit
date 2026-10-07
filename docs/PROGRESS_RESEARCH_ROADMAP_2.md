# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-07。当前唯一执行入口；背景见[Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，历史过程与旧页面原文见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

## 0. 最新结论

**新冻结版本四参考Gold区分4/4；语义门槛未过、machine trusted0。** 实际4请求11,909 tokens，Flash only、retry0，producer seal后独立Gold attempted4/区分4。[逐项结果/接线更正](research/E1C2_EXECUTION_PLAN_RESULTS_2026-10-07.md)、[公开收据](../data/e1c_evaluation_2_execution_plan_results.json)。

找到根因：内部runner重入配置覆盖外层executor，旧paid的API/类型hook并未生效；原得分、负结果不改，组件效果解释已更正。修复后实际API/uncertainty/plan产物4/4，不靠preflight声明作证。工程1402 passed/4 skipped/33 warnings（60.81秒），Ruff/预算V3/compact preflight过，不等于修复率。当前无下载需求。

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
| witness grounding零费审计 | 全4审计，1项trace期待/公开guard未在失败trace观察到 | 其余也未获语义证书；组件未接live |
| 机器可信/Agent修复/E2 | machine0、新repair/official resolved未做 | 不报30/30，不开Fresh30 |

## 2. 当前瓶颈

正常control与数值四参考门槛本轮已通过。剩余首要问题是**公开期待有依据、候选失败支持对应行为义务**。当前数组候选Gold区分，但期待引用是trace，实际在参数校验失败，没有观察到公开guard位置；不能直接升格，也不能只因位置不同断言毫无关联。

下一版先让期待角色检查进入oracle lock前、源调用链/实际失败位置形成“API义务候选／原报故障机制未证”双标签。trace/code-only引用只说明背景，不可捏造期待；自然语言未分类也不是自动通过。zero正负例后另冻一次四参考，Gold与语义分别核算。

## 3. 严格验收定义

1. 生成侧只用公开issue允许投影与exact-base生产源，不输入原测试断言/题面可执行答案/Gold/官方评分日志。
2. 定位规则无task-ID→文件表、无人工挑文件；保留来源、rank、窗口预算与SHA。
3. 两次有效normal control和两次稳定非setup目标失败；独立Gold消除不自动授予行为忠实性证书。
4. 新probe须对齐公开行为义务，unknown保持unknown；自动语义门槛尚未完成。
5. Agent补丁由独立官方评分判resolved。代码回归、可信复现和30/30 resolved是三个不同目标，不best-of合并。

## 4. 当前唯一执行顺序

| 顺序 | 下一步 | 放行证据 | 未过时 |
|---|---|---|---|
| 1 | 期待角色在oracle lock前接线 | trace/code-only不能直接充当desired behavior；明确接口义务或公开自然语言来源 | unknown/弃答，不造答案 |
| 2 | 实际失败与生产调用链分账 | API参数支持问题与公开报告故障位置区别记录；两次trace/source SHA绑定 | 不因Gold消除自动trusted |
| 3 | 跨仓库零费正负例与工程门槛 | 有效期待/错误trace期待/有效normal/错误setup/未知语义覆盖 | 不付费盲扩批 |
| 4 | 新方法冻结后一次同四参考 | Gold与语义分别核算，完整hook真实产物、约束不改 | 原namespace不重跑，不best-of |
| 5 | 同版完整九准入DEV/有限native覆盖 | 保留固定12分母，行为忠实性/cross-repo gate | 不把screen4当全12 |
| 6 | 新不重叠canary预注册一次 | 方法先冻后选，可信≥2/3且行为一致 | 永久封存回DEV |
| 7 | Agent patch/独立official grade | 同方法预算baseline/treatment小修复证据 | 无收益不扩批 |
| 8 | 同版旧DEV30→另授权Fresh30 one-shot→E2 | 单一冻结身份逐题resolved | 不承诺30/30，Fresh30失败不回调 |

每个新付费实验先列精确命令/Flash/次数/≤100,000 tokens，不Pro、不自动retry。execution-plan v1/v2及之前所有已started的smoke/freeze/run/Gold/audit禁止重跑；修改方法另立namespace，不改旧源/预算/账本。本轮4/4数值门槛已过但语义未过，停止本轮paid扩批，不开第6canary。当前没有新live/canary命令待执行。

## 5. 时间与停止条件

[原一周计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)保持原预注册。本轮解决执行链并首次得到同版四参考Gold4/4，但不能据此承诺一周或30/30。可控交付是期待锚定、候选行为分账、跨仓库反例与一次冻结DEV实证；语义门槛未过就不抽新独立任务、不继续同方法采样。

## 6. WebCodex与本机安全

云端可接源码、无模型单测和脱敏摘要，使用uv.lock；exact-base源码/镜像/私有.codex/凭证不会随Git同步。缺材料明确INFRA_BLOCKED；[接手说明](research/NEXT_SESSION_HANDOFF.md)给出安全检查命令。旧bridge白名单未扩，不假称新paid入口云端端到端已验证，不开裸Docker daemon。

本轮未下载/删除镜像或重启Docker，未改IPC/VHD/registry/proxy/tunnel/密钥。全部实验负结果和备份保留。sealed TEST/C5/Fresh30/SERBench私有Test500/Agent repair/E2仍关闭。

## 7. 更新纪律

本页只维护最新状态和可执行待办，逐轮日志只追加集中续档。此前本页及交接页的多份“当前/最新”快照已原文移入2026-10-07集中归档，Git历史也保留；不要按归档旧命令操作。原协议、结果、预算、response/state/ledger/seal均不回填。
