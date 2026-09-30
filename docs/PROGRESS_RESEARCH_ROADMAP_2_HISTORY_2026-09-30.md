## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan + local result synthesis
- Origin Date: 2026-09-25
- Verification Status: DEV v4 为 4/12 可信补丁前复现；canary v1 负结果 1/3；canary v2 已冻结选题、官方镜像摘要直连受阻
- Version Label: progress-roadmap-2-v4

# 研究进度路线图 2：从项目启动到现在

> **最新快照：2026-09-30。** 本页是阅读入口；下方按日期保留的旧快照不能代替本段。逐轮旧日志见 [原集中日志](research/PROGRESS_LOG_ARCHIVE.md)与 [9 月 27 日续档](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

**当前进展：** 旧 DEV12 上先后运行 v3、v4 两个独立 `deepseek-flash` 开发身份，分别 8 请求／27,696 tokens 与 8 请求／25,424 tokens，无自动重试。v3 虽有 3 个 Gold 可区分候选，但额外强断言使它不适合作为新方法；v4 明确区分“返回值判据”和“调用不抛异常”，5 个重复失败候选中 4 个 Gold 区分且符合公开 issue，故当前 **4/12 DEV 可信复现、跨 2 仓库**，只说明开发集改善。已先[冻结第二批方法](research/E1C2_CANARY_V2_METHOD_FREEZE_2026-09-30.md)，再只用元数据固定 Seaborn-2846、Marshmallow-1343、pytest-8861，和 DEV12／第一批均不重叠；官方 `task.yaml` 3/3 已核。**官方 Docker Hub manifest 直连被重置，尚未形成权威镜像摘要、未下载新镜像、未读新 issue、未运行第二批模型或评分。** 镜像站单独估计压缩层合计约 2.93 GiB，不能替代官方摘要。[用户终端直连下载命令与停机条件](research/E1C2_CANARY_V2_DIRECT_DOWNLOAD_HANDOFF_2026-09-30.md)。全量回归 **1083 passed／4 skipped／1 failed**（已知 Streamlit 冷启动 8 秒超时），失败单项独立复跑 **1 passed**；两次不能拼称全绿。新版修复、sealed TEST/C5、Fresh30 均未运行。

### 以下为历史快照，标题中的“最新／当前”仅指当时，不代表现在

**最新结果（以下旧快照均非现状）：** E1-C evaluation_2 的首批独立 canary 已按预注册固定三题运行完毕：本地官方镜像 3/3 身份核对，官方 Base/Gold 双准入 2/3；Sphinx 镜像 `/testbed` 的未提交 `tox.ini` 修改触发源码身份守卫，原位记失败。另两题使用 `deepseek-flash` 共 **2 次请求、5,755 provider tokens**、无重试；scikit-learn 的公开 issue 对齐 probe 经两次同日志 base 失败及 grader-only Gold 消除，可信 **1 个**；Marshmallow 对缺少明确行为判据的 RFC 弃答。固定分母结果 **1/3，低于 ≥2/3**，本批已封存负结果，不能在这批题上改规则后仍称独立。新版 official repair、sealed TEST/C5、Fresh30 均未运行；代码全量回归 **1083 passed / 4 skipped**，不是修复率。[逐项证据与后续边界](research/E1C2_INDEPENDENT_CANARY_V1_RESULT_2026-09-29.md)。

**canary 准备的最新状态（下段 DEV-only 结果仍有效）：** 已先封存[完整复现方法与预算](research/E1C2_CANARY_METHOD_FREEZE_2026-09-29.md)（`deepseek-flash`、最多 3 请求、单题 14,000 / 整批 42,000 provider tokens、无自动重试），再按原预注册盐仅用元数据固定三个不重叠身份：scikit-learn-10581、Marshmallow-1702、Sphinx-10320。公开 `task.yaml` 元数据和三张镜像的官方/直连镜像站 manifest **3/3 摘要一致**；任务正文、官方测试及 Gold **尚未读取**，本批 provider 调用 **0**。本地镜像 **0/3 完成**；直连下载已交用户终端执行，当前只有第一张约 4 MiB 可续传片段，没有并发下载。镜像通过之前不宣称 canary 结果；[集中日志](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

**最新 DEV-only 结果（下方旧快照仅供历史参考）：** DEV12 官方准入仍是 Base-Fail **11/12**、Gold-Pass **9/12**、双门槛 **9/12**。统一公开 issue/生产源码 DEV v1 在用户改为 Flash-only 之前用 `deepseek-v4-pro` **8 请求、24,699 provider tokens**；v2 按新要求用 `deepseek-flash` **8 请求、25,645 tokens**（硬上限 81,845），均无自动重试。v2 的 9 条准入 DEV 中，7 条产生可重复 base 失败，但独立离线 Gold 对照只有 **3/7 区分成功**；公开 issue 语义核对后，可信补丁前复现为 **3/12、跨 2 仓库**：scikit-learn-13496（确定性规则）、Marshmallow-1359 与新增加的 Marshmallow-1252（模型 probe）。这不是模型修复率，也不是独立泛化。完整代码回归 **1080 passed / 4 skipped**。本轮只做 DEV，既有[canary 预注册方案](research/E1C_EVALUATION_2_CANARY_PREREG_2026-09-29.md)未执行，**没有选择/读取/运行 canary、sealed TEST 或 Fresh30，也没有 official repair**；详见[集中日志](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

**当前实况（覆盖下方历史快照）：** 获精确授权的 constructor DEV pilot 只执行了 **1 次** `deepseek-flash` 请求，实际 **3,889 provider tokens**、无重试；模型原响应是提示中 JSON 结构示例的照抄 `{"source":"Python probe"}`，不是可执行 Python，原账本和响应封存，不能算模型生成可信复现。另立 **零 provider 调用** 的任务无关公开布尔构造参数规则，对 scikit-learn-13496 自动生成 probe；exact-base 两次相同 `unexpected keyword argument 'warm_start'` 失败，grader-only Gold 在一次性隔离容器应用后同 probe 退出 0。由此 DEV 共有 **2 个跨仓库可信补丁前复现**：Marshmallow-1359（保存的模型 probe 经公开异常逐字引用重放）和 scikit-learn-13496（确定性公开 issue 规则）；后者不是模型产物，也不是独立泛化证据。下一步先冻结完整生成/分类器与不重叠的独立 canary，盲态零模型验证须达到 **≥2/3**，否则不运行 repair live/Fresh30。新版 official repair 尚未运行；旧 E1-B sealed TEST、C5、Fresh30 未打开。详见[集中日志](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

**最新零调用准备：** 在 Marshmallow-1359 已有 1 个可信 DEV 复现后，按公开 issue 中“明确请求将参数暴露于构造函数并给默认值”的通用规则，唯一选择另一仓库 scikit-learn-13496。新 `e1c2-dev-constructor-pilot-v1` 仅使用冻结 v3 公开 issue/生产窗口，直接从 issue 抽取逐字证据引用，避免前次模型引用改写；一次模型生成与后续容器验证分开。零调用 preflight 两次一致，官方 Base-Fail/Gold-Pass 与本地镜像身份有效；预计调用预留 **8,858**、弹性/硬上限 **12,000 provider tokens**、最大 1 次请求、输出上限 1,200。新身份 provider ledger/state 均未生成，**本轮新增付费调用 0、可信 DEV 仍 1/12**。精确 `run` 命令须单独授权；专项 **12 passed**、Ruff clean。[集中日志](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

**最新结果（覆盖下方零调用冻结快照）：** 用户授权的精确 `e1c_evaluation_2_traceback_pilot run` 已执行一次，Marshmallow-1359 发出 **1 次** `deepseek-flash` 请求，实际 **3,807 provider tokens**，无重试/超预算。原响应因 `issue_quote` 非逐字原文而被拒，原状态不回填。用任务无关的“公开 issue 唯一明确异常行”另立零模型 replay 身份，在相同已保存 probe 上两次得到与 issue 完全一致的 `AttributeError`、日志 SHA 一致；grader-only Gold 补丁在隔离容器成功应用后，同一 probe 退出 0。因此 evaluation_2 获得 **Marshmallow-1359 这 1 个可信 DEV 复现**；仍未达到跨仓库 ≥2 的开发门槛，不启动独立 canary、repair live 或 Fresh30，也不把它称为 patch 成功率。专项回归 **16 passed**、Ruff clean；全量 **1066 passed / 4 skipped / 1 failed**（同一 Streamlit 冷启动 8 秒超时），失败单项独立复跑 **1 passed**，两次运行不可拼成一次全绿。[证据与边界](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

**当前最新（traceback DEV pilot 零调用冻结）：** 没有重跑已中断的 feedback-pilot-v1。复查公开 issue 后，pytest-6680 以文档更新为主，原生产源码 probe 已在 base 通过，不值得按原路线继续消耗模型额度。新 `e1c2-dev-traceback-pilot-v1` 用任务无关的“公开 issue 同时包含 traceback 与明确异常”规则，在 9 个已准入 DEV 输入中唯一选中 Marshmallow-1359；不使用 Gold/评分日志挑题。预检同时验证 Base-Fail/Gold-Pass 身份、冻结本地镜像与请求预算：估算预留 **8,002**、弹性上限/硬上限 **12,000 provider tokens**，最多 **1 次** `deepseek-flash` 请求、单次输出上限 1,200、无自动重试。`freeze.json` 已写入；新身份的 provider ledger/state 均不存在，**新增付费调用 0、trusted 仍 0/12**。专项回归 14 passed、Ruff clean。按仓库 `AGENTS.md`，新的付费 `run` 需要用户对精确命令另行授权；随后仍须重复补丁前失败与 grader-only Gold 区分，跨仓库 DEV ≥2 和独立 canary ≥2/3 之前，不启动 repair live/Fresh30。[集中日志](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

**最新实验结果：** 获授权的 feedback pilot 只发出 **1 次** `deepseek-flash` 请求、**2,013 provider tokens**，Marshmallow 因 issue 限定的 `python-dateutil` 缺失条件在当前镜像不成立而弃答；第二题在请求前被任务 token 预留上限挡住，整轮已封存 `interrupted_no_auto_retry`，不自动重跑。用公开 issue + 生产窗口自动推断该可选依赖并在离线容器隔离后，旧 probe 的补丁前失败可重复，但 **Gold 应用成功后仍不满足其过严的时区断言**，Gold 区分失败。因此 trusted 仍 **0/12**，这不是 12 题修复失败，也没有新的 official repair grade。下一步是 DEV 方法修正和新身份预检，不能使用旧中断命令继续付费；[证据与边界](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

本轮代码验证：专项 **10 passed**、Ruff clean；全量 **1062 passed / 4 skipped / 1 failed**（同一个 Streamlit 冷启动 8 秒超时），失败单项独立复跑 **1 passed**。两次运行不可合并成一次全绿。

**本轮零调用续进展：** 找到旧输入中“同一显式路径的结构窗口挤掉词法窗口”的通用定位缺陷；已按固定交错规则为 9 个准入 DEV 任务生成 **9/9 新 v3 输入**，原 v2 不覆盖。Marshmallow-1252 的公开 issue 相关源码窗口因此进入输入，但尚未证明模型能复现故障。依据上轮“补丁前通过”的执行反馈，新的两题、两次调用、9,000 provider-token 上限的 pilot 已零调用预检并冻结，**未执行付费 `run`**；需要对精确命令另行授权。当前 trusted 仍 **0/12**，独立 canary/Fresh30 关闭。本轮全量代码回归 **1060 passed / 4 skipped / 1 failed**（既有 Streamlit 8 秒冷启动超时），失败单项独立复跑 **1 passed**；不可拼称一次全绿或修复率。[明细日志](research/PROGRESS_LOG_ARCHIVE_2026-09-27_CONTINUATION.md)。

**E1-C evaluation_2 当前门槛（2026-09-29）：** Docker Desktop 已恢复并重新接回保有 DEV12 的原活动盘；12/12 不可变 image ID 在线匹配，12/12 容器源码内容身份检查通过（其中两张官方镜像仅有 `100644→100755` 权限位变化）。冻结 DEV12 的独立官方 Base-Fail/Gold-Pass 已全部执行：**Base-Fail 11/12、Gold-Pass 9/12、双门槛 9/12**；PyVista 三题保留在分母中，分别因 Gold 不过或官方日志不可解析而不入可评分 pilot。对这 9 题，公开 issue → exact-base 生产源码的自动定位已 **9/9 冻结 v2 输入**，不读公开断言/测试文件/Gold。用户授权的两仓库 DEV pilot 已运行：`deepseek-flash` **4/4 调用、5,606 provider tokens**，无重试/超额；原始 4 个候选先被过窄的本地导入检查拒绝。零调用修正并保留原结果后，3 个唯一 probe 进入离线容器；分别排除了基础 Python 与源码路径的执行环境误配，使用官方 `testbed` 环境重放时 **3/3 均在补丁前通过**。所以**可信复现仍 0/12、新版 official repair 未运行**，DEV12 跨仓库门槛未过，独立 canary/Fresh30 仍关闭。下步只能在开发集采用任务无关的执行反馈与 Gold 区分审计，另冻结新命令后再申请精确授权；不能把 4 次调用、9/12 准入或代码回归包装为修复率。[详细执行边界](research/E1C_CODING_AGENT_EVALUATION_2.md)。本次全量非模型回归 **1058 passed / 4 skipped**，不是修复率。

**最新 E1-C 门槛（9 月 27 日）：** Docker Engine 已恢复；source-contract 在旧 DEV 上达到 2 个跨仓库、可重复、network-none 的 trusted runtime witness，因此冻结了新的独立三题 canary。其 Django、SymPy 两题的盲态 preflight 均为 **0 个可执行复现候选**；即使第三题成功，最多也只有 **1/3**，低于预注册的 **≥2/3**。该 canary 已封存为 `sealed_negative_threshold_unreachable`，不是模型修复 0/3。第三题 Matplotlib 随后完成官方 Base-Fail 与 Gold-Pass（F2P 分别 0/1、1/0，P2P 均 680/680）；这补齐了准入证据，但不能重新打开已失败的 preflight 门槛。**本轮 0 次 provider 调用；paired live、C5、同版 DEV30、Fresh30 均关闭。** 新的专项回归 17 passed；完整非模型回归 1038 passed / 4 skipped / 1 failed（已知 Streamlit 8 秒冷启动，单测独立复跑通过），不可拼称全量通过。下一步只能使用旧 DEV/非 canary 证据提出实质不同的任务无关复现机制，先过零模型开发门槛，再冻结不重叠的全新独立 canary；不能用本批 canary 后验补规则或把跨版 best-of 当成 30/30。

**最新 DEV 方案（尚未运行模型）：** 旧 DEV30 继续作为开发对照；另已 [冻结补充 DEV12 身份](../data/e1c_reproducer_dev12_identity.json)，覆盖 4 仓库，12/12 元数据与公开 issue 投影可核验，这 12 题不得再进入独立 canary/Fresh30。借鉴近期 issue-to-test 研究的[有限候选复现 + 执行反馈筛选](research/E1C_REPRODUCER_DEV_NEXT_2026-09-27.md)，首个零模型反馈分类器已实现、专项 8 passed；生成器和真实复现实验尚未运行。须先在 DEV12 证明跨仓库新增可信补丁前复现，才能申请新独立 canary；目前未产生新官方修复结果。

**evaluation_2（新开发协议，非新成绩）：** [独立执行与磁盘整理说明](research/E1C_CODING_AGENT_EVALUATION_2.md) 已建立；新增身份绑定的零模型反馈汇总入口，复用原分类器，候选失败绝不自动晋升可信复现。专项测试通过，但 DEV12 真实 probe、模型修复、官方评分均为 0；旧 E1-C 结果和封存 canary 不改写。

**Docker 缓存清理（9 月 27 日）：** 为给 evaluation_2 留出 Docker 内部空间，已[按精确身份移除 10 张已封存/旧 canary 镜像](research/DOCKER_E1C2_CACHE_CLEANUP_2026-09-27.md)，保留 4 张旧开发/回放镜像与 Alpine。Docker/本机 bridge/项目专项复验通过；旧 67.2 GiB 盘、全部研究证据和 tunnel 配置未触动，活动 VHDX 仅经 Docker 正常镜像删除而更新，没有直接删除/压缩。镜像逻辑占用 37.61→9.285 GB，但 D: 空闲仍 4.56 GiB；旧盘无可验证外置备份、活动盘无安全离线压缩条件，均未删除/压缩。App 私有连接清理前后均报告 `not connected`，云端端到端未获验证。

**9 月 28 日后续：** 用户确认无备份删除旧 `.bak` 并亲自操作；已[复验](research/DOCKER_E1C2_CACHE_CLEANUP_2026-09-27.md)旧文件不存在、活动 VHDX 存在，D: 空闲升至 **71.78 GiB**。Docker Engine/容器、bridge 本机单测和本地 tunnel 健康均正常；App 私有连接仍 `not connected`，冷重启与 WebCodex 云端调用未验证。上段 9 月 27 日记录是当时快照，不代表当前旧盘仍存在。

**evaluation_2 9 月 28 日续进展：** DEV12 的 12/12 官方 `task.yaml` 元数据已小流量取得并绑定冻结身份；issue-only 自动定位输入、两种固定 probe 提示、候选静态检查与不自动拉镜像的 Docker 双次执行入口已实现。定位前增加冻结 base commit/干净工作区核验，防止将错误版本或本地修改的源码窗口送入模型。专项 10 passed、最终代码的全量 UTF-8 回归 **1045 passed / 4 skipped**。本地已有 Alpine 镜像的 `--pull=never --network none --read-only` 容器参数冒烟测试通过，但这不是 DEV12 官方镜像或 probe 验证。真实 DEV12 probe/可信复现/新版官方修复仍为 **0/12、0/12、0**。用户已关闭 Docker Desktop VPN 代理，但直连 Docker Hub registry 的 manifest 请求被重置，DaoCloud 对所试精确镜像返回 403；未下载 DEV12 镜像。当前先停在[新版协议的镜像传输门槛](research/E1C_CODING_AGENT_EVALUATION_2.md)，不得把工程准备计成实验结果。

**同日镜像传输续核：** 官方 Docker Hub 的少量 manifest 元数据经 7892 获取，`docker.1ms.run` 与 `docker.1panel.live` 的同一 DEV12 镜像元数据显式绕过系统代理直连；两条候选传输均 12/12 顶层与 `linux/amd64` manifest 原始 SHA-256 完全一致。首张最大层在 1ms 的 1 字节 Range 直连成功，1Panel 的限时直连可取得实际内容，但短时速度不保证整镜像。新增可重跑的 [metadata-only 审计](../evals/e1c_evaluation_2_image_transport.py)与 `.codex/e1c/evaluation_2/dev12_image_transport.json`（1ms SHA-256 `76c2eaf8dd97b2dbc4676ba13ae8d49614f42e67b1ab904598bb4b8b19edb458`）、`dev12_image_transport_1panel.json`（SHA-256 `03ad6419c7cfa6fd2350d69eed9226d1f8c9e44fd8bccebbec915d6d7fc330f2`）。新增代码后的全量 UTF-8 回归 **1047 passed / 4 skipped**。这证明有望用非 VPN 路径搬运**同一内容**，但 **12/12 manifest ≠ 12/12 本地镜像**：Docker Desktop 持久化设置仍记录旧 `manual/7892`，需先确认 Docker Desktop 与 Containers proxy 的 No proxy 已应用，再开始单张镜像层下载。D: 当前约 71.73 GiB 空闲，尚无 DEV12 image pull、Base/Gold、真实 probe 或新 provider 调用。

**本轮最新状态：** 两个 Docker Desktop mirror pull 均停在首层后；1Panel 直连无 Range GET 可读取大层。已加入[逐层摘要校验、可复用已完成层的 OCI 下载器](../evals/e1c_evaluation_2_mirror_acquire.py)，首张 Marshmallow DEV 镜像取得约 683 MB 已核对层，按用户要求暂停，以便用户关闭 VPN 在终端续跑；尚无可运行的完整本地 DEV12 镜像。该题 exact-base 干净源码和 assertion-stripping 后的自动定位已通过零模型准备，但真实 probe/可信复现/official repair 仍为 0。专项 8 passed；最终全量 UTF-8 回归 **1051 passed / 4 skipped**。下一步先完成单张 OCI 导入与 Base/Gold 准入，再扩展 DEV12；终端命令和停机边界见[详细协议](research/E1C_CODING_AGENT_EVALUATION_2.md)。

**下载交接更新：** 用户关 VPN 后在第 11 层遇到长度/摘要不匹配，未将其晋升；已加入严格 Range 续传、层内速度/ETA 和 Docker 导入心跳，并准备 [DEV12 逐张批处理命令](research/E1C_CODING_AGENT_EVALUATION_2.md)。约 683 MB 已核对完整层及 76 MB 半截层仍保留；批处理可续跑并在 D: 余量不足时停机。**尚未导入完整 DEV12 镜像或运行 Base/Gold/probe**；专项 11 passed、全量 UTF-8 **1054 passed / 4 skipped**。整批仅为镜像获取，不改变 E1-C evaluation_2 准入状态。

**本轮导入修复后的实际状态：** 首张 Marshmallow DEV 镜像 16/16 压缩描述符及解压层 diff-id 已核对，Docker 格式归档已成功导入，镜像 ID 匹配官方 config digest；批处理能跳过已导入的首张并安全回收其临时 layout/归档。容器 HEAD 是 SWE-bench 附加空提交，和冻结 base commit 的源码树完全相同且 base 为祖先；执行守卫据此做严格树等价检查。当前是 **1/12 镜像已导入**，仍是 **0/12 official Base/Gold、0/12 真实 probe、0/12 可信复现、0 新 provider 调用**。下载其余 11 张的终端命令不变；详见[详细协议](research/E1C_CODING_AGENT_EVALUATION_2.md)。

**最新批次快照：** 用户终端已推进到 **6/12 张镜像已验证导入**；第 7 张一个 726,858,641 字节层在 90,220,012 字节提前 EOF，但 `.partial` 留存且镜像站精确 Range 可达。已加入有进展才自动重连（最多 31 次）并维持最终官方摘要校验，终端可用同一批处理命令续跑，单张超时调至 6 小时。当前仍为 **0/12 official Base/Gold、0/12 真实 probe、0/12 可信复现、0 新 provider 调用**；全量回归 **1056 passed / 4 skipped**。详见[详细协议](research/E1C_CODING_AGENT_EVALUATION_2.md)。

## 一分钟看懂现状

项目从一个 LangGraph + FastAPI + Streamlit Agent 服务，发展成可以检索、阅读、受控编辑和测试代码的 Coding Agent。研究目标已收敛为：**在不偷看测试答案、不靠人逐题选文件的条件下，用有限证据与预算自动修好真实代码问题。**

目前**基础设施和研究管线已建好，可靠的端到端自动修复尚未证实**。E1-C 第一次独立 30 题只通过 **1/30**。这 30 题后来变成开发集：一次同版完整运行 **4/30**；跨许多版本逐题挑最好得到 **13/30**，但那不是一个系统一次运行的成绩。转向盲态后，最新付费对照 C4 两臂均 **0/6**。全新 Fresh30 **尚未选题，更未测试**。

## 三条线分别在研究什么

| 主线 | 通俗解释 | 不能混用的指标 |
|---|---|---|
| 平台与 Runtime | 让 Agent 能安全地读、改、测代码，并留下账本 | 单元测试通过 ≠ 修好 benchmark 任务 |
| V0→V3 | 研究检索哪种证据、何时停、历史经验是否有用 | 找到 Gold 证据 ≠ 模型能写正确 patch |
| E1-B / Formal E1 / E1-C | 模型写 patch，再用独立测试判修复成功 | DEV 逐题 best-of ≠ 独立一次性成功率 |

## 过去一个月的主线时间表

| 时间 | 做了什么 | 实际结果和边界 |
|---|---|---|
| 8 月底—9 月中 | 跑通原服务；用本地 BGE-M3 替换知识库的 OpenAI embedding；增加代码搜索、阅读、受控写入、测试、轨迹、经验、沙箱和预算控制。 | 证明工程链路可用，不证明真实问题的修复率。 |
| 9 月中—18 日 | 转入 Research Mode；从本仓库修复历史整理 20 条可复现任务；做 V0 检索对照和 V1 冻结策略。 | V1 在相同 4 条 frozen TEST 上保持 Context Recall 0.7812，同时平均上下文 122.5→87.0 tokens、检索动作 2.00→1.25；只属于检索效率。 |
| 18—19 日 | V2 建立有来源/泄漏检查的决策记录、离线策略和 Runtime shadow；接入 SERBench 官方接口。 | 221 条 records 实际只对应 20 个原始问题。Cal500 frozen V2 方法 MSS@8=0.078，低于 upstream BM25 starter 0.104；Test500 预测生成但 private evaluator 未评分。 |
| 19—20 日 | V3 冻结执行时 provenance、严格过去经验回放；做 6 条非 sealed compact pilot 和 3 组 memory OFF/ON 配对。 | pilot 3 成功/3 失败；三组配对的 patch 与成败相同，ON 总共多 369 tokens。未观察到增益，但样本太小，不能宣布记忆无效。 |
| 20—22 日 | E1-B 在 4 条 DEV 上反复改编辑器；Formal E1 分 Wave A 12 题、Wave B 18 题执行。 | E1-B 曾达到 2/4 DEV，但未达冻结门槛；原 6 条 TEST 未执行，fixture 保密性却已受损。Formal E1 **已运行并封存 0/30**，其中 23/30 是 provider 基础设施失败，不能把 0/30 当纯模型能力。 |
| 23—24 日 | E1-C 从 40 条有准入记录的候选中按固定顺序取 30 条，检查 exact base、官方镜像、Base-Fail 与 Gold-Pass，随后一次性运行。 | 30/30 行、49 次模型调用、65,801 tokens、最终 **1/30**。运行完整性/安全/基础设施达到预设 E2 operational Entry Gate；这**不是**修复质量达标，E2 main 尚未开始。 |
| 24 日 | 已见过结果的 E1-C 30 题转为 DEV；尝试窗口、失败反馈、自动定位、受控编辑及机械修复。 | 同版完整运行 4/30；跨版 best-of 13/30。大量无效编辑、重复补丁、错误位置、预算和网络问题说明同质付费重试不值得继续。 |
| 25 日 | 从“读公开测试断言继续调参”转为修复端/评测端隔离的盲态路线；完成 B4、C4 小样本对照及故障复现 v3/v4。 | B4 两臂 1/4 对 1/4；C4 两臂 0/6 对 0/6，按规则停止。v3 三条未调过的 DEV 故障复现 0/3；v4 对其污染后开发诊断复现 3/3，**不是独立验证，也不是修复 3/3**。 |

### 为什么 9 月 24 日的版本号特别多

v2.1、v3.4、v4.3、v5.0 等是**各自冻结身份的小实验**，不是一次完整 30 题实验逐渐从 1/30 跑到 13/30。旧 30 题每做一轮都更“见过”结果，适合开发诊断，不再能充当全新测试。自动 locator 虽给 **30/30 提供源码窗口**，只有 **16/30 是高置信路径，14/30 为词法回退**；“有窗口”不代表文件选对。把公开新增测试断言放进提示的 v5.0 三题实验 **0 新解**，因此改走盲态路线。

## 最容易被混淆的结果

| 数字 | 正确含义 | 不能改写成 |
|---|---|---|
| Formal E1 0/30 | Wave A 0/12 + Wave B 0/18，已执行；23 条 provider 基础设施失败留在分母。[机器汇总](../data/formal_e1_n30_summary.json) | “30 题没跑”或纯模型修复率为 0 |
| E1-C 1/30 | 原始独立 cohort 的一次性最终 official resolved。[Entry Gate 报告](research/E2_ENTRY_GATE_STATUS_2026-09-23.md) | E2 main 已完成或 E1-C 表现好 |
| DEV 4/30 | 同一旧 30 题上的一次同版完整运行 | 独立未知任务 4/30 |
| DEV best-of 13/30 | 跨多版、逐题取历史最好，帮助定位瓶颈 | 某一个版本一次通过 13/30 |
| B4 1/4 对 1/4；C4 0/6 对 0/6 | 盲态配对 canary，没有 treatment 净新增 official resolved | 盲态机制已验证有效 |
| v4 复现 3/3 | 三条已污染 Django DEV 的零模型故障复现 | 新任务修复 3/3，或独立 canary 通过 |
| 本地 pytest 数百 passed | 代码工程回归 | Autonomous Repair Rate |

**旧 Roadmap 首页的纠错：** 其中“Formal E1 n=30 仍 sealed、未执行”与 [正式汇总](../data/formal_e1_n30_summary.json) 矛盾。正确状态是**已运行、结果封存、resolved=0/30**。“sealed”不能解释为“未执行”。原 E1-B 六条 TEST 未执行，但 fixture confidentiality 已损坏，不能作为 v4 之后的干净确认集。

## 2026-09-25 Strict-v5 最新推进

严格盲态路线已进入真实 strict-v5 post-freeze admission。Playbook **Stage A-E 零模型工程层已 machine READY**：当前 strict-v5 workspace identity 为 **90 files**，SHA `03ede235f688353cdc024f60393d055b97cf0e3ec16e149329e20cbbcc9bd495`；31/31 legacy artifact seal 仍验证 unchanged，contamination ledger 244 identities。B-E 分别覆盖 assertion-blind boundary、固定 DEV30 taxonomy、task-agnostic reproducer engineering、production-only localization/inspect safety；aggregate 明确 `engineering_ready_a_through_e=true`，但 `independent_canary_admission_ready=false / live_allowed=false / c5_allowed=false / fresh30_allowed=false`。当前三题 identity 已冻结并认证；statement strict projection 3/3、exact-base production source 3/3、grader-only **3/3 tasks / 15/15 files** 均已闭环。当前 Strict-v5 全专项 **136 passed / 766 deselected / 5 warnings / 0 failures**；最新全量 **899 passed / 4 skipped / 33 warnings / 0 failures**，Windows 全量命令固定为 `python -X utf8 -m pytest -q`。这些仍是工程回归，不是 repair efficacy。

旧 DEV30 taxonomy 仍为固定分母 30。当前 v5 三题固定为 `pydata__xarray-3993 / sympy__sympy-15308 / django__django-16092`，不得换题。Docker Desktop 的 WSL stale-VHD 问题已修复，Engine 和代理恢复；**Sympy exact official image 已本地就绪**。剩余 xarray + Django：formal xarray 1 MiB 样本 **316,599 B/s**、估算 **6475.1s**，targeted diagnostic Django **300,969 B/s**、估算 **4490.1s**，都不满足 frozen 900s。当前 cache accounting：xarray 还缺 **2.020GB**，需约 **2.245 MB/s**；Sympy 0；Django 仍缺 **1.351GB**，需约 **1.502 MB/s**。GHCR admission 旁路仍因确定性 digest mismatch 关闭。Protocol consistency 全部通过，provider/model calls=0。Base-Fail/Gold-Pass 尚不能对三题完整执行；live/C5/Fresh30 继续关闭。

## 当前真正卡住的四件事

1. **当前首先卡在 frozen 900s budget 下的 xarray/Django official image layer transport，而不是 Docker Desktop 是否能启动。** Docker/WSL/代理已恢复，Sympy 已成功拉取；但 xarray/Django 当前实测约 0.30-0.32 MB/s，明显低于 cache-aware 所需的 2.245/1.502 MB/s。Formal gate 继续在 pull 前 fail-closed；GHCR 不能作为 admission 旁路。
2. **故障复现仍不够通用。** C4 只有 1/6 得到可信补丁前复现，v3 untouched DEV 为 0/3；v4 的 3/3 来自看过机制后的三条 Django DEV，不足以证明新仓库/新题有效。
3. **自动定位和真正修复都未过门槛。** “30/30 有窗口”不是 top-k 正确率；C4 即便接入结构证据也 0/6 official resolved。要分别审计错文件、证据不够、编辑拒绝、目标失败、回归失败和弃答。
4. **没有同版 30/30，也没有新 30 的独立证据。** 重复开发可以帮助找机制，却不能保证必然达 30/30；跨版 best-of 不可拼成一个系统成绩。

## 接下来按什么顺序做

| 顺序 | 必须交付的东西 | 停止/放行条件 |
|---|---|---|
| 1 零模型协议修复 | 禁用题面断言提取路径；做端到端泄漏负面测试；完善任务无关复现与自动 top-k 定位，记录代码/配置 SHA。 | 严格盲态不过，不付费扩批。旧 30 题只作 DEV。 |
| 2 独立 canary 身份 | 从外部仅取元数据，**先冻结**与 232-ID denylist 不重叠的 3 条 instance/repo/base/image；生成 metadata audit + freeze certificate，之后才允许 materialization plan。 | 官方 GitHub tree 只有 instance/repo，HF 仍 DNS 失败，当前没有完整四字段 metadata-only source；不可拿旧题或完整 benchmark row 冒充新题。 |
| 3 配对小实验 | 同模型同预算比较 baseline/treatment；真实模型命令遵守仓库 AGENTS.md 的**精确命令授权**。 | treatment-only official resolved ≥1、baseline-only=0 且无安全/身份/预算异常，才开 C5；否则保留负结果并停。 |
| 4 C5 同版 DEV 30 | 冻结单一代码/模型/提示/预算身份，旧 DEV 30 题一次跑完并独立官方判分。 | 当前 Fresh30 硬门槛要求 **30 attempted / 30 official resolved**。未达标就报告失败，不拼历史版本。 |
| 5 Fresh30 one-shot | 先冻全新 30 条身份，逐题通过 exact-base、官方镜像、Base-Fail/Gold-Pass；配置冻结后一次性运行，30 条都留分母。 | 此批次目前 **0 条选题、0 条运行**；结果可能比 DEV 差，这才是泛化检验。 |
| 6 E2/E3 | E2 main 的 100 题多臂实验、E3 更大规模外部实验另立协议、样本和预算。 | E1-C operational Entry PASS 不自动等于 E2 已启动或获授权。 |

“完美 30/30”是**可检验的目标，不是可承诺的结果**。若长期达不到，需在看全新任务之前决定：保留硬门槛并诚实报告未达成，还是先修改预注册研究问题、改用独立泛化评估；不能见结果后改规则。当前 [v4/Fresh30 预注册](research/E1C_BLIND_REPRODUCER_V4_PREREG_AND_FRESH30_PLAN_2026-09-25.md) 仍 fail-closed，[Fresh30 计划](../data/e1c_fresh30_v4_prereg_plan.json) 明确 gate_ready=false、30 个槽位为空、new_task_tree_touched=false。

## 工作区与阅读顺序

本页创建前，main HEAD 为 ad6426f，工作区已有 **11 个 tracked modified、327 个 untracked status entries**。现有源码、冻结文件和 .codex/e1c 产物均不清理、不覆盖；新 live 前先审核差异并固定可复现身份。最近 v4/gate 专项回归 **14 passed / 4 warnings**；历史两次全量回归分别 **714 passed / 4 skipped** 和 **713 passed / 1 failed / 4 skipped**，后一失败是 Streamlit AppTest 8 秒冷启动超时。这些数都不是修复率。

**以后阅读顺序：** 本页看全貌 → [E1-C 当前交接](research/README.md)看当前门槛 → [集中日志](research/PROGRESS_LOG_ARCHIVE.md)查历史 → 对应 RESULT/freeze/机器 artifact 核实数字。不要从旧实验文件里写的“下一步”直接启动新实验。

**详细执行作业书：** 从严格盲态改造、独立 canary、同版 DEV 30/30 到全新 Fresh30 one-shot 的逐步条件，见 [E1-C strict-blind 详细计划](research/E1C_STRICT_BLIND_DEV30_TO_FRESH30_PLAYBOOK.md)。该文件是待执行计划，不代表门槛已通过。

## 2026-09-27 E1-C strict-successor CTI checkpoint

按现有 strict-blind PLAYBOOK 继续且未重跑 sealed/frozen 历史实验。successor canonical-testbed-interpreter (CTI) DEV30 gate 已通过：30/30 固定分母、2 个 repo 的 canonical interpreter、2 个 compile-ready candidates、leakage forbidden hits=0、provider calls=0，并在旧 DEV 上得到 1 个 trusted reproducer；这仍是开发证据，不是独立 repair efficacy。随后已在读取 task 内容前冻结新的三仓库独立 canary：astropy__astropy-12962、matplotlib__matplotlib-26291、sphinx-doc__sphinx-7757，并从 frozen source revision 3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d materialize 三条 metadata。初始 Docker cache 为 0/3；当前已按既有 900s budget 启动 astropy official image materialization，Job 8aa88def-901f-436f-853d-b52cd83b213a 尚在运行。真实模型 paired canary、C5、DEV30、Fresh30 均继续关闭；下一 gate 是完成/判定该 official image materialization，再继续 immutable image identity 与其余 admission prerequisites。机器 checkpoint：../data/e1c_strict_successor_cti_checkpoint_2026-09-27.json。

### 2026-09-27 successor-CTI continuation

复用既有 Job `8aa88def-901f-436f-853d-b52cd83b213a`，未重复拉取：astropy official image 已在原 frozen 900s budget 内成功完成，exit=0，registry digest=`sha256:5dc63f2dfdb44cbffd610371ead4822c0ee13944499f1c23f77f10f9f4b2a000`。随后尝试执行本地 immutable image inspect 时，WebCodex execution route 在命令启动前因 `runtime_project_id does not match the runner` 拒绝；明确没有命令启动、没有文件副作用，因此该项记为 Runner recovery-identity 基础设施 blocker，而不是 Docker/实验失败。已从冻结 checkpoint 恢复剩余 exact images：matplotlib-26291 与 sphinx-7757；它们尚未 materialize。Stage G 仍要求三条 image identity、exact-base source、Base-Fail、independent Gold-Pass、sanitized issue、probe/prompt reserve 与 Docker resource gate 全部完成，之后才能展示精确 paired-live 命令请求授权。provider/model calls 仍为 0；C5/DEV30/Fresh30 继续关闭。

本轮继续后确认该 execution blocker 可通过使用 Runner 注册的完整 project identity 消除；astropy 本地 `RepoDigest` 已与上述 registry digest 精确一致，本地 image ID=`sha256:7ebf14d6cfcf6fca5796e04bd957ee3217611420af6ca48007715ce501b10812`。随后严格按冻结顺序只启动一次 matplotlib official image pull，仍使用 900s budget，durable Job=`b210b849-f25a-4b1c-ad58-d02fbfed891b`；当前尚在运行，不得重复启动。并行只做了只读 Docker resource probe：4 images / 6.885GB / 5.466GB reclaimable，未执行 prune/delete。sphinx 仍等待 matplotlib terminal 后才允许启动。provider/model calls 仍为 0，协议未改，paired canary/C5/DEV30/Fresh30 继续关闭。

继续观察而未重启 matplotlib Job 后，其在 frozen 900s budget 内成功 terminal（exit=0），official/local RepoDigest=`sha256:1b5b3c1164c4f2a4210bec437b5416fb6346560c09b49e17ede58d045e8b8231`，local image ID=`sha256:757855ad838faa91630ec9c1be7207a03a3edcd8eba0c23e974a1d11aa783625`。随后严格串行只启动一次 sphinx official pull，Job=`1c1ae975-9cc2-49ef-8a47-d516812391df`，同样 900s budget；当前仍运行，必须继续 observe 而不是重复 pull。三镜像中 astropy+matplotlib identity 已闭环，sphinx 是当前唯一 image gate。provider/model calls=0，未改协议。

随后 sphinx 原 Job 也在 frozen 900s budget 内成功完成（exit=0），official/local RepoDigest=`sha256:afdd76c95a6cc039f5f2aa49ba8f66da3eddc72a0c11bbc32666b99496f237c0`，local image ID=`sha256:2ec63928131f897d3eb58b599aa6e4c6fe34db8b1e523ea7f075c8da70102b02`。至此 successor independent canary 的三条 official image identity 已 **3/3 闭环**。另执行现有只读 `experiment_preflight.py --network`：provider_calls=0；Docker daemon、official parser、旧 30-task task/source/clean、GitHub HTTPS 均 PASS，DeepSeek endpoint 可达（401），Docker Hub auth HEAD 出现 `WinError 10054`。该 preflight 的 `local_images 0/30` 指旧 candidate_manifest 30 题，与本次 successor 三题 canary 不同，不能用于否定当前 3/3 image gate。下一 gate 转为三题 exact-base/source + official Base-Fail/independent Gold-Pass admission，再做 sanitized issue/probe/prompt reserve/resource gate；live 仍关闭。

进一步核查 Stage G admission workspace：三条新 canary 在旧 `.codex/e1c/tasks/<iid>`、`admission_v2/<iid>` 与 exact-base repo 目录均不存在，因此旧 cohort 的 Base-Fail/Gold-Pass 记录不能被复用成新 canary evidence。已找到可复用的既有 `e1c-admission-phase-v2` 记录语义和 official parser commit `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`；下一步必须先把已经冻结的三个 task blob（保持 frozen source revision/blob SHA）物化到独立 successor-canary admission workspace，再物化 exact-base source，之后才能合法跑 Base-Fail/Gold-Pass。该发现是 admission 前置缺失，不是实验失败；provider/model calls 仍为 0。

本轮已把三个 preregistered task blob 正式物化到独立 `.codex/e1c/successor_cti_canary/`：Astropy `cad89687...`, Matplotlib `47cd2ea4...`, Sphinx `9a9bd8e6...`，三者均通过重新计算 Git blob SHA 的精确 identity 校验；`materialization.json` 记录 source revision、blob SHA、content SHA256 和 size，provider/model calls=0。随后检查 official image `/testbed`，确认三张镜像都含 frozen base commit object，但不能直接把 image HEAD/worktree 当 exact-base：Astropy 有环境导致的 `pyproject.toml` 修改，Matplotlib/Sphinx HEAD 是额外 SWE-bench setup commit。尝试从 image 内 Git object database 零网络导出 exact-base 时，单个 120s job 在复制 Astropy `.git` 阶段 timeout，留下 partial/dirty Astropy scratch directory，Matplotlib/Sphinx 尚未开始；没有生成 `exact_base_materialization.json`。因此这次 timeout 记为 materialization blocker，不计实验失败，Base-Fail/Gold-Pass 尚未启动。下一 gate 改为使用更快的 archive/export 路径分别完成 3/3 clean exact-base identity，再进入 official Base-Fail/Gold-Pass。

已按该 gate 恢复：仅删除 dedicated canary scratch 中上轮 partial Astropy export，改用 immutable official image 内 frozen commit 的 `git archive`，Job `6b5d6351-b6e5-4ac6-a30a-f6f7ac5848d0` 最终 exit=0。`exact_base_materialization.json` 已记录三题 frozen base + Git tree + archive SHA256：Astropy tree `f0a8a0e5...31f1`、Matplotlib `cb67fa49...7033`、Sphinx `07b18305...d114`。Windows tar 展开 Matplotlib 时对若干 symbolic-link-like SVG entry 报 `Invalid argument`，因此 Windows 展开目录/file_count 不作为 canonical clean-tree evidence；后续 Base-Fail/Gold-Pass 将直接在 official Linux image 中 `reset/clean` 到 frozen base 并核验 HEAD/clean，再复用既有 admission_v2 parser/grader。task identity、image identity、frozen base commit/tree identity 现均 3/3；provider/model calls=0，尚未运行 Base-Fail。

继续追到 admission 的真实执行入口后，已从旧 cohort `admission_v2/*/{base,gold}.json` 恢复 frozen grader 语义：official parser commit=`02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`、immutable image digest/source tree checks、image setup diff/patch overlap、`--network none`、read-only `/admission` mount、`eval.sh`、independent `gold.patch`、raw log SHA256 与 F2P/P2P parser fields。与此同时确认新 canary 的 frozen `task.yaml` 仅含 public metadata（repo/base/image/version/log_parser/datasets），不包含 `eval.sh`、`gold.patch` 或 F2P/P2P expectation；因此现在不能凭空构造 Base-Fail 命令。下一 gate 是从同一 official SWE-bench evaluator/source revision 独立物化这三题的 admission payload 并记录 provenance/hash，之后才能合法运行 Base-Fail→Gold-Pass。旧 cohort payload/result 不会被复用为新 canary evidence；provider/model calls 仍为 0。

本轮继续追 payload provenance：本地 `.codex/e1c/swebench-harness` 的 Git object database 已确认精确锁定 official parser/evaluator commit `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`；在不展开/修改 sparse checkout 的情况下直接读取该 commit 源码，确认 `make_test_spec` 必须由完整 dataset row 提供 `eval_script`、`FAIL_TO_PASS`、`PASS_TO_PASS`，gold prediction 则来自同一 row 的 `patch`。HF datasets-server 的 SWE-bench test `first-rows` 当前可达并确认公开 schema 含 `patch/test_patch/eval_script/FAIL_TO_PASS/PASS_TO_PASS`，但按 instance_id 的 `filter` 请求返回 422，`search` 请求长时间 stall，因此本轮没有伪造或部分生成 canary payload。该问题记为 official dataset-row transport/query blocker，不计实验失败；下一步优先复用本机完整 dataset cache，否则改用稳定 official dataset download/API 精确取三条 frozen row。Base-Fail/Gold-Pass 仍未运行，provider/model calls=0。

随后已绕过不稳定 row API，使用 HF official Parquet endpoint 下载 SWE-bench test `0.parquet`（33,293,897 bytes，SHA256 `d4f5a245c75319fa8240c540674958c4d491e82edf274b144d43836bdcbc4567`）；三个 frozen instance_id 3/3 精确命中 preregistered base commit。已为每题独立物化 `eval.sh / gold.patch / test.patch / FAIL_TO_PASS.json / PASS_TO_PASS.json / provenance.json` 并记录逐文件 SHA256。随后三题 Base raw phase 均已在 immutable official Linux image、`--network none`、reset/clean frozen base 下完成：Astropy 2 failed/96 passed（raw SHA `d1f10978...8974`）、Matplotlib 1 failed/49 passed（`b62a913f...c941`）、Sphinx 1 failed/33 passed（`731b8d42...d5e7`）。但这些 pytest summary 暂不当作 official Base-Fail 判定：直接 import frozen harness 时遇到 host Python `docker.models` package conflict。下一 gate 是在不改变 grader semantics 的前提下，用隔离兼容环境或 object-level frozen parser 对三份 raw log 做正式 F2P/P2P classification；只有 official Base-Fail 通过后才执行 independent Gold-Pass。provider/model calls 仍为 0。

已继续完成 frozen parser 隔离：没有修改 grader，而是从 commit `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e` 直接导出 grading/types/constants/log_parsers/infra_failure 对象文件到 dedicated `frozen_parser_bundle`，在 UTF-8 隔离环境运行原代码。正式 Base 判定为：Astropy F2P 0/2、P2P 96/0；Matplotlib F2P 0/1、P2P 49/0，二者 clean Base-Fail；Sphinx F2P 0/1 但 P2P 0/33，因此不满足 clean Base-Fail，不能丢题或假装通过。已只对前两题执行 independent Gold-Pass：Astropy raw SHA `6c1a550c...853b`，frozen parser resolved=true、F2P 2/0、P2P 96/0；Matplotlib raw SHA `666ac056...b1e8`，resolved=true、F2P 1/0、P2P 49/0。Sphinx Gold 未运行。下一 gate 是审计 Sphinx raw log status-map 与 official P2P id 的 key mismatch，判断是 environment/log-format identity anomaly 还是真正 admission failure；在 3/3 admission 前 live canary 继续 CLOSED。

Sphinx anomaly 已定位到 frozen evaluator 的可观测性边界：`parse_log_sphinx=parse_log_pytest_v2` 只能记录显式 `PASSED/FAILED` 行，而该 official eval command 的 pytest quiet progress 把 33 个通过 P2P 只打印为 dots；因此 parser status-map 只有目标 FAILED 1 条，33 个 P2P 全部因 absent 被判 failure。raw suite 明确仍是 `1 failed, 33 passed`，所以不能解释成 33 个测试真实回归。另发现 earlier manual admission 未复现 frozen `make_test_spec -> record_test_exit_code` 注入；已按 frozen code 生成 LF-only `eval.official.sh` 并 3/3 重跑，得到 Astropy `2 failed/96 passed`, test exit 1, SHA `d6222baa...4dc6`；Matplotlib `1/49`, exit 1, SHA `c08331a6...504f`；Sphinx `1/33`, exit 1, SHA `f0cd8645...c7be`。正式 parser 结果仍为前两题 clean Base-Fail、Sphinx P2P unobserved 0/33。期间一次 PowerShell CRLF 生成脚本导致三题 exit 4/0 tests，已明确判为 generator error，不作为实验证据。下一步只检查 frozen PLAYBOOK/admission_v2 是否已有这种 quiet-pytest observability anomaly 的预注册处理；若没有，不会自行加 `-rA/-vv`、改 parser、换题或放宽 gate，而是 seal Sphinx admission blocker。

已完成该检查并封板：历史 `admission_v2` 中 Sphinx 8056/9230/9673 的 frozen parser admission 都依赖 eval log 中显式 `PASSED` 行，没有 raw summary fallback；successor PLAYBOOK/artifacts 未定义 quiet-pytest observability exception。当前 `e1c_strict_successor_cti_canary_identity.json` 只冻结恰好三题，也没有 preregistered substitute/backup 顺序，因此不能在看到 Sphinx admission 结果后换题。已生成 `.codex/e1c/successor_cti_canary/admission_summary.json`，SHA `57446395934e4694500dcb46f0ef040c7e093303f4778bdb7bc597ce01267cf5`：Astropy/Matplotlib 为 clean Base-Fail + Gold-Pass，Sphinx 为 retained blocker，`admission_complete=false`, `admitted_count=2/3`。因此当前 frozen identity 的 paired live canary 正式保持 NOT RUN / BLOCKED；这不是模型 0/3 或 canary failure。后续若继续，只能先另行预注册 successor evaluation protocol/identity，且不得追溯修改本次 frozen canary。

已按该 gate 继续并在读取任何新 task YAML 前冻结 CTI2：`data/e1c_strict_successor_cti2_admission_protocol.json` SHA `6a6c20df874a202af881ae0d0bb2f502ee0612c45cf86456b44619e2930f1575`，预注册 3 primary + 3 ordered environmental reserves；只有 image/source/evaluator-observability/container-runtime 等预定义 admission infrastructure failure 可按固定顺序替补，valid Base-Fail、Gold-Pass failure、题目内容/难度、模型结果和 post-admission probe 均禁止触发替补。随后 metadata-only 冻结 `data/e1c_strict_successor_cti2_canary_identity.json` SHA `94be4c30cb70f20ef1da90db800f8aa3bd51929743b009a9d08ed7b7809850d4`：primary=`pydata__xarray-4939`,`pvlib__pvlib-python-1239`,`scikit-learn__scikit-learn-25370`；reserve 顺序=`psf__requests-1327`,`django__django-9296`,`sympy__sympy-15555`，reserve 内容仍未读取。三条 primary task blob 已 materialize 且 Git SHA 3/3 一致，manifest SHA `2dd9f3e922b7ee2939151b1db959c263adbf223d5a89626e1025fb21cd732814`。当前零模型 blockers：三张 primary official image 均未本地化；xarray pull 能连接 Docker Hub 并完成部分层，但 WebCodex one-shot 在 120 秒强制结束，尚未达到既有 900 秒 image gate，故不能提前启用 reserve；official cached test parquet 已取得 xarray 84/1797 与 scikit-learn 1/59 F2P/P2P，pvlib 属 dev split，而 runner 的 Hugging Face DNS 当前 `getaddrinfo 11002`，official dev row 尚未 materialize。provider/model calls 仍为 0。



### 2026-09-27 CTI2 admission complete; Stage D preflight blocks paired live

继续严格复用 frozen/sealed 产物，没有重跑已完成的 xarray admission，也没有读取 reserve #2/#3。CTI2 active set 最终为 `pydata__xarray-4939`、`scikit-learn__scikit-learn-25370`、`psf__requests-1327`（pvlib 仅按预注册 infrastructure 条件替换为 reserve #1）。scikit-learn Base frozen-parser 为 F2P 0/1、P2P 59/0；requests Base 为 F2P 0/1、P2P 31/0；二者均 `resolved=false, infra=false`。随后 independent Gold：scikit-learn F2P 1/0、P2P 59/0，requests F2P 1/0、P2P 31/0，均 `resolved=true, infra=false`。结合此前 xarray，CTI2 admission 现为 **3/3 complete**；`.codex/e1c/successor_cti2_canary/admission_summary.json` SHA256=`a0cd5838c660d30034af37c69781276047d10d6dc752609b8aefb83acaca8f45`。provider/model calls 仍为 0。

随后按 PLAYBOOK Stage D 只使用公开题面经 frozen strict-v5 deterministic projection 后的自然语言、exact-base 生产源码和任务无关定位/复现机制做零模型 preflight；三题 issue projection 均成功，自动 localization 也均产生生产源码候选，但 frozen strict-v6 natural-language witness plan 对三题均返回 `no_reproducer`。successor expected-failure compiler 的补充检查也没有形成可执行可信场景：xarray/requests 无公开 exception contract；scikit-learn 虽有公开 `InvalidIndexError` contract，但 frozen production candidates 无 safe compiled scenario。未使用 official Base/Gold failure/test assertions 反推 probe。机器结果 `data/e1c_strict_successor_cti2_stage_d_preflight.json` SHA256=`48f8def9a42d1efa28ffa4eaacae0d631de34551d1a507176f18e27e10ca19c8`：trusted reproducer **0/3**，预注册门槛要求 **>=2/3**，因此 Stage D `gate_passed=false`。

资源侧另封存 `data/e1c_strict_successor_cti2_resource_preflight.json` SHA256=`7fa9ba4ca9415a4017ed7d710bcac68766a8d3ce4e589fa1810fe2b233964b67`，三张 active official image 均在本地。当前结论不是 paired canary 0/3，而是 **paired live canary NOT RUN / CLOSED**：admission 已 3/3，但 trusted-reproducer 前置 gate 未过。不得在这三题上根据后验结果补专用 probe，也不得越过 gate 请求模型调用。按 Stage F，下一合法工作是回到 DEV/聚合机制证据，形成 materially new、task-agnostic reproducer mechanism；其零模型 gate 通过后，再先冻结一个新的、不重叠的 independent canary identity，之后才可看新题内容。C5/DEV30/Fresh30 继续 CLOSED。最新 checkpoint：`data/e1c_strict_successor_cti_checkpoint_2026-09-27.json`。


### 2026-09-27 Stage F failure/ROI audit + non-destructive workspace protection

按最新 checkpoint 继续，但没有越过 CTI2 Stage D 的 frozen gate。首先对工作区做只读保护审计：HEAD 保持 `ad6426fc9f11c7caecd969ded11cd69c7d8a11cb`；未执行 `git reset`、`git clean`、删除既有 untracked artifact 或 Docker prune。审计时有 11 个 tracked dirty path、788 个 untracked path；考虑到 hygiene heuristic 会把正式研究 artifact 标为 temporary，本轮不按该标签自动清理。已生成 `data/e1c_workspace_protection_inventory_2026-09-27.json`，记录 393 个研究文件 path/SHA，SHA256=`1161c106733f146d431db019666483111cefd576ed3ee3644aae95576c6cbc6d`。

根据 V25 seal 的 two-round stop rule 和当前 CTI2 0/3 trusted-reproducer preflight，完成零 provider failure/ROI audit：`data/e1c_strict_successor_failure_roi_audit_2026-09-27.json` SHA256=`cb15064f1a3fe39c4bc3aa7732ec82e86461c9541fccd9471beb5e6b33ae8af4`。核心结论是 localization consensus 已不是主要瓶颈：V25 old-DEV 6/6 有 consensus candidate、total family support=17，但 expected-failure executable compilation 仅覆盖 old DEV 2/30，CTI2 independent preflight trusted reproducer=0/3。继续增加定位 family 的预期信息价值低，下一机制必须直接改善可执行、可判定的 pre-patch failure reproduction。

因此只冻结了 development-only change card `data/e1c_strict_successor_typed_contract_change_card_2026-09-27.json`，SHA256=`be547832cddccb946631296a24e97caa812205dcf2d3e9dc875527333f51ee3b`。假设限定为 `projected natural-language behavioral claim -> typed executable contract`；只允许 projected issue、production localization/source、exact-base canonical offline runtime；禁止 task-id rule、benchmark assertion/test、Gold、official Base failing assertion 和 independent-canary task-specific tuning。新 DEV gate 要求至少 2 个跨 repo trusted old-DEV pre-patch reproducer、重复稳定、network disabled、0 leakage、focused tests、provider_calls=0。

尝试只读恢复旧 DEV repair-visible bundle 的 `.codex` 全树扫描在 60 秒超时，无输出、无状态变更；该项只记 diagnostic timeout，不记实验失败。为避免把 CTI2 independent tasks 变成开发集，本轮没有拿 CTI2 三题继续调机制，也没有冻结新的 canary。下一唯一合法 gate 是先恢复/确定性重建 old-DEV projected issue + exact-base production source 输入，并在旧 DEV 上证明 typed-contract compiler 的跨 repo trusted-reproducer gain；未通过前 paired live、C5/DEV30、Fresh30 全部保持 CLOSED。


### 2026-09-27 Stage F old-DEV source-contract recovery

继续最新 checkpoint 后，已定向恢复全部 6 个 old-DEV repair-visible bundle，来源仅为既有 `.codex/e1c/strict-v6/postfreeze-v1` 与 `strict-v7/postfreeze-v1` 的 `problem_statement.md + exact-base source`，未使用 CTI2 independent task 作为开发反馈。固定输入 inventory：`data/e1c_strict_successor_typed_contract_old_dev_inputs.json` SHA256=`2f2ad6bb4b27f3318b5cde24f5dafbfe54d32edfbe1981f2af2cc1c764553ad3`。

复用既有 frozen generic source contracts 对 exact-base old DEV 重新执行，得到 2 个跨 repo 的稳定 source-level pre-patch failure witness：`django__django-15569` 的 `_unregister_lookup()` 缺少 clear/invalidate effect；`scikit-learn__scikit-learn-13313` 的 frozen never-used witness 没有发现 external call/registration。结果 artifact `data/e1c_strict_successor_existing_source_contract_old_dev_eval.json` SHA256=`95113442e2ed607d4a8ee81ce49ffcc32bfb35243294d16ea8a79e8697c2fca4`；两次重复 evaluation 完全一致，repeatability artifact SHA256=`c4be9b1ea181e04cf1fc28cff1ffda7df5f0aa732e8f2dbc895055b1016937c9`。这些证据只称 source-level failure witness，不提升为 canonical trusted reproducer。

Focused regression 使用项目锁定环境 `uv run pytest`：12 passed in 0.12s。系统 Python 直接调用 pytest 因环境没有 pytest 失败，该次调用无 WebCodex 文件修改，不属于实验失败。Leakage audit 对新 source-contract artifacts 检查 `FAIL_TO_PASS/PASS_TO_PASS/gold.patch/test.patch/benchmark_assertion=true`，0 hit，artifact SHA256=`325b106f3b6905bd654a4ca3201204db4c9e5cf7601830b1407c36b9bb16b794`。

当前唯一 blocker 是 canonical runtime admission：`django__django-15569` 与 `scikit-learn__scikit-learn-13313` 对应 SWE-bench images 当前均不在本机 Docker cache，因此 trusted runtime reproducer count 仍严格记为 0。Admission artifact `data/e1c_strict_successor_source_contract_runtime_admission.json` SHA256=`9fb6cadc2a796c6bb07ae0d923a19d34c30f712b9072106e4fc0bbee23de7b6c`。下一 gate 是只 materialize 这两个已经由 old-DEV 证据确定的 canonical images，验证 immutable digest/exact-base，然后 network disabled 下重复运行 frozen contracts；要求 >=2 cross-repo trusted reproducible pre-patch failures。通过前不得冻结新 independent canary，paired live/C5/DEV30/Fresh30 继续 CLOSED，provider_calls=0。


### 2026-09-27 Stage F canonical-runtime acquisition + workspace hygiene

按最新 checkpoint 继续后，先执行非破坏性 workspace hygiene。`workspace_hygiene_check` 的 temporary-file 启发式命中多条既有研究脚本/manifest，因此未据此删除任何文件；本轮没有执行 `git reset`、`git clean`、文件批量删除、Docker prune 或缓存清理。新建只读保护快照 `data/e1c_workspace_hygiene_snapshot_2026-09-27.json`，SHA256=`4c363218973a087c3ad5883adb51317ae0781b8d2575f81961c98aad73fab984`。HEAD 保持 `ad6426fc9f11c7caecd969ded11cd69c7d8a11cb`。

重新核验两个 old-DEV source roots：`django__django-15569` HEAD=`884b4c27f506b3c29d58509fc83a35c30ea10d94`、`scikit-learn__scikit-learn-13313` HEAD=`cdfca8cba33be63ef50ba9e14d8823cc551baf92`，均 exact-base 且 clean。证据 `data/e1c_strict_successor_source_contract_source_identity_recheck.json` SHA256=`d3c0c3c75495238bc81d2f4bc6c934e427c0e7f4a907d7596532a4a539a23555`。

Canonical image acquisition 严格顺序执行，仅启动 `django__django-15569` 一次 pull（Job `7cbe0576-a632-460b-9af7-bf6329ef144f`）。Docker 复用了 6 个已有 layers，但固定 120s WebCodex 通道结束时仍有 4 个 layers pending，job 以 timeout 终止；image 尚未 materialize，且无残留 running container。为避免重复下载和并发争抢，没有启动 scikit-learn 第二个 pull。Acquisition ledger `data/e1c_strict_successor_source_contract_image_acquisition.json` SHA256=`0e32db7d13a3ce4a04834ec2002a9904dec94485193e972caaf6a7ba0885bcce`。

因此当前研究状态不变：2 个跨 repo source-level pre-patch failure witnesses 已稳定重复，但 canonical `trusted_runtime_reproducer_count=0`。下一唯一 gate 是通过可超过 120s 的执行路径继续完成 django image，再顺序 materialize scikit-learn image；两者均记录 immutable RepoDigest 后，才在 `--network none` 下对 frozen behavior contracts 各重复执行两次。要求 >=2 cross-repo trusted reproducible pre-patch failures、zero leakage、provider_calls=0 后，才能冻结新的 non-overlapping independent canary。paired live、C5/DEV30、Fresh30 继续 CLOSED。


### 2026-09-27 Source-contract DEV gate passed; new independent identity frozen

用户完成两个 old-DEV canonical image pull 后继续执行。RepoDigest：Django-15569=`sha256:13d3ee8c6e4aa4d5c34024f32ada971a11153bfe0023339ddc4bdfb0ca48925d`；scikit-learn-13313=`sha256:d2cf61b57c1e5e6e4a3cc80978ca4d606204bb5c24d0296081a0608cd69921ed`。Image/base identity 通过：scikit HEAD exact base；Django setup HEAD 与 frozen base tree 相同、base ancestor=true、tree clean。

Frozen Django source-effect contract 在 canonical `--network none` image 中独立执行两次，均稳定 pre-patch failure，result SHA=`6500186e483ca530e6205deed3aaa1f3c60a44b337ffdfeee9bba5d476f188ed`。scikit 第一次调用因旧 image Python 不支持 evaluator 文件的 `from __future__ import annotations` 而未进入 contract，严格记 evaluator-portability invalid，不记 task failure/success。随后创建只做语法兼容、保持 frozen source_usage AST 语义的 standalone evaluator（SHA256=`947e663e328c822fb368aff5fe88301ddb773d4ed27af64000a16668a9fac48f`；无 task/test/Gold 输入），在 canonical network-none image 中两次运行均稳定 pre-patch failure，result SHA=`8c0635252afc34b8f11817935ce3a4876186b53c9dace559a08c5e16e5223526`，与 frozen host evaluator 完全相同。

因此 development gate `data/e1c_strict_successor_source_contract_development_gate.json` SHA256=`42bc8bbde0d06b180b264b42de4946b16a879e376e23ca548341749408c1b07a` 正式 `gate_passed=true`：trusted runtime reproducer=2、跨 2 repos、每题双重复、network-none、leakage pass、provider_calls=0。

按 PLAYBOOK 在查看新题内容前冻结新的 non-overlapping metadata-only identity：`data/e1c_strict_successor_source_contract_canary_identity.json` SHA256=`939ef8b897f12d145d10ddcfdb477d8df42b1d166ff6e341879b010ca1c09499`。Primary=`django__django-12453`, `sympy__sympy-13761`, `matplotlib__matplotlib-21559`；ordered environmental reserves=`scikit-learn__scikit-learn-12834`, `pylint-dev__pylint-8819`, `sqlfluff__sqlfluff-1577`，reserve 内容仍未读取。

冻结后尝试仅 materialize 三个 primary task YAML，但当前 project Git 不包含 frozen SWE-bench inventory revision `3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d`，三个 `git show` 均返回 128；因此没有 task content 被读取，blind identity 仍有效。证据 `data/e1c_strict_successor_source_contract_primary_materialization.json` SHA256=`176f9c5fa44388510859a44753ec93ccad3ebd3c52ab9b9af1fae51dce873a5d`。下一 gate 是恢复该 frozen inventory revision 或 byte-identical cache，只 materialize 三个 primary，然后继续 admission + issue projection + source-contract trusted reproducer preflight；>=2/3 前不得进入 paired live。C5/DEV30/Fresh30 继续 CLOSED。
