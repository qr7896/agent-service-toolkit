## Material Passport

- Origin Skill: academic-research-suite / experiment-agent; ponytail（复用现有分类器）
- Origin Mode: experiment design + DEV pilot audit
- Origin Date: 2026-09-27
- Verification Status: DEV v4 跨仓库 4/12 可信；独立 canary v1 为 1/3 负结果；第二批已冻结选题但官方镜像摘要直连受阻
- Version Label: e1c-coding-agent-evaluation-2-dev-v3

# E1-C Coding Agent evaluation_2：先可信复现，后付费修复

> **当前状态（2026-09-30）：** 旧 DEV v4 的单独身份使用 `deepseek-flash` 8 请求、25,424 provider tokens、零重试；固定 DEV12 中 4/12 个公开 issue 对齐 probe 经两次 base 同日志失败和 grader-only Gold 消除，跨 2 仓库，较旧 v2 的 3/12 多 1 个开发样本，但仍非泛化或修复率。先冻结[第二批完整方法](E1C2_CANARY_V2_METHOD_FREEZE_2026-09-30.md)再元数据选题，固定 Seaborn-2846、Marshmallow-1343、pytest-8861，与 DEV12／首批不重叠。官方任务元数据已核，但 Docker Hub 官方 manifest 的**无代理直连被重置**，因此镜像 0/3、第二批 issue/Gold 未读、第二批模型调用 0。用户自行下载的[直连命令、预估及进度显示](E1C2_CANARY_V2_DIRECT_DOWNLOAD_HANDOFF_2026-09-30.md)会先要求官方/镜像站摘要一致，失败就停在下载前。首批独立 canary 仍是 1/3 负结果；新版 repair live、sealed TEST/C5、Fresh30 未运行。

## 以下为历史快照；“当前／最新”均只指当时

> **当前结果（2026-09-29）：** 首批不重叠独立 canary 固定三题，镜像 3/3 身份核对、官方 Base/Gold 双准入 2/3。`deepseek-flash` 对两题各请求一次，共 5,755 provider tokens；scikit-learn-10581 的公开 issue 对齐 probe 两次同日志 base 失败、Gold 后通过，可信 1；Marshmallow-1702 对缺少明确行为判据的 RFC 弃答；Sphinx-10320 因官方镜像工作树不干净未过准入。固定分母 **1/3 < 2/3**，本批已封存负结果，不能在本批后验补规则。新版 repair live、sealed TEST/C5、Fresh30 均未运行。详见[独立 canary 结果](E1C2_INDEPENDENT_CANARY_V1_RESULT_2026-09-29.md)和[集中日志](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

> **canary 准备进展（2026-09-29）：** DEV-only 3/12 结论见下段。已先冻结[canary 方法与 42,000-token 整批硬预算](E1C2_CANARY_METHOD_FREEZE_2026-09-29.md)，再只凭元数据选定三题；官方 `task.yaml` 和镜像 manifest 均核对，三张本地镜像尚未取得（0/3），任务正文/评分材料未读，canary provider 调用 0、盲态结果无。用户接手直连下载，之后仍要逐题做 exact-base、官方准入、生成及离线判别，不能把 3/3 manifest 当作测试通过。[集中日志](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

> **2026-09-29 最新 DEV-only 状态（下方历史快照不代表当前）：** 冻结 DEV12 官方 Base-Fail 11/12、Gold-Pass 9/12、双门槛 9/12。统一 DEV v1 在 Flash-only 指令前用 `deepseek-v4-pro` 8 请求、24,699 provider tokens；v2 用 `deepseek-flash` 8 请求、25,645 tokens。v2 的 7 个重复 base 失败中，仅 3 个在 grader-only Gold 下被消除；结合公开 issue 语义核对，可信补丁前复现现为 **3/12、跨 2 仓库**，新增加 Marshmallow-1252，另两项为 Marshmallow-1359 和 scikit-learn-13496。这不是 official repair 或独立泛化。逐项失败、预算与证据仅记在[集中日志](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。[预注册 canary 方案](E1C_EVALUATION_2_CANARY_PREREG_2026-09-29.md)仍未执行；本轮没有选择/读取/运行 canary、sealed TEST 或 Fresh30，完整 canary 方法/配置冻结与盲态验证待后续单独推进。

> **2026-09-29 当前实况（覆盖下面历史快照）：** constructor DEV pilot 获精确授权后只发出 1 次 `deepseek-flash` 请求（3,889 provider tokens），但返回的是提示里的 `{"source":"Python probe"}` 占位示例，非有效代码，原账本不改、不重试。另立零调用的任务无关公开布尔构造参数规则，scikit-learn-13496 在 exact-base 上两次同样失败，grader-only Gold 消除该失败。因此当前是 **2 个跨仓库可信 DEV 补丁前复现**（Marshmallow-1359 保存模型 probe；scikit-learn-13496 确定性规则），只满足开发数量门槛，不是模型修复率或独立泛化。先冻结生成/分类器和不重叠的新三题 canary；盲态 ≥2/3 之前不做 repair live/Fresh30。见[集中日志](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

> **2026-09-29 最新执行结果（覆盖下面旧快照）：** 用户精确授权的 traceback pilot 已发出 1 次 DeepSeek `deepseek-flash` 请求、实际 3,807 provider tokens，无重试。原响应的 `issue_quote` 非逐字原文，被原 validator 拒绝；原状态保留。新零模型 replay 只把证据引用换为公开 issue 中唯一逐字异常行，不更改已保存的模型 probe；其在未修改 base 上两次触发同一 `AttributeError` 且日志哈希一致，grader-only Gold 成功应用后同一 probe 退出 0。Marshmallow-1359 因而是 **1 个可信 DEV 复现**，不是模型修复或独立泛化；跨仓库 ≥2 门槛、独立 canary、repair live、Fresh30 均未通过/未开启。专项 16 passed、Ruff clean；全量 1066 passed / 4 skipped / 1 failed（Streamlit 冷启动超时），失败单项独立复跑 1 passed，不拼称全绿；见[集中日志](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

> **2026-09-29 最新零调用冻结：** 已封存的 feedback-pilot-v1 不重跑；pytest-6680 公开 issue 主要为文档任务，不再作为下一次生产源码 probe 的付费目标。新 `e1c2-dev-traceback-pilot-v1` 按公开 issue 的明确 traceback/异常唯一选中 Marshmallow-1359，冻结一调用 `deepseek-flash` DEV probe。预算按提示估算预留 8,002 tokens，弹性上限 12,000（也是硬上限），仅按实际 provider usage 计费；最大输出 1,200，无自动重试。零调用预检已通过，未生成 provider ledger/state，未运行新的付费命令，trusted 仍 0/12。该任务即使得到可重复 base 失败，也须另外做只在 grader 侧的 Gold 区分，不能直接晋升 trusted。专项 14 passed、Ruff clean；[集中日志](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

> **2026-09-29 feedback pilot 已执行后的状态：** 原冻结精确命令只完成 1 次付费调用（Marshmallow 弃答，2,013 provider tokens）；pytest 在第二次请求发出前被每题预留上限挡住，原身份中断且不自动重跑。DEV 零调用 optional-dependency 诊断使旧 probe 的补丁前异常可重复，但 grader-only Gold 判别中，同一 probe 的过严时区断言仍失败，故 **trusted 0/12**；这不是新版修复成功率。后续新付费实验须修复预算预检、另立身份并取得新精确命令授权。[详细证据](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

> **2026-09-29 零调用续进展：** 旧 v2 的结构窗口会挤掉词法窗口，现按固定交错规则冻结 9/9 新 v3 issue-only 输入，旧输入保留。Marshmallow-1252 因此包含公开问题更相关的源码行，但没有新的可信复现。基于上轮的补丁前 `exit 0` 反馈，下一轮两题各一次的 `e1c2-dev-feedback-pilot-v1` 已通过零调用 preflight 并冻结；上限 2 次请求、9,000 provider tokens，模型 `deepseek-flash`，不自动重试，未运行 `run`。精确命令 `uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_feedback_pilot run` 尚待独立授权。完整验证与单项冷启动超时见[集中日志续档](PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

> **当前状态（2026-09-29，覆盖下文旧快照）：** Docker Desktop Engine 29.4.0 已恢复，活动数据目录重新指向 `D:\DockerDesktopData\wsl`，12/12 DEV12 镜像的在线 image ID 匹配冻结导入记录；未清空/重建 VHDX 或更改 tunnel 配置。12/12 离线容器源码内容与冻结 base 一致且工作树干净；两张官方镜像的 `SWE-bench` 附加提交只改变文件执行权限，守卫明确只容许 `100644→100755` 且 blob SHA 不变，其他内容差异仍拒绝。D: 当前约 59.3 GiB 空闲。
>
> **官方准入与 issue-only 输入：** DEV12 全部分别执行一次 Base/Gold，**Base-Fail 11/12、Gold-Pass 9/12、两者均过 9/12**。PyVista 的 `4311`、`3747` 为 Base 过、Gold 未过；`4648` 的两阶段日志均未被官方 parser 识别。失败题不被剔出冻结 12 题分母，也不冒充模型失败。评分材料和原始日志只在 `.codex/e1c/evaluation_2/grader-only/`；其公开文件按冻结 Git 树的 blob SHA 校验。9 个通过任务均有 issue-only、exact-base、生产源码自动定位的 `frozen_input_v2.json`，不含任务 ID、测试源码、官方断言或 Gold 内容；旧 v1 输入保留。一个源码窗口因普通文本含 `gold` 被现有泄漏审计拦下，新规则跳过该窗口并补选，审计没有放宽。当前模型生成 probe 已在 2 个 DEV 任务上尝试，但 **trusted 0/12、新版 official repair 未运行**；独立 canary/Fresh30 仍关闭。后续付费及零调用重放结果见下段。
>
> **已完成 DEV 付费 pilot 与零调用复盘：** 用户授权的精确命令 `uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_dev_pilot run` 已完成，Marshmallow-1252 与 pytest-6680 两题各两个固定视角，`deepseek-flash` **4/4 调用、5,606 provider tokens**，0 ambiguous/failed、0 自动重试、0 超预算。原 runner 因仅允许窗口对应模块而误拒绝包根公开导入；修正为仅允许 exact-base 中真实存在的本地生产模块。旧响应零调用重放后，3 个唯一 probe 均通过静态审计；其后排除了基础 Python 路径/环境误配，最终使用镜像 `testbed` Python 的 replay-v4 为 **3/3 补丁前退出 0**，故 **0 个重复失败候选、0 trusted**。Marshmallow 公共 issue 限定“未安装 dateutil”，而镜像 testbed 装有 dateutil；pytest 两个 probe 只检查了 base 已满足的行为。各重放按 v2/v3/v4 新目录留存，不覆盖原付费记录。下一轮应为任务无关的执行反馈迭代与 Gold 区分审计，并重新冻结预算/命令；仓库 `AGENTS.md` 要求任何新付费命令另获精确授权。DEV12 ≥2 个跨仓库 trusted 且随后独立 canary ≥2/3 之前，不启动修复 live 或 Fresh30。

> **2026-09-28 最新磁盘状态：** 用户已手动删除下文提到的旧 `.bak` 数据盘；本机复核 D: 空闲 71.78 GiB、活动 VHDX 与 Docker/本机 bridge 正常。下文 9 月 27 日双盘清单和删除前提是历史记录；[执行复验](DOCKER_E1C2_CACHE_CLEANUP_2026-09-27.md)为准。旧盘未备份，离线镜像缓存已失去。

## 身份、旧版边界与当前状态

这是**新开发协议**，不是把 E1-C 旧结果重命名为新版成绩。旧 E1-C 的 1/30 独立结果、后续旧 DEV30、strict-v5 与 source-contract canary 均原样保留。source-contract 独立三题因前两题 0 个可执行候选而封存，不能在其题目上补规则后继续称独立。旧 DEV30 仅作开发对照，不并入 DEV12 分母。

evaluation_2 当前冻结 DEV12 身份为 [`data/e1c_reproducer_dev12_identity.json`](../../data/e1c_reproducer_dev12_identity.json)：12 题、4 仓库、每仓库 3 题，永久不进入未来独立 canary/Fresh30。最新状态以上方 2026-09-29 快照为准；可投影 issue 或镜像导入均不等于可复现或修复成功。

**2026-09-28 续进展（工程，不是实验结果）：** 新增 [`evals/e1c_evaluation_2_probe.py`](../../evals/e1c_evaluation_2_probe.py)，复用旧 strict-v5 的 issue 断言剥离和生产源码自动定位；定位前核对源码工作区为冻结 base commit 且无未提交/未跟踪文件，只给生成器两种固定、任务无关提示视角。新增候选 AST 静态拦截和 `--pull=never --network none --read-only`、digest-pinned、exact-base 的容器执行入口。执行器在候选失败时重复两次，分别留日志/哈希；setup、超时或 Docker 错误立即停，不会把重复的任意错误晋升 trusted。该静态拦截不是可替代容器的安全沙箱；目前仅用模拟 Docker 的专项测试验证，**尚未运行任何真实 DEV12 probe**，也尚无可信语义判别器或模型生成结果。新增 [`evals/e1c_evaluation_2_metadata.py`](../../evals/e1c_evaluation_2_metadata.py) 用官方冻结任务树仅获取 12/12 `task.yaml` 的 `repo/base_commit/image` 元数据，写入 `.codex/e1c/evaluation_2/dev12_metadata.json`，未读取任何官方测试/Gold 内容。专项测试 10 passed（见本轮验证），不计修复成功。

**直连网络阻塞：** 用户在 Docker Desktop UI 将 proxy 设为 `No proxy` 并关闭 VPN 全局模式；`docker info` 不显示原 7892 端口，但不能据此证明其内部代理上游已改。GitHub 小元数据请求 12/12 成功，但 Docker Hub 官方 registry 对第一张 PyVista DEV 镜像的 manifest 请求连接被重置；宿主直连 IPv4/IPv6 探测亦被重置，Docker Hub tag API 直连超时。DaoCloud `m.daocloud.io/docker.io/...` 对该精确任务的 manifest 返回 403。**未拉取任何 DEV12 镜像、未传输大文件、未调用模型。** 不能从这些单点探测推断所有国内镜像均不可用；也不能在缺少官方 manifest/digest 时把其他来源直接升格为权威。后续需先取得不消耗 VPN 大流量的可验证官方传输路径，且逐张通过 digest 与 Base/Gold 准入，才运行真实 DEV12 probe。专项回归 10 passed；全量以 `uv run --frozen python -X utf8 -m pytest -q` 运行得 **1045 passed / 4 skipped**。默认 `uv run --frozen pytest -q` 的单项失败只因 Windows 未启用 UTF-8 模式，独立复跑及全量 UTF-8 复跑均通过，未改断言。

**2026-09-28 镜像传输突破（仅 manifest，不是 image gate PASS）：** 新增 [`evals/e1c_evaluation_2_image_transport.py`](../../evals/e1c_evaluation_2_image_transport.py)。通过本机 7892 **仅**向 Docker Hub 取有 200 KB/响应上限的官方鉴权与 manifest 元数据；通过显式空代理分别直连 `docker.1ms.run` 与 `docker.1panel.live` 取同样的 manifest，比较原始字节 SHA-256，并对 OCI index 进一步比较唯一 `linux/amd64` 子 manifest。冻结 DEV12 在两条候选直连路径均 **12/12 完全一致**：`.codex/e1c/evaluation_2/dev12_image_transport.json`（1ms，SHA-256 `76c2eaf8dd97b2dbc4676ba13ae8d49614f42e67b1ab904598bb4b8b19edb458`），`dev12_image_transport_1panel.json`（1Panel，SHA-256 `03ad6419c7cfa6fd2350d69eed9226d1f8c9e44fd8bccebbec915d6d7fc330f2`）。首张 PyVista 最大镜像层在 1ms 直连取得 1 字节 Range（206）；1Panel 对 Range 请求不支持，但限时、限速直连取得 4.15 MB/6 秒，短时样本不保证整镜像速度。清单中的压缩层大小逐项相加约 16.37 GiB，此数不等于实际新增磁盘占用或承诺的传输量。**尚未拉取任何 DEV12 镜像**，因此还没有本地 RepoDigest、exact-base 或 Base-Fail/Gold-Pass。Docker Desktop 持久化设置文件仍保留 9 月 26 日的 `manual/7892`，Windows 用户代理也仍启用 7892；即使 UI 已切到 No proxy，仍需确认已 `Apply & restart` 且 Containers proxy 不走 VPN 后，才允许 Docker 下载镜像层。绝不能因为 manifest 12/12 匹配就越过后续官方运行准入。专项镜像传输与 probe 测试 4 passed；最终全量 UTF-8 回归 **1047 passed / 4 skipped**。

**2026-09-28 本轮直连 pilot（未完成，非实验成绩）：** 用户确认 Docker Desktop 已重启。两条 digest-pinned `docker pull` 对同一 Marshmallow DEV 镜像都在首层后停滞；直接请求一个大层时，Range GET 返回 403，但 1Panel 无 Range GET 返回 200 并实际传输约 10 MB/10 秒。故新增 [`evals/e1c_evaluation_2_mirror_acquire.py`](../../evals/e1c_evaluation_2_mirror_acquire.py)：仅对冻结 DEV12 身份，从已核官方摘要的 1Panel 直连获取 manifest 与各层，逐字节核对大小/SHA-256，组成 OCI layout，再尝试 Docker 导入并核对配置摘要；每个已完成层可复用，半截层不可晋升。Marshmallow pilot 已取得约 683 MB 经核对的完整层，因用户要关闭 VPN 在本人终端验证，下载已暂停，没有并发任务、没有导入镜像。进程网络连接为镜像站 IPv6 `:443`，无该进程至 `7892` 连接；这能证明程序未使用本机 HTTP 代理，不能单凭连接表排除系统级 VPN 虚拟网卡路由。终端续跑命令如下，关 VPN 后执行才能实际验证无需 VPN：

```powershell
cd D:\codex\working\project20260827
uv run --frozen python -X utf8 -m evals.e1c_evaluation_2_mirror_acquire marshmallow-code__marshmallow-1252 --workdir .codex/e1c/evaluation_2/acquire/marshmallow-code__marshmallow-1252 --timeout 1800 --load
```

另对同题以浅层 Git fetch 取得并验证 exact-base `b063a103ae5222a5953cd7453a1eb0d161dc5b52` 的干净源码；公开 statement 经 assertion-stripping 投影后，任务无关定位返回 4 个源码窗口，均在 `src/marshmallow/utils.py`。这是**定位候选**，未生成为可执行 probe、未进行 Base/Gold 准入，不表示定位正确或修复成功。专项 8 passed；最终全量 UTF-8 回归 **1051 passed / 4 skipped**。真实 DEV12 probe/可信复现/official repair grade 仍均为 0；无新 provider 调用。

**用户关 VPN 后的终端续跑反馈：** 前 10 个描述符可复用，第 11 个约 293 MB 层发生 `size or digest differs`，不能判为下载成功；该错误可能由切换网络时连接提前结束，也可能由镜像站截断，原始报错没有实际字节数，不能确认为切网所致。现场存在 76,546,048 字节 `.partial`，完整层仍未晋升。对该层的单次 1 KB Range 探测得到 `206` 与正确 `Content-Range`，因此下载器现改为在检查精确偏移/总长后续传，并在最终层长及 SHA-256 匹配之前保持 `.partial` 状态；不删除已有完整层，不放宽官方摘要。新增续传回归后专项 **9 passed**；此改动后的全量回归待完成。用户下一次可在 VPN 关闭状态下原命令续跑，仍须核对导入结果。

**DEV12 逐张下载命令（准备就绪，尚未执行整批）：** 新增 [`evals/e1c_evaluation_2_batch_acquire.py`](../../evals/e1c_evaluation_2_batch_acquire.py)，现会跳过已验证的 Marshmallow pilot，再按压缩层大小逐张处理冻结的其余 11 题。每层约 8 秒打印一次 MiB/速度/ETA，Docker 导入每 15 秒心跳；完整层和已验 Docker 镜像在中断后跳过。每张开始前 D: 空闲必须高于 `20 GiB + 6 × 该张压缩层大小`，否则停机；仅在 Docker 配置摘要验证后删除该题临时 OCI layout 和 Docker 格式归档，不触碰旧镜像、活动 VHDX、tunnel 或研究记录。终端可执行：

```powershell
cd D:\codex\working\project20260827
uv run --frozen python -u -X utf8 -m evals.e1c_evaluation_2_batch_acquire --timeout-per-image 21600 2>&1 | Tee-Object -FilePath .codex\e1c\evaluation_2\dev12_download_docker_archive.log -Append
```

冻结清单压缩层标称合计 **16.37 GiB**；按稳定 1–3 MiB/s 粗算纯下载约 **1.6–4.7 小时**，另有归档格式转换及 Docker 导入，整批可保守预留 **3–8 小时**，掉线或低于 1 MiB/s 可能更久。网络速度、共享层与镜像解压比例均未知，不能保证本机约 71 GiB 可一次容纳全部 12 张；安全磁盘门槛可能中途停下，保留已验证镜像并允许续跑。该命令**只完成镜像获取**，不等于官方 Base/Gold 准入、可信复现或 E1-C evaluation_2 完成。

**首次真实导入排错与修复：** 2026-09-28 终端完成 Marshmallow 16/16 压缩描述符后，旧脚本生成的 OCI tar 被此机 `docker load` 拒绝（缺 `manifest.json`），属于本地归档格式兼容错误，不是 VPN 或镜像内容错误。已移除仅此一份可重建的错误临时 tar（984,637,440 字节），保留校验层；改为先验证每层解压后 diff-id 与官方 config，再生成 Docker save 格式 `manifest.json`/层 tar。首张实测 `docker load` 成功，镜像 ID `sha256:3b9a967a6152c6e44cf542323e2a8e13b4bbf18944091271093525f4a7343ff6` 等于官方 config digest。容器内 HEAD 为 SWE-bench 的 `273093c08eacabfcd5c0bbc9d9b19022142a07a5`，并非 base commit `b063a103ae5222a5953cd7453a1eb0d161dc5b52`；但 base 是其祖先，两者树哈希均为 `29a4d241a8bad5b523b52179c47e28c7d5add577`、`git diff` 为空、工作区干净，因此执行守卫改为祖先 + 完全相同源码树 + 干净工作区，而非误判空的 SWE-bench 附加提交。批处理已识别此镜像并避免二次导入，核验后仅清理该任务生成的临时 layout/归档；当前 D: 空闲约 71.7 GiB。**此项是镜像内容/源码树核验，不是 official Base-Fail/Gold-Pass。**

本轮修复后的全量 UTF-8 回归为 **1055 passed / 4 skipped**；该数字仅是代码回归，不是修复成功率。

**用户终端后续批次反馈：** 已验证导入 **6/12** 张；第 7 张 `scikit-learn__scikit-learn-13496` 的 726,858,641 字节层在收到 90,220,012 字节后提前 EOF，失败内容只保留为 `.partial`。同一镜像源对精确下一段返回 `206` 及正确 `Content-Range`；下载器新增最多 31 次的**有进展才重连**，每次继续前严格核对 Range/总长，最终仍须满足官方全层大小与 SHA-256，完整坏摘要或无进展不会自动重试。当前此层实测速率约 0.17–0.24 MiB/s；此前 3–8 小时的整批估计已不可靠，若持续此速，剩余下载可能超过 12 小时。终端命令已将单张上限调为 21,600 秒（6 小时），断线时可原命令续跑；6 张已导入的镜像不会重下。此状态仍未进行 official Base/Gold、probe 或模型调用。最终全量 UTF-8 回归 **1056 passed / 4 skipped**，不代表修复成功率。

## 零模型反馈接口（已实现）

[`evals/e1c_evaluation_2.py`](../../evals/e1c_evaluation_2.py) 复用 [`evals/e1c_reproducer_dev_feedback.py`](../../evals/e1c_reproducer_dev_feedback.py)。其输入是未来经批准的独立 probe 执行器产出的 JSON ledger；必须声明 `schema=e1c-evaluation-2-probe-ledger-v1`、`cohort=dev12`、冻结身份文件的 SHA-256 及 `rows`。每行须有 `instance_id / probe_sha256 / returncode / timed_out / stdout / stderr`，可选 `public_exception` 的 `exception_type / message`，但其来源仍需后续 issue-only 审计。该入口拒绝未知任务、重复 probe、身份不匹配及明显 grader-only 字段；输出不复制原始 stdout/stderr。无 ledger 时不运行；绝不拉镜像、运行 Docker、调用模型或写入旧结果。

执行方式：`uv run --frozen python -X utf8 -m evals.e1c_evaluation_2 <已审核的DEV12-probe-ledger.json>`。输出仅有失败原因与**候选**数量，`trusted_reproducer_count` 和 `development_gate_passed` 仍固定为 0/false。这不是可信复现判别器，也不是自动定位或修复代理。为避免把简单退出码当成果，可信晋升必须由后续冻结的语义对齐、exact-base/不可变镜像、network-none、重复运行和来源审计共同决定。

## 下一步门槛与停止条件

1. 用任务无关的自动生产源码定位，给 DEV12 每题固定输入；不读取官方 `test.patch`、Gold、断言、grader 日志或测试源码。实现有限候选 probe 的安全验证与执行器；它只能写独立临时 probe，不能改生产代码。
2. 为 DEV12 取得 exact-base 官方镜像及 Base/Gold 准入。先小规模零/低费 pilot，记录 attempted / safe / executable / issue-aligned / trusted，并用 evaluation_2 入口分流失败。环境错误、超时和无关失败不得晋升。
3. DEV12 固定分母达到至少 **2 个不同仓库的新增 trusted prepatch reproducer**，每题重复两次一致、零泄漏、身份与网络门槛通过，才冻结生成器/判别器/代码与预算。未达门槛就停在 DEV，不开独立 canary。
4. 仅从不重叠、未读内容的元数据池冻结新 canary；盲态 official Base/Gold 与 preflight 若未达至少 2/3 trusted，就继续停止，不进行付费配对。通过后再冻结精确付费命令/预算并取得该命令授权；后续依次为同版旧 DEV30 对照、Fresh30、E2。不得把跨版 best-of 称一次系统成绩。

## 实施优先级、资源边界与保守预期（2026-09-28）

**实测资源快照，不是实验成绩：** 本机 i9-14900HX（24 核/32 线程）、31.7 GiB 内存（检查时空闲 10.3 GiB）、RTX 5070 Ti Laptop（12 GiB 显存）、健康 SSD；Docker Engine 可用，其可见内存约 15.5 GiB；D: 空闲约 **71.77 GiB**。远端 API 模型调用不靠本机 GPU，现阶段更可能受 Docker 官方镜像传输与磁盘容量制约。快照会变，**每次拉取前重新量测**，不要把 71.77 GiB 当固定预算。单次只跑一个较重的官方容器；不预下载全部 DEV12，更不同时缓存 Fresh30/E2 所有镜像。以 D: 剩余 **20 GiB** 作为暂定操作预警线，临近时暂停新拉取并核对日志、镜像身份及清理对象；该线是安全余量，不是研究门槛或对单镜像大小的保证。记录 `Get-PSDrive D`、`docker system df -v` 与活动 VHDX 文件长度；镜像逻辑大小不可简单相加，删除镜像也不保证宿主 VHDX 自动缩小。不得手工删除活动 VHDX、Docker 内部层或隧道文件。

**保守预期：** 目前 0/12 真实 probe，无法估算新版可信复现率，更不能承诺旧 DEV30 或 Fresh30 的 30/30。先证明输入边界、自动定位和可执行复现链路，再依次通过 DEV12 跨仓库 ≥2、独立 canary ≥2/3、同版旧 DEV30 对照及独立 Fresh30。前两道门槛失败均回到 DEV，而非改写已看的 canary。通过复现门槛只支持“无需公开断言、无需人工选文件的可信复现流程”这一有限主张；修复成功率必须另以 official repair grade 计算。历史 E2 operational Entry Gate 的 PASS 也不是新版修复有效性证据。

**开发投入顺序：**

1. **先做任务无关的方法：** 公开自然语言 issue → exact-base 生产源码自动定位 → 有界、独立的候选 probe → 沙箱执行反馈 → issue-aligned 语义判断。对每题保存输入来源、候选、定位轨迹及失败分类；测试源码、公开/官方断言、`test.patch`、Gold、grader 日志和人工选文件均不得进入运行时。非零退出码或环境报错不能自动晋升可信复现。
2. **用冻结 DEV12 做故障分类，不靠扩充题库刷分：** 记录 attempted / safe / executable / issue-aligned / trusted 的固定分母和仓库分布。可在 DEV 内审计方法错误，但人工审计结果不得变成任务 ID 特例、运行时提示或独立成绩。更多 DEV 样本用于发现通用失败类型；只有未参与调参的 canary/Fresh30 才检验泛化。
3. **方法链稳定后才比较模型或候选预算：** 先用同一输入、同一执行器、同一固定预算比较模型/提示视角，一次只改一个变量；更强模型或更多候选可能改善生成，但不能修复泄漏、错误归因、镜像漂移。参数如 top-k、源码窗口、候选数、token 上限只在 DEV 做少量预设对照，冻结后不因 canary 结果回调。

**DEV12 镜像获取规则：** 先对少量跨仓库任务做零模型 image/official Base-Fail/Gold-Pass pilot，再按冻结 DEV12 清单分批扩展；未拉取/未运行的题保留在固定分母中并明确标注 `not_attempted`，不得报成失败或成功。每批开始前检查 D: 余量、Docker 状态、上批容器是否退出、官方 Docker Hub `linux/amd64` manifest digest；拉取后记录本地 RepoDigest、exact-base 与 official admission 证据。先保存日志与 digest，再评估是否按**精确 image ID/tag**移除不再即时需要的镜像；绝不运行全局 prune。

镜像来源默认是 SWE-bench 的 Docker Hub 官方任务镜像。**VPN 不是协议必需条件**：若直连能稳定取得官方 manifest 与层数据，则不需要；若直连不可用，可以在 Docker Desktop 的代理设置中使用可用的合规 VPN/代理出口，但“浏览器能上网”或仅 manifest 可达不证明 `docker pull` 可完成。国内加速器/镜像站可能存在，但**未核验 DEV12 全部精确镜像可用**，不能默认替换官方身份；阿里云 ACR 的旧 Docker Hub 镜像加速器已停止同步最新镜像。任何替代传输必须先与官方 `linux/amd64` manifest digest 核对，再验证拉取后的本地 digest 与 exact-base；缺少官方权威 digest、镜像不等价或传输不稳定时停在环境阻塞，不用相似镜像、重打标签或放宽 Base/Gold 门槛。历史 strict-v5 中 GHCR 非权威、`mirror.gcr.io` 失败的记录也不能推断 DEV12 的当前可用性。

依据：[Docker Desktop 代理设置](https://docs.docker.com/desktop/settings-and-maintenance/settings/)、[Docker registry pull-through cache](https://docs.docker.com/docker-hub/image-library/mirror/)、[Docker 按 digest 拉取](https://docs.docker.com/reference/cli/docker/image/pull/)、[阿里云 ACR 镜像加速说明](https://help.aliyun.com/zh/acr/user-guide/accelerate-the-pulls-of-docker-official-images)。

## 两块 Docker 数据盘：和 evaluation_2 的关系

2026-09-27 清理前核对：旧盘 `D:\docker_related\DockerDesktopWSL\disk\docker_data.vhdx.inactive-20260927.bak` 为约 67.2 GiB 的**离线旧缓存**；当前盘 `D:\DockerDesktopData\wsl\disk\docker_data.vhdx` 为约 60.9 GiB 的**活动数据盘**。清理前 Docker 可运行，`docker system df` 显示 15 张镜像、0 容器、0 volume、0 build cache，镜像逻辑大小 37.61 GB。清理后剩 5 张、9.285 GB，但 D: 空闲仍 4.56 GiB；详见[清理记录](DOCKER_E1C2_CACHE_CLEANUP_2026-09-27.md)。

| 内容 | 对 evaluation_2 DEV12 | 对旧证据/未来复跑 | 处置级别 |
|---|---|---|---|
| 旧盘内 2026-09-23/24 原始 30 + 替补 10 的镜像缓存 | 无现成 DEV12 镜像 | 含最终旧 DEV30 的回放价值；其中原始 7 + 替补 3 未入选最终 DEV30 | 整盘先外置归档；不可称“无价值”直接删 |
| 旧盘其余 strict-v5 canary 痕迹 | 不可充当新独立 canary | 历史审计价值；部分拉取不完整 | 随整盘归档 |
| 当前盘清理前 15 张、清理后 5 张镜像 | **0/12** DEV12 对应；无需它们才能启动 DEV12 代码开发 | 保留 `sympy-14711` 等 4 张旧开发/回放镜像和 Alpine | 已按精确镜像清理 10 张，详见清理记录 |
| 当前盘 Docker 内部 overlay2/containerd/isocache | 不是可直接复用的 DEV12 镜像 | Docker 管理的存储；隐藏 image store 可能仍占空间 | **不可手动删目录或活动 VHDX** |
| 仓库 `data/`、`.codex/e1c/`、`docs/`、`evals/` 及测试 | 身份、来源、协议、可追溯性所必需 | 旧实验的安全证据 | **不清理** |

旧盘的 43 个 SWE-bench 任务镜像**名称记录**包括原始候选 30、替补 10、strict-v5 canary 3；名称出现不证明每张镜像都已完整拉取。最终旧 DEV30 为原始 23 + 替补 7。未入最终旧 DEV30、也不属于 DEV12 的 10 个任务是：`astropy__astropy-13453`、`django__django-16454`、`django__django-14787`、`scikit-learn__scikit-learn-25747`、`sympy__sympy-13031`、`django__django-15695`、`pylint-dev__pylint-7080`、`django__django-11964`、`sympy__sympy-16792`、`django__django-14373`。它们的镜像缓存对当前执行优先级最低，但历史准入记录仍应保留在仓库。

当前盘清理前 15 张镜像中，仅 `sympy-14711` 属最终旧 DEV30；`django-12453`、`sympy-13761`、`matplotlib-21559` 属已封存 source-contract canary；其余为此前开发/canary 镜像及 Alpine。本轮已按身份移除其中 10 张旧 canary；剩余 4 张旧开发/回放镜像和 Alpine 暂留。删镜像降低旧轮次的离线回放能力，但不删除仓库内结果与安全证据。

## 安全清理顺序（历史方案；旧盘现已由用户手动删除）

1. 先保留仓库全部身份/审计/结果文件及官方 image digest。清理之前运行 `docker image ls -a --digests` 和 `docker system df -v` 留下清单；确认没有运行中的容器或正在拉取的镜像。**不要使用** `docker system prune -a`、`--volumes`、`docker image prune -a` 或对 Docker 内部目录手工 `Remove-Item`。
2. 对当前盘，只对确认不需即时复跑的**具体 image tag**运行 `docker image rm --no-prune <精确仓库:标签>`，逐张检查 Docker 的输出并复核 `docker image ls -a`。对 `<none>` 镜像先核对完整 image ID、引用关系及历史用途，再决定是否移除；不要用 `-f`。共享层意味着列出的镜像虚拟大小不可直接相加当作回收空间。
3. 对旧盘，优先复制到外置磁盘并验证文件长度和 SHA-256，再停止 Docker Desktop、执行 `wsl --shutdown`；核对路径、文件名以及活动盘仍是 `D:\DockerDesktopData\wsl\disk\docker_data.vhdx`，旧盘没有被挂载或引用。外置副本验证和 Docker 重启/历史镜像可见性检查通过后，才可**单文件**删除旧 `.bak`。如果没有外置副本，删除意味着丢失低速下载来的旧镜像缓存，未来重跑旧 DEV30 可能需要重新拉取；不要承诺“毫无影响”。
4. 删除镜像不等于 Windows 上的动态 VHDX 立即缩小；空间仍紧张时另做官方支持的离线压缩流程，先备份、完全退出 Docker/WSL、确认没有挂载，再处理活动 VHDX。不要对运行中的盘做 DiskPart compact 或手工修改 overlay2/containerd。

上述是原先优先备份的安全建议。用户后来明确选择**不备份**并亲自删除了旧 `.bak`；它已不存在，不要再运行旧删除命令。当前活动盘 `D:\DockerDesktopData\wsl\disk\docker_data.vhdx` 绝不能作为删除目标。

依据：[Docker 按镜像删除与 `--no-prune`](https://docs.docker.com/reference/cli/docker/image/rm/)、[Docker Desktop 分离的镜像存储](https://docs.docker.com/desktop/features/containerd/)、[Microsoft WSL 磁盘空间说明](https://learn.microsoft.com/en-us/windows/wsl/disk-space)。

9 月 27 日通过 Docker 精确移除 10 张旧 canary 镜像；9 月 28 日用户另行手动删除旧 `.bak`。**活动 VHDX、隧道内容及研究证据未删除，数据盘未离线压缩。**活动 VHDX 内部数据因 Docker 正常删除操作发生变化。
