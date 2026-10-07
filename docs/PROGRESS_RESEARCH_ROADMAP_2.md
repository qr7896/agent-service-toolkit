# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-07。当前唯一执行入口；背景见[Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，历史过程与旧页面原文见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

## 0. 最新结论

**公共报告锚版Gold4/4、异常或缺失keyword对应3/4；machine trusted0，E1-C未封板。** 实际6 Flash请求21,400tokens、retry0；公开A/B正常-目标对照真正执行，期待引用prose锚并明确推断来源。producer seal后独立Gold attempted4/区分4，不是完整DEV/独立/Agent修复。[逐项结果与严格边界](research/E1C2_REPORT_ANCHOR_RESULTS_2026-10-07.md)、[公开收据](../data/e1c_evaluation_2_report_anchor_results.json)。

新例外观察器只记真实builtin异常匹配摘要/公开缺失参数，未认语义资格。v1因CRLF/LF SHA差异在probe前停止，负记录保留；v2验证原副本摘要、LF投影和容器文件/Git canonical blob，不改原源码，并保持缺dateutil环境。另项仅API行为差异，原报guard机制未证。最终1436 passed/4 skipped/33warnings（104.66秒），Ruff/预算V3/compact preflight过，工程数非修复率，当前无下载需求。

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
| 前版严格期待门槛 | 期待在lock前筛查、公开A/B/共享输入源绑定；Gold3/4 | 错误期待被拒，但新生成覆盖未保；unknown不trusted |
| 公开normal零费feasibility | 自动派生1程序、4次normal通过、Gold读取0 | 不是模型输出，未接live，不拼分 |
| 公共报告锚新版本 | 新假设口径下Gold4/4，真实A/B输入表达式/source绑定 | 前版3/4不回填，不是严格前版过关 |
| 真实异常观察与双source身份 | v1失败保留，v2观察3/4对应；CRLF/LF原副本/有效文件/Git blob核对 | 不等于语义证书或抵抗恶意程序的attestation |
| 机器可信/Agent修复/E2 | machine0、新repair/official resolved未做 | 不报30/30，不开Fresh30 |

## 2. 当前瓶颈

公共比较/回归报告现在可以支持明确标记的call_completes假设，错误trace/code期待仍拒。期待原始prose引用、Source-import绑定、normal两过、target重复失败和Gold区分均已有记录；不能再只加提示或原地采样。

剩余是**受限语义资格与校准**：公开输入约束是否满足、真实调用是否符合接口义务、实际异常对应哪个报告机制。新observer三个任务有真实事件对应，另一项在参数校验失败而非原报guard，须分别标API兼容行为与原故障机制。任何source帧/同消息/Gold组合不自动trusted；必须验wrong fixture、影射、生产对象被改、shape/输入约束偏离、环境/源变化等反例，校准后再冻结证书scope。

## 3. 严格验收定义

1. 生成侧只用公开issue允许投影与exact-base生产源，不输入原测试断言/题面可执行答案/Gold/官方评分日志。
2. 定位规则无task-ID→文件表、无人工挑文件；保留来源、rank、窗口预算与SHA。
3. 两次有效normal control和两次稳定非setup目标失败；独立Gold消除不自动授予行为忠实性证书。
4. 新probe须对齐公开行为义务，unknown保持unknown；自动语义门槛尚未完成。
5. Agent补丁由独立官方评分判resolved。代码回归、可信复现和30/30 resolved是三个不同目标，不best-of合并。

## 4. 当前唯一执行顺序

| 顺序 | 下一步 | 放行证据 | 未过时 |
|---|---|---|---|
| 1 | 零模型语义资格scope与反例 | 输入约束/production调用/期待来源/真实异常分别有依据；unknown不晋升 | 不把3/4对应叫可信 |
| 2 | 跨repo校准与观察器身份/环境验收 | wrong fixture/alias shadow/对象修改/shape偏离/同消息误用/源码与环境变化反例 | 不因Gold自动认证 |
| 3 | 完整method含observer/双source身份freeze | classifier定义、支持与不支持边界、源码/输入/预算先冻 | 不改旧namespace |
| 4 | 同版四参考/九准入DEV与有限native | Gold、受限行为资格、原报机制分账，保留固定12 | 不把screen4报全12 |
| 5 | 新不重叠canary一次 | 全历史排除，方法先冻后选；可信≥2/3且行为一致 | 负结果封存回DEV |
| 6 | Agent patch/独立official grade | 小型baseline/treatment同预算修复证据 | 无收益不扩批 |
| 7 | 同版旧DEV30→另授权Fresh30 one-shot→E2 | 单一冻结身份逐题resolved | 不保证30/30，不回调Fresh30 |

每个新paid实验先列精确命令/Flash/次数/≤100,000tokens，不Pro/retry。report-anchor-reference-dev-v1、exception-observation-zero-v1/v2及所有已started的run/smoke/audit/Gold禁止重跑、改旧source/预算/账本。本轮不再paid扩批；语义资格未认证，不抽第6canary、TEST/Fresh30/repair/E2不打开。当前无新live/canary命令待执行。

## 5. 时间与停止条件

[原一周计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)保留预注册。本轮新假设口径Gold恢复4/4且成本较前版30,477下降至21,400，但不能称隔离因果收益、严格原口径达标或一周/30题保证。可控交付是有边界的行为资格校准、完整freeze和一次同版DEV实证；未过不抽新独立任务。

## 6. WebCodex与本机安全

云端可接源码、无模型单测和脱敏摘要，使用uv.lock；exact-base源码/镜像/私有.codex/凭证不会随Git同步。缺材料明确INFRA_BLOCKED；[接手说明](research/NEXT_SESSION_HANDOFF.md)给出安全检查命令。旧bridge白名单未扩，不假称新paid入口云端端到端已验证，不开裸Docker daemon。

本轮未下载/删除镜像或重启Docker，未改IPC/VHD/registry/proxy/tunnel/密钥。全部实验负结果和备份保留。sealed TEST/C5/Fresh30/SERBench私有Test500/Agent repair/E2仍关闭。

## 7. 更新纪律

本页只维护最新状态和可执行待办，逐轮日志只追加集中续档。此前本页及交接页的多份“当前/最新”快照已原文移入2026-10-07集中归档，Git历史也保留；不要按归档旧命令操作。原协议、结果、预算、response/state/ledger/seal均不回填。
