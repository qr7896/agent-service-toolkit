# WebCodex 接手：E1-C evaluation_2

交接日期：2026-10-06。仓库：`qr7896/agent-service-toolkit`。先读 [AGENTS.md](../../AGENTS.md)、[当前 Roadmap](../PROGRESS_RESEARCH_ROADMAP_2.md)、[一周计划](E1C2_ONE_WEEK_PLAN_2026-09-30.md)，不要按历史文档的旧“下一步”直接运行。

## 当前状态

**最新：Docker已恢复，Faithful完整缓存回放完成：Gold5/12、新provider0、缺缓存0。** 原16Flash请求37593tokens生成不重试，原无效环境验证另留；四参考保留，新增Lasso可执行证据，人工可观察行为审查5/12，机器trusted仍0，不是Agent修复/独立成绩。[最新完整结果](E1C2_FAITHFUL_REPLAY_RESULT_2026-10-06.md)。四批独立canary1/3、0/3、1/3、0/3仍封存，不覆盖。

## 当前下一步：独立Faithful canary v5

开发gate通过，已先提交方法代码/协议b794f3a，再封存52份方法文件03ef71a；method SHA7fe8bf6c1fa9c0acbe82915ba43410b0f95db65615bb3def949dc5b1801feab3。新模块`evals.e1c_evaluation_2_faithful_canary_v5`，新目录`.codex/e1c/evaluation_2/faithful-canary-v5`。按既有metadata-only盐序排除所有历史/四批canary，选固定三题无替补；本次截至此处未读新issue/Gold、未调用provider或下载blob。完整[选题前协议](E1C2_FAITHFUL_CANARY_V5_METHOD_2026-10-06.md)。不要重复freeze-method/select；不要运行任何旧v4/v3/cached replay入口。

顺序：identity完成→仅官方task.yaml metadata/授权7892小官方manifest→用户关闭VPN全局/TUN且Docker No proxy直连下载→本机admit/public/preflight→列精确run命令/Flash/最多6请求/60000tokens→一次run/gold。每请求之前真实engine/image检查，不以磁盘loaded.json代替。任何失败保留现场，不自动provider重试、不调当前canary后继续称独立；≥2/3且人工行为审查通过才另冻repair，机器/人工结果分开报。Agent repair/TEST/C5/Fresh30/E2仍未开放。

identity和小型transport现已完成：排除304身份，SymPy-22080/Sphinx-9180/pytest-7749，identity SHAbaa5abda0f8151dba915a13975ab014ca4b5315080a1c7b39426d17ab96d294b；transport SHA3b1892690e3b70edbbf6a356ee349b1382a434e6562addbf2126432d1be6090d。官方摘要3/3一致，7官方Docker小metadata请求/25899正文bytes，blob/provider0。三镜像本地tag均不存在，压缩2.946GiB；大文件交用户，直接复制[本次终端命令](E1C2_FAITHFUL_CANARY_V5_DOWNLOAD_2026-10-06.md)。新题issue/Gold仍未读，不再调用select或重抽。下载后才按上述顺序零调用准入，未准入题保留分母3。

工程完整单次1151passed/4skipped/33warnings/0failed（54.23秒），专项22passed、指定预算/V3重点18passed/Ruff通过，原V3 preflight ready=true。首次测试漏UTF8参数/另一次V3强制UTF8导致子进程编码异常都保留为命令环境异常，不修改冻结代码/断言。所有原记录和IPC备份留存；不动VHD/镜像/tunnel，不假称tunnel端到端已验证。自10月5日可见usage仍222269，本轮新增付费0。云端缺本机.codex/source/image/执行器即INFRA_BLOCKED，不索取密钥或开放裸daemon端口。

## 已完成的缓存恢复准备（历史命令，不再执行）

以下保留当时Docker不可用的接手记录；其preflight/run/gold现已完成，结果见页首。不按旧“当前/未执行”继续运行。

普通Docker Desktop启动未恢复；日志明确旧`Docker\\run\\dockerInference` IPC socket不可访问，backend退出。用户确认尚待：仅正常停止Docker、备份改名`C:\Users\qq人\AppData\Local\Docker\run`目录、再普通启动。未触碰该目录/注册表/WSL/镜像/VHD/代理/tunnel。没有确认不可factory reset/global prune/强关全部WSL。Docker start/status查询可能后台挂起，勿再叠加启动或付费run。

确认并恢复后必须先真实`docker version`含Server及九个immutable image ID全部可inspect，再在本机执行以下**零模型**命令，任一步非0即停，不自动重试provider：

```powershell
foreach ($stage in @('preflight', 'run', 'gold')) {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_faithful_infra_replay $stage
    if ($LASTEXITCODE -ne 0) { throw "零付费回放停止于 $stage；保留原件，不自动重试。" }
}
```

新目录faithful-input-dev-v1-infra-replay-v1；cache-only model不使用真实钥匙、不发HTTP，原usage标upstream、新provider0。原方法/输入/preflight须与源freeze相等，绑定原全部response SHA；环境transport失败立即中断，不当软件证据。没有收集的缓存角色记controller缺失、不补模型调用、不假称模型弃答。独立[协议](E1C2_FAITHFUL_INFRA_REPLAY_2026-10-06.md)。截至交接回放未执行、无有效新分数。

新faithful_dev run/gold已执行（评分无效），严禁再次运行；三张v4镜像已下载、canary模型已结束，下方旧download/admit/public/run/gold均为历史。旧code/state不回填，新结果另立。原source freeze00ab5ba6ccb4a3755b014191ddcb2c6aee5d989dd13b67d4825390b68b457581，state516721755853e07629e02d0980ca405b3df5d2483f576802b29e5837e399888e，ledgerb590d99136bfa8a78201bbfec41b631fc4f501030631fd46929d824f1af91307。云端clone缺本机.codex/cache/执行器即INFRA_BLOCKED，不索取密钥、不伪造复跑或开放裸Docker端口。

有效DEV改进证据与独立≥2/3仍未达，不选新canary、不启动repair/TEST/C5/Fresh30/E2。自10月5日以来可见usage222269（含旧SDK错误4281，非账单核验），当前不续付费。最后工程单次1148passed/4skipped/33warnings/0failed（49.54秒），只表示代码回归，不保证Docker健康。所有原件及四批负结果保留，集中日志唯一入口。

## 以下为旧counterfactual/v4执行交接（历史，不按其“当前”操作）

历史counterfactual新生成4/12、13请求26762tokens，包含人工行为审核、非原报告同一错误栈，不是修复率；当时进入第4批准备。该批现已0/3结束，不能用旧DEV成功数补入分母。

新的入口为`evals.e1c_evaluation_2_counterfactual_canary_v4`；完整方法SHA`88df1067d0770a74ebe6d72d7eee74b78c3135defd1659b97c7b444c5fbd21ea`先冻，metadata-only排除301历史身份后选PVLib-1048/SymPy-20131/scikit-15535。identity SHA`06d55d996a2f6786d8718340d24c8debd5e8c2a566897cf55c3b24e114f3a337`；三张官方/mirror摘要一致，官方小metadata7请求/26342bytes，模型/blob0。公开[下载收据](../../data/e1c_evaluation_2_counterfactual_canary_v4_transport_receipt.json)。尚无该批泛化或修复结果，不能重选或改冻结依赖。

## 当前需要用户终端：直连下载新三张

压缩层PVLib1.587/SymPy1.064/scikit1.396GiB，总4.047GiB；实际安装体积更大，逐张磁盘守卫最大约29.52GiB。D现场约42.2GiB，不承诺最终空间必够，触发守卫即停、不自行prune。平均1–5MiB/s传输约14–70分钟，加校验/导入粗估40分钟–2小时；0.2MiB/s仅传输约5.8小时，单镜像硬超时6小时。逐层进度/速度/ETA、Range续传、SHA校验和导入心跳沿用原实现。

官方元数据seal已缓存，这条download不走7892/官方blob。先关闭VPN全局和TUN、Docker No proxy；显式空代理不能绕过系统级透明路由。只使用**新模块**：

```powershell
Set-Location 'D:\codex\working\project20260827'
Start-Transcript -Path '.codex\e1c\evaluation_2\counterfactual-canary-v4\download.log' -Append
try {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_canary_v4 download --timeout-per-image 21600
    if ($LASTEXITCODE -ne 0) { throw '下载中断，保留缓存/日志，不进入模型实验。' }
} finally {
    Stop-Transcript
}
```

返回verified_loaded=3后核验loaded/transport与Docker ID，再按同一新模块依次`admit --timeout 900`、`public`、`preflight`；每步非0即停，infra失败保留固定分母3、不换题。完成live freeze才列精确`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_canary_v4 run`：Flash≤6请求/60000tokens、单题2/20000、输出3000、重试0，沿用用户≤100000许可。结束后同模块`gold`独立评分/语义审核；一次可信≥2/3才另冻repair，不打开TEST/C5/Fresh30。下方所有v3历史命令不重跑。

原counterfactual_fast_dev已经run/gold完成，不重跑；原counterfactual_dev慢入口只有零调用freeze，不再另开付费trial。快输入适配逐次重查Git/base/生产SHA/image身份，上游九条输入与慢入口逐字一致，不是手选文件。云端无本机原件/执行器则报INFRA_BLOCKED，不复制密钥/公开评分答案或开放Docker裸端口。

最新工程全仓1127passed/4skipped/0failed/33warnings（142.85秒）。首次并发重负载导致原Streamlit8秒超时，已记录；失败项原样单独通过，再串行完整通过，未改超时或断言。所有旧模型试验/record/镜像/VHD/tunnel设置保留，累计本日可见usage179080（含旧SDK错误4281，非账单）。第4批至多60000，不无限扩批。

以下为上一轮DEV v3的历史要求，counterfactual机制现已完成；未支持的五条pair仍保留unproven，不能把局部证明扩大为普遍语义证明：

接手时先核验两份公开结果JSON和其中SHA对应本机原件；云端缺原件时报INFRA_BLOCKED，不虚构复跑。旧DEV v3已运行，禁止再次`run/gold`。下一步按DEV结果文档第1–5项：证明control/target非触发参数可比、生产前置条件校验、保持issue oracle、合成负例与四条参考不退化；仅旧DEV/合成，先零调用，不读取canary调参。证明不足不新增付费试验/新canary；新增付费须新身份和冻结Flash≤100000预算先列命令，不无限连跑。新方法尚未实现，不能算已验证创新或自动可信。

本机本轮回归1118passed/4skipped/0failed/33warnings（50.55秒），工程回归非修复率。下一独立样本/Agent repair/DEV30/Fresh30/E2都未启动。未扩大权限、开放Docker远程端口、修改tunnel或清理镜像/VHD；D盘约42.2GiB。

历史封板记录：先冻新方法/预算再metadata-only选题，三题Flask-5063、PyVista-4226、SymPy-17150不与历史identity重叠。官方/镜像站摘要3/3一致；当时未读issue/未付费。freeze SHA`978a0b86ba70f7cf9c7fd9add3a123c682202afb73d401ade4cb15b3c2bc7a44`，identity SHA`62649edc20998fad8f101a488ccbb22e0dff6343bf81a0fc3398e5fed5d1500d`。现已执行，保留[协议](E1C2_HYBRID_CANARY_V3_METHOD_2026-10-05.md)、[初始传输收据](../../data/e1c_evaluation_2_hybrid_canary_v3_transport_receipt.json)与各失败原件，不改原freeze或回填初始收据。

## 已完成的用户直连下载与执行（历史命令，不重跑）

已核压缩层分别1.067/2.130/1.064GiB，总4.261GiB（磁盘安装体积不是该数字）。D:现场42.77GiB空闲，逐张`20+6×compressedGiB`空间守卫，当前最大门槛32.78GiB；后续镜像解压仍可能触发stop，不承诺空间必够。不清理原记录、活动VHD或tunnel。下载显示每层MiB、速度、ETA、断点续传与Docker导入心跳。平均1–5MiB/s，传输约15–73分钟，加校验/导入粗估总40分钟–2小时；0.2MiB/s则仅传输约6小时，网络未知不保证时长。单镜像硬超时6小时。

关闭VPN全局及TUN（仅取消全局可能仍被TUN接管），Docker保持No proxy。官方小型manifest seal已缓存，本条download不请求官方或7892；镜像与blob显式空代理直连，不能绕过系统级透明路由。失败时保留日志，通知执行者，不自动重试。

```powershell
Set-Location 'D:\codex\working\project20260827'
Start-Transcript -Path '.codex\e1c\evaluation_2\hybrid-canary-v3\download.log' -Append
try {
    uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 download --timeout-per-image 21600
    if ($LASTEXITCODE -ne 0) { throw '下载未完成：保留缓存和日志，不进入模型实验。' }
} finally {
    Stop-Transcript
}
```

返回`verified_loaded=3`后，先核对loaded/transport/image ID，再执行以下**零模型**命令，任一步非0即停、不自行跳过：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 admit --timeout 900
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 public
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 preflight
```

所有阶段位于`.codex/e1c/evaluation_2/hybrid-canary-v3/`，保持live/public/source与grader-only分区。未双准入仍占固定分母，不替换题；预算预检须给出可执行候选数及reserve。仅在这些条件满足后，先报告以下精确付费命令：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 run
```

Flash非thinking、temperature0、最多6请求、单题20,000/整批60,000provider tokens、单请求输出3,000，SDK零重试。在用户已授权单实验≤100,000范围内，但不得无限串批或放宽此freeze。run完成才执行`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 gold`，独立零模型判别。记录provider返回alias而非不可变版本；可信≥2/3（机器与人工语义审核分开）才另冻Agent repair小实验。失败封存回DEV，不能在v3修规则后仍称独立；sealed TEST/C5/Fresh30继续关闭。

**云端限制**：新代码和身份在Git；小型metadata/transport seal仍在本机`.codex`。用户用本机终端完成下载；WebCodex须经已验证本机执行器读取这些摘要/调用限定入口，缺执行器、Docker、缓存或原件时报INFRA_BLOCKED。不能把云端clone误当本机、不打开Docker远程裸端口、不上传密钥；tunnel在线能力仍需独立检查。本次没有改Docker/tunnel设置。

封板时工程回归：1115 passed、4 skipped、33warnings、0failed（50.61秒）；最新1118见页首。skip与原套件一致，非修复率。指定重点18passed/Ruff通过/V3规定原preflight退出0。

## 已封存 v2 背景（不要按旧建议重建下一批）

DEV v4 经语义审核可信复现 4/12，不是修复率；首批独立 canary 1/3，已封存负结果。第二批经元数据代理修订、用户直连下载，3/3镜像及官方双准入通过；三次Flash一次执行共13,783 tokens，可信0/3，已封存。旧DEV的成功数不能补入这批分母。新版 repair / C5 / Fresh30 / E2 main 未运行。详见[第二批结果](E1C2_CANARY_V2_AMENDED_RESULT_2026-10-05.md)和[data摘要](../../data/e1c_evaluation_2_canary_v2_amended_result.json)。

canary v2 方法 SHA：`fd58671dcdb923e70b7f018362682802849c54651655e21d051828e1d6f4d14b`；identity SHA：`a22311ffc4dd41c379e839e5618bccb35164367b35b9a3797bf5f17bb3dba997`。以 [freeze JSON](../../data/e1c_evaluation_2_canary_v2_method_freeze.json) 核验方法文件，不重写摘要迁就改动。

## 第一步：可执行性检查

在仓库根目录执行；安装依赖可能需要网络，但不需要模型密钥：

```sh
git status --short
git rev-parse HEAD
uv sync --frozen --group dev
uv run --frozen python -X utf8 -m pytest -q tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py
uv run --frozen python -X utf8 -m pytest -q
```

依赖已缓存时可加 `--offline`。本机测试记录与已知 V3 preflight 编码失败见[保全记录](WORKSPACE_REORGANIZATION_2026-09-30.md)。零失败才称本次回归通过；skip 必须解释，不能通过删除断言或增加 skip 造绿。

只读确认 `docker version`、`docker image ls` 和需要的本地摘要文件是否存在。Docker 不存在时继续源码/单测工作，报告 `INFRA_BLOCKED`。GitHub 上只有可公开材料；`.codex`、镜像和本机 bridge 不会随 clone 自动出现。不要索取或上传 `.env`、Gold 正文、密钥或整块数据盘。

## 当前冻结批次已封存：不要重跑

本批完整路径为 `.codex/e1c/evaluation_2/canary-v2-metadata-proxy-v1/`，已有 acquire、grader-only、issue-only、source、live原始记录。原始响应、输入、账本、状态和Gold结果保留，不回填、不删除。云端 clone 只有公开摘要，不能假定这些本机原件存在。下列命令仅为已执行记录，不能再作为“下一步”运行：

```sh
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy admit
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_metadata_proxy public
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_live run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_gold
```

新适配器已实现，live freeze SHA `5b3c8bb508019adb2fd33f32511d9d16f3bebc8cb5979e69e2cc7f4871c1004f`。三题都有四个自动窗口；Seaborn回显到输出上限导致响应拒绝，Marshmallow无效fixture导致Gold后仍失败，pytest明确弃答。原runner把弃答统一记candidate_rejected；审计报告单列，原state不改。

实得0/3，不足2/3，本批已关闭。任何格式重放、窗口扩展或候选修订都只能作为未来开发材料，不能重报本批独立成绩。下一步回旧DEV开发通用机制；有同预算增益后再冻新方法、选择同时排除DEV及两批canary的新身份。Fresh30和旧六条TEST继续关闭。

## 已完成的 DEV 开发计划（历史要求保留）

以下开发已完成并保留多轮结果，当前按页首v3执行，不重复计费：按一周计划在**新版本**实现响应分账、行为合同、fixture正对照与自动源码窗口覆盖核验；复用现有定位、预算、容器和 ledger。先用旧DEV及合成夹具做通用回归，禁止任务ID→文件/规则表。不得修改 canary v2 的14份冻结方法文件或本批live freeze；已有 DEV12 与旧 DEV30 可用于调试，sealed TEST、SERBench private/Test500内容不可用于调参。响应协议改善与真实可信覆盖增益分别报告。

先实现合成边界测试，再在已有非保护 DEV 证据上验证。若缺原始输入/镜像，输出明确缺失路径和所需能力，不伪造真实实验。每个新付费 DEV 实验先输出精确命令、模型、最大请求数、token 上限与冻结身份；使用用户已有单实验≤100,000 tokens 的许可范围，不无限串联批次，遵守一周计划的累计预算与停止规则。

## 每次结束必须回传

- Git commit、实际命令、退出码、测试通过/失败/跳过数。
- 固定分母、各阶段人数、弃答/环境失败/模型失败分别计数。
- 请求数、provider tokens、失败扣费、自动重试次数。
- 新产物相对路径和SHA；未运行项及下一条条件式命令。
- 是否触及 protected 数据、镜像/本机设置（正常应为否）。
- 只在[集中续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)追加过程，更新 Roadmap 2 当前状态；保留旧版本和失败记录。

旧 E1-B 交接全文保留在[历史快照](NEXT_SESSION_HANDOFF_HISTORY_2026-09-30.md)。
