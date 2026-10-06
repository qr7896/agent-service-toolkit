# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-06。本页是当前执行入口；背景见 [Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，逐轮过程见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。本页不再堆叠历史“最新快照”。

## 1. 完成情况

| 环节 | 证据 | 状态 |
|---|---|---|
| DEV12 身份、镜像 | 12 张官方等价镜像曾完成本地核对 | 已完成准入；每次运行仍须核验现场 |
| DEV12 官方双准入 | Base-Fail 11/12；Gold-Pass 9/12；同时满足 9/12 | 异常题保留在固定分母 |
| 自动定位 | 9 个准入任务的公开 issue / exact-base 生产窗口冻结 | 无人工选文件；有窗口不等于定位正确 |
| DEV v4 复现 | 8 次 Flash 请求 / 25,424 tokens；5 个重复失败候选、4 个 Gold 区分 | 人工语义审核后可信 4/12，跨 2 仓库 |
| 旧 DEV 零调用形态审计 | v4 的 9 条记录：3 个调用后标记、1 个值比较、1 个吞异常、2 个不支持结构、2 个无候选 | 只做结构筛查；9/9 语义状态仍未验证，不增加可信数 |
| 独立 canary v1 | 2 请求 / 5,755 tokens；可信 1/3 | 未达 ≥2/3；负结果封存 |
| 独立 canary v2（传输修订） | 3/3 镜像/双准入；3 次 Flash、13,783 tokens；1 个重复失败候选、Gold 区分 0 | 可信 0/3，未达 ≥2/3；负结果封存 |
| 旧DEV合同A/B v1/v2 | v1 B因SDK处理截断中止、不重试；v2两臂各9题完成，Gold各1/12 | 无证据直接取代基线；[分账报告](research/E1C2_DEV_CONTRACT_STUDIES_2026-10-05.md) |
| source-contract hybrid | 新生成15请求/29,864 tokens，Gold3/12；controller v2缓存回放4/12、零新增调用 | 仅DEV开发证据，含人工语义审核；不是独立成绩 |
| 独立hybrid canary v3 | 镜像3/3、双准入2/3；3Flash请求/7280tokens | 可信1/3，固定分母3，负结果封存 |
| 最新旧DEV hybrid v3 | 弃答STOP/路径锚点；9题新生成、12请求/24712tokens | 可信3/12（含人工审核），未保留四条参考，开发门槛失败 |
| Counterfactual零调用 | 九条B审计：1 supported/5 unproven/3 abstain；同元素对照两次拒错fixture，缓存回放4/12 | 仅局部开发证明，target/oracle不改，非独立/非新生成成绩 |
| Counterfactual新生成 | 原九题/固定12，13Flash请求26762tokens，Gold4 | 经人工可观察行为审查4/12，array不是原报告同一报错位置；四参考保留 |
| 第4批独立canary | 镜像3/3、双准入2/3；3请求5596tokens | 0/3负结果封存，不换题/重算 |
| 输入事实保真/导入归属定位 | 公开fixture AST无assert/输出答案，3题4safe块；自动找到继承fit，关系/深度/seed/SHA可追踪 | 零调用审计与新协议已冻，不手选文件 |
| Faithful DEV原生成 | 原九题16请求37593tokens，无provider失败/重试 | 原验证INFRA_INVALID保留，不回填、不报0/12 |
| 运行态恢复/完整0付费回放 | engine/9个image健康；9题执行、6候选Gold5/12，无缺缓存角色 | 原四参考保留、新Lasso候选；人工行为审查5/12，机器trusted仍0 |
| 下一独立canary v5 | 52份方法文件先冻结，排除304身份后选SymPy-22080/Sphinx-9180/pytest-7749；官方摘要3/3一致 | 等用户直连下载2.946GiB；Flash≤6/60000尚未调用，新题issue/Gold未读 |
| 新版 Agent 补丁 + official grade | 尚无结果 | 未运行 |
| 严格同版 DEV30 / Fresh30 / E2 main | 尚无结果 | 保持门槛关闭 |

**现存人工环节：** Gold 区分不能自动证明 probe 忠实表达 issue。最新5/12包含人工可观察行为审查，底层`trusted_reproducer=false`保持原样。后续分别报告自动准入和人工审核后结果，不合称“全自动可信”。

## 2. 当前瓶颈与最新入口

**Docker已恢复；当前推进新独立v5，不重跑旧题。** 第4批0/3已封存，回DEV补公开输入事实保真与生产import/reexport/inheritance定位。Faithful源生成16请求37593tokens，原无效环境验证保留；恢复后新namespace完整0付费回放Gold5/12、四参考保留、跨两仓库，新增Lasso候选输入/终端API与public事实相符。人工可观察行为审查5/12，不是自动语义证明；源生成成本较此前26762增加约40.5%，没有已控制消融的因果/省费结论。[完整结果](research/E1C2_FAITHFUL_REPLAY_RESULT_2026-10-06.md)、[公开gate](../data/e1c_evaluation_2_faithful_replay_dev_gate.json)。

当前外部步骤是用户终端直连下载新三张，压缩层2.946GiB，最大单张空间守卫26.123GiB；D现场约38.64GiB。官方Docker小metadata经授权7892共7请求/25899正文bytes，所有大blob仍0、不走代理。镜像未在本地，新题正文/Gold未读；完整[下载命令、进度与ETA](research/E1C2_FAITHFUL_CANARY_V5_DOWNLOAD_2026-10-06.md)。完成后依次admit/public/preflight，现场核准预算，再列唯一Flash run，不能按旧入口重复缓存回放。

获准同一次停机备份改名两个旧IPC目录后启动成功，备份均保留；没有删除、改注册表/WSL/镜像/VHD/代理/tunnel或读取密钥。真实engine/9个immutable image均核验、评分后engine仍健康。新回放preflight/run/gold均完成、provider0、缺缓存0，**上述命令不能再执行**。原错误state与日志不回填。工程完整单次1151passed/4skipped/33warnings/0failed（54.23秒）；首次非UTF8测试命令的环境守卫失败记录保留，未弱化断言/跳过。规定V3 preflight按原命令ready=true。

第4批method/identity/transport原件与最早0调用receipt保持，当前由[封存结果](research/E1C2_COUNTERFACTUAL_CANARY_V4_RESULT_2026-10-06.md)补充执行状态：PVLib环境兼容失败，SymPy缺关键窗口而弃答，scikit两个probe base通过。方法/样本不重抽，不能在本批补规则重报独立。下载/admit/public/run/gold旧命令不再运行，TEST/C5/Fresh30继续关闭。

canary v3保留身份Flask-5063、PyVista-4226、SymPy-17150，方法SHA`978a0b86ba70f7cf9c7fd9add3a123c682202afb73d401ade4cb15b3c2bc7a44`未变。用户完成下载；Flask/SymPy双准入、PyVista Base没有明确目标失败记录，保留分母。两题模型共3请求7280tokens；Flask候选行为偏离且Gold不区分，SymPy经审核可信，最终1/3。见[完整结果](research/E1C2_HYBRID_CANARY_V3_RESULT_2026-10-05.md)。不得换题/在已看身份调参后重称独立；repair、sealed TEST/C5/Fresh30继续关闭，冻结协议和下载收据作为历史保留。

下面是旧v2基础设施与负结果背景，不作当前执行命令：

2026-10-05 用户允许仅小型官方元数据使用本机 7892。新增并封存传输修订 `e1c2-canary-v2-metadata-proxy-v1`，保持原选择身份和 14 份方法文件。官方认证及 manifest 经代理，镜像站 manifest 直连，三张镜像摘要 **3/3 一致**；官方响应正文仅 **26,333 字节 / 6 请求**。新 seal 位于 `.codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1/image_transport.json`；原 direct-only 路径仍无 seal，历史失败保留。这是同一三题 cohort 的基础设施修订，不是新抽样。

用户已下载 **3/3 镜像**，本机image ID/源码身份及六项官方Base/Gold全部通过；公开issue/生产窗口3/3物化，各四个窗口。冻结新live身份后一次调用Flash三题，实际13,783 provider tokens（硬上限42,000、无重试）。可信复现 **0/3**，该批关闭。环境已可运行，主瓶颈转为生成与定位质量。

- 元数据代理限官方 token/manifest，最多 9 请求、200,000 字节/响应、2,000,000 字节累计正文；无跳转/重试，拒绝 blob URL。
- 下载只读取缓存 seal，镜像层通过空 ProxyHandler 直连；用户关闭 VPN 全局/TUN，Docker 保持 No proxy，再用新入口下载。
- 本批 `admit/public/live/Gold` 已执行并封存，不再重复。Seaborn输出回显/不可解析；Marshmallow构造fixture错误，Gold后仍失败；pytest因相关生产窗口不足而明确弃答。

完整结果与账本摘要见[第二批负结果](research/E1C2_CANARY_V2_AMENDED_RESULT_2026-10-05.md)。[传输协议](research/E1C2_CANARY_V2_METADATA_PROXY_AMENDMENT_2026-10-05.md)、[live协议](research/E1C2_CANARY_V2_PROXY_LIVE_PROTOCOL_2026-10-05.md)和原[直连尝试](research/E1C2_CANARY_V2_DIRECT_DOWNLOAD_HANDOFF_2026-09-30.md)保留，命令只作历史证据。

## 3. 严格验收定义

1. **非公开断言输入**：生成侧只使用公开 issue 的允许自然语言投影与 exact-base 生产源码；不读测试断言正文、题面可执行断言、Gold、官方测试/评分日志。新生成的行为检查须有 issue 依据。
2. **非人工定位**：同一规则自动选择文件/符号/窗口，记录来源、排名、预算；无任务 ID→文件表、人工挑文件、逐题特例。
3. **可信复现**：无网络、不可变镜像，同一 probe 两次稳定 base 失败；独立 grader 中 Gold 消除失败；环境异常和语义不符不晋升。
4. **真实修复**：Agent 生成补丁，经盲态验证后由独立官方评分判 resolved。Gold-Pass 不算 Agent 修复成功。
5. **全通过**：代码回归零失败、同版 DEV30 30/30 resolved、Fresh30 30/30 是三个不同指标。固定分母、不合并版本最好结果、不把未运行算通过。

## 4. 待办与放行条件

| 顺序 | 工作 | 完成证据 | 失败分支 |
|---|---|---|---|
| 0 | v2 负结果与当前入口保全 | 原response/state/ledger不回填，公共摘要/结果页已写 | 不拼接旧DEV成功数 |
| 1 | 响应分类/行为合同已开发 | v1 SDK失败保留，v2 raw JSON两臂完整；issue oracle固定 | 无完整A/B优势，不包装增益 |
| 2 | 正对照/生产覆盖已开发 | API/类/traceback统一选择、生产AST/真实import证明，合成与旧DEV回归 | 定位覆盖不等于语义正确 |
| 3 | DEV研究与完整回归已记录 | Faithful回放Gold5/12；全仓1151passed/4skipped/0failed | 语义包含人工审查，工程通过不算repair |
| 4 | Counterfactual局部机制已实现 | 1case literal类型对照、生产guard来源、两次控制验证；四参考保持 | 5条unproven保留，未宣称通用语义证明 |
| 4b | Docker恢复＋0付费DEV回放已完成 | 同输入/代码/响应SHA，新provider0、无缺缓存，Gold5/12 | 不重跑、不把原错误验证回填成有效 |
| 4c | 新独立v5准备中 | 方法SHA7fe8bf6c1fa9c0acbe82915ba43410b0f95db65615bb3def949dc5b1801feab3先冻；metadata-only排除旧身份，用户直连下载 | 固定3无替补；≥2/3才另冻repair，失败封存，Fresh30关闭 |
| 5 | 新修复配对小实验 | 同模型/预算 baseline/treatment，独立 official grade | 无净收益不扩批 |
| 6 | 同版旧 DEV30 | 单一冻结身份、30 行，目标 30/30 resolved | 保留失败分布，Fresh30 关闭 |
| 7 | Fresh30 one-shot | 门槛真过后先选新身份、再读内容、一次运行 | 如实报告，不回调规则 |
| 8 | E2 / E3 | 新预注册、样本、预算、提前停止条件 | operational PASS 不代表已完成 |

已封存 canary v2：`deepseek-flash`、non-thinking、temperature 0；每题≤1请求 / 14,000 provider tokens；整批≤3请求 / 42,000；单请求输出≤2,600；retry=0。实用13,783 tokens。后续“弹性预算”不改写这一冻结身份。

## 5. 一周交付

[10 月 1–7 日详细计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)列明原逐日工作、预算、消融与停止条件。截至10月5日，三批canary均负结果封存；新counterfactual零调用机制及新生成4/12通过开发参考门槛，独立门槛仍未过。本次新增26762tokens，累计本日可见usage179080（含旧SDK错误4281，非核账单）。系列非无限预算，第四批最多60000，后续repair仍需单独门槛/预算，不承诺10月7日必达30/30。

可控交付是输入隔离和自动定位检查、一个通用复现改进、同预算 DEV 消融、冻结记录、独立结果或明确阻塞报告、可接手的状态包。**30/30 保留为目标；当前证据不足以承诺一周必达。**

重点改进：固定 issue 行为合同，限定执行反馈可修改的部分，保留明确弃答。它针对“失败候选不一定忠实于 issue”的瓶颈。已有 canary v2 方法不改；新 DEV 方法另立版本，再先冻结不重叠 canary。

## 6. WebCodex 接手

- 云端可以接源码、单测、文档和公开摘要，使用提交的 `uv.lock`。
- 本机镜像、`.codex` 原始证据、WSL 盘和 tunnel 凭证不会随 Git 同步。桥接端到端未验证，不假定云端可访问本机 Docker。
- 大文件仍由用户终端直连；长任务先确认执行器不会受已有 120 秒通道限制。
- 缺原始材料时明确报告，不虚构复跑。直接使用[交接说明](research/NEXT_SESSION_HANDOFF.md)。

## 7. 更新纪律

当前状态仅更新本页；逐轮日志只写[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。旧协议和结果保持原样。原全文见[完整历史快照](PROGRESS_RESEARCH_ROADMAP_2_HISTORY_2026-09-30.md)，其中“当前/下一步”只指其原日期。
