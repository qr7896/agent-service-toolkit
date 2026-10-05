# Roadmap 2：E1-C evaluation_2 当前状态与执行顺序

状态日期：2026-10-05。本页是当前执行入口；背景见 [Roadmap 1](PROGRESS_RESEARCH_ROADMAP.md)，逐轮过程见[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。本页不再堆叠历史“最新快照”。

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
| 独立hybrid canary v3 | 方法先冻、身份后选；三镜像摘要一致，压缩4.261GiB | 待用户终端直连下载；模型0调用、未读issue |
| 新版 Agent 补丁 + official grade | 尚无结果 | 未运行 |
| 严格同版 DEV30 / Fresh30 / E2 main | 尚无结果 | 保持门槛关闭 |

**现存人工环节：** Gold 区分不能自动证明 probe 忠实表达 issue。4/12 包含人工语义审核，底层 `trusted_reproducer=false` 保持原样。后续分别报告自动准入和人工审核后结果，不合称“全自动可信”。

## 2. 当前瓶颈与最新入口

**当前下一步是新hybrid canary v3用户直连下载，不是重跑旧批。** 自动生产覆盖、raw JSON响应分账、源码import前提、构造目标重分期、评分前B→A控制器与回退oracle一致性已完成开发/回归。新生成pilot原始3/12保留；controller v2零调用缓存4/12跨2仓库，恢复基线但未证明胜过历史v4或独立泛化。原始三题v2负结果不回填。详见[本轮研究报告](research/E1C2_DEV_CONTRACT_STUDIES_2026-10-05.md)。

新canary v3身份：Flask-5063、PyVista-4226、SymPy-17150，排除全部历史identity后metadata-only盐选，无人工挑题/文件。方法SHA`978a0b86ba70f7cf9c7fd9add3a123c682202afb73d401ade4cb15b3c2bc7a44`；官方/mirror摘要3/3一致，官方仅7请求/26,299正文bytes经7892。大文件直连，未下载；三题issue未读、模型0调用。新批Flash最多6请求/60,000tokens、每题20,000、不重试；见[冻结协议](research/E1C2_HYBRID_CANARY_V3_METHOD_2026-10-05.md)和[用户终端/接手入口](research/NEXT_SESSION_HANDOFF.md)。先下载→admit/public/preflight→付费run→独立Gold/语义审核；≥2/3才推进repair。环境或模型失败如实占固定分母3，不换题。

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
| 3 | DEV研究与完整回归已记录 | 新hybrid3/12；v2缓存4/12，含人工审核；1115passed/4skipped/0failed | 缓存不是独立确认，pytest不是repair |
| 4 | 新canary v3已冻，等待下载 | 下载→官方双准入→冻结输入→Flash≤6/60k→判别，一次≥2/3 | 失败封存，不能后验补规则再称独立 |
| 5 | 新修复配对小实验 | 同模型/预算 baseline/treatment，独立 official grade | 无净收益不扩批 |
| 6 | 同版旧 DEV30 | 单一冻结身份、30 行，目标 30/30 resolved | 保留失败分布，Fresh30 关闭 |
| 7 | Fresh30 one-shot | 门槛真过后先选新身份、再读内容、一次运行 | 如实报告，不回调规则 |
| 8 | E2 / E3 | 新预注册、样本、预算、提前停止条件 | operational PASS 不代表已完成 |

已封存 canary v2：`deepseek-flash`、non-thinking、temperature 0；每题≤1请求 / 14,000 provider tokens；整批≤3请求 / 42,000；单请求输出≤2,600；retry=0。实用13,783 tokens。后续“弹性预算”不改写这一冻结身份。

## 5. 一周交付

[10 月 1–7 日详细计划](research/E1C2_ONE_WEEK_PLAN_2026-09-30.md)列明原逐日工作、预算、消融与停止条件。截至10月5日，环境修复、两批canary封存、DEV合同A/B/新控制器开发与回归已完成，新canary等待用户下载。DEV本组可见usage106,543（含SDK错误4,281；非已核账单），加本日v2canary为120,326，系列非无限预算。独立确认及Agent repair未完成，不能承诺10月7日必达30/30。

可控交付是输入隔离和自动定位检查、一个通用复现改进、同预算 DEV 消融、冻结记录、独立结果或明确阻塞报告、可接手的状态包。**30/30 保留为目标；当前证据不足以承诺一周必达。**

重点改进：固定 issue 行为合同，限定执行反馈可修改的部分，保留明确弃答。它针对“失败候选不一定忠实于 issue”的瓶颈。已有 canary v2 方法不改；新 DEV 方法另立版本，再先冻结不重叠 canary。

## 6. WebCodex 接手

- 云端可以接源码、单测、文档和公开摘要，使用提交的 `uv.lock`。
- 本机镜像、`.codex` 原始证据、WSL 盘和 tunnel 凭证不会随 Git 同步。桥接端到端未验证，不假定云端可访问本机 Docker。
- 大文件仍由用户终端直连；长任务先确认执行器不会受已有 120 秒通道限制。
- 缺原始材料时明确报告，不虚构复跑。直接使用[交接说明](research/NEXT_SESSION_HANDOFF.md)。

## 7. 更新纪律

当前状态仅更新本页；逐轮日志只写[集中续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。旧协议和结果保持原样。原全文见[完整历史快照](PROGRESS_RESEARCH_ROADMAP_2_HISTORY_2026-09-30.md)，其中“当前/下一步”只指其原日期。
