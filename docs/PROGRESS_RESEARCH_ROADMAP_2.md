# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-07。当前唯一执行入口；背景见[Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，历史过程与旧页面原文见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

## 0. 最新结论

严格DTO兼容修订完成，真实四参考screen **Gold区分2/4、机器可信复现0**，没有Agent补丁/official resolved，质量门槛未通过。本轮接口失败版9请求25,928 tokens；兼容版6请求18,038，合计15/43,966、Flash only、retry0。[逐项结果/完整验收](research/E1C2_UNIFIED_POLICY_CODEC_RESULTS_2026-10-07.md)、[可核对收据](../data/e1c_evaluation_2_unified_policy_codec_results.json)。

已完成工程回归1388 passed/4 skipped/33 warnings（93.81秒），Ruff与规定V3 preflight通过；工程数不是复现或修复率。当前不需要下载新镜像。

## 1. 已完成与尚未完成

| 环节 | 实际证据 | 边界 |
|---|---|---|
| DEV12基础设施 | 12镜像身份曾现场核验；Base-Fail11/12、Gold-Pass9/12、双准入9/12 | 每次仍核验运行现场；异常留固定12分母 |
| 非人工选文件 | 公开issue与exact-base生产源自动窗口/入口/guard来源和SHA | 覆盖与定位正确、语义忠实性是不同指标 |
| 历史独立canary | 五批1/3、0/3、1/3、0/3、0/3封存 | 都未达≥2/3；不能再调参后称独立 |
| API义务与类型观测 | 旧参考新生成分别Gold3/4、2/4 | 比较基线保留，不合并最好成绩 |
| 本轮单一政策 | 替换叠加System、公开Human不改；接口负结果已封存 | 9调用均解析拒绝，没有有效候选 |
| 本轮严格兼容 | 9旧响应零调用解码且五个code/oracle字段不改；真实screen2/4 | DTO兼容+canonical示例并改，不称单因素因果收益 |
| control/隐式协议审计 | 六新响应零执行审计，两份同动作control标记；六单测通过 | diagnostic未接live；同动作不自动证明无效，不同动作不证明独立 |
| 本版完整DEV/可信复现 | 未完成完整九准入；machine trusted0 | 四参考不能报DEV12全过 |
| 自动修复/E2/Fresh30 | 未运行新Agent修复与独立新任务 | 不提前开放 |

## 2. 当前瓶颈

兼容版SK13496与MM1252有稳定base失败且独立Gold消除；SK26289在list输入通过后弃答，尚未执行source-consistent输入假设；MM1359正常control落在同一故障配置而失败。问题在可执行的输入假设与正常控制，不是继续下载镜像或堆源码窗口。

源码无显式raise不能证明条件不会抛错；裸Name guard可能调用类型协议。公开约束、已观察事实、合成假设和unknown必须分账，假设不能叫原报告exact输入；也不能用Gold或原测试来填输入。

## 3. 严格验收定义

1. 生成侧只用公开issue允许投影与exact-base生产源，不输入原测试断言/题面可执行答案/Gold/官方评分日志。
2. 定位规则无task-ID→文件表、无人工挑文件；保留来源、rank、窗口预算与SHA。
3. 两次有效normal control和两次稳定非setup目标失败；独立Gold消除不自动授予行为忠实性证书。
4. 新probe须对齐公开行为义务，unknown保持unknown；自动语义门槛尚未完成。
5. Agent补丁由独立官方评分判resolved。代码回归、可信复现和30/30 resolved是三个不同目标，不best-of合并。

## 4. 当前唯一执行顺序

| 顺序 | 下一步 | 放行证据 | 未过时 |
|---|---|---|---|
| 1 | 零调用执行契约 | 公开约束/输入假设/control状态/目标API/未证项分栏，来源SHA可核对 | 不靠提示授予可信 |
| 2 | 正常配置与隐式协议有限探索 | 同动作审状态、不同动作也验独立；模型自身提出API-valid假设并实际执行 | 不手填array/date/assertion，不原报化 |
| 3 | 跨仓库零调用正负例、工程门槛 | 有效control/同故障假control/共享setup/类型冲突/未知入口均覆盖 | 不付费盲扩批 |
| 4 | 新method/input/budget/source freeze后一次旧四参考 | 同版新生成、对照保留、行为忠实性/cross-repo gate | 负结果seal；原namespace不重跑 |
| 5 | 同版完整九准入DEV | 固定12分母、预算与质量分账 | 不拼旧成功数 |
| 6 | 新不重叠canary预注册一次 | 方法先冻结再选择，可信≥2/3且行为一致 | 永久封存，回DEV |
| 7 | Agent patch/独立official grade | 同方法预算小型baseline/treatment修复证据 | 无收益不扩批 |
| 8 | 同版旧DEV30→另授权Fresh30 one-shot→E2 | 单一冻结身份、每题resolved记录 | 不保证30/30，Fresh30失败不回调规则 |

每个新付费实验先明示精确命令/Flash/次数/≤100,000 tokens，不使用Pro、不自动retry。已完成run/smoke/freeze/Gold/audit禁止再次执行；改变方法必须新namespace，不能改旧源或账本。当前没有新live/canary命令待执行。

## 5. 时间与停止条件

[原一周计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)保留，不改当时预注册。10月7日现有证据不能承诺一周或任何日期达到30/30。本轮付费screen已封存，停止重复采样；后续先交付可执行契约与跨仓库反例，再用一次冻结DEV实证决定是否继续。不能把增加回归数当研究效果。

## 6. WebCodex与本机安全

云端可接源码、无模型单测和脱敏摘要，使用uv.lock；exact-base源码/镜像/私有.codex/凭证不会随Git同步。缺材料明确INFRA_BLOCKED；[接手说明](research/NEXT_SESSION_HANDOFF.md)给出安全检查命令。旧bridge白名单未扩，不假称新paid入口云端端到端已验证，不开裸Docker daemon。

本轮未下载/删除镜像或重启Docker，未改IPC/VHD/registry/proxy/tunnel/密钥。全部实验负结果和备份保留。sealed TEST/C5/Fresh30/SERBench私有Test500/Agent repair/E2仍关闭。

## 7. 更新纪律

本页只维护最新状态和可执行待办，逐轮日志只追加集中续档。此前本页及交接页的多份“当前/最新”快照已原文移入2026-10-07集中归档，Git历史也保留；不要按归档旧命令操作。原协议、结果、预算、response/state/ledger/seal均不回填。
