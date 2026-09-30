# 工作区重整、保全与发布记录

日期：2026-09-30。范围：当前项目的阅读入口、记录索引、交接与Git发布；不是磁盘清理或模型实验。

## 1. 保全措施

整理前HEAD为`ad6426fc9f11c7caecd969ded11cd69c7d8a11cb`。原工作区有11个已跟踪修改；`--untracked-files=all`下合计907个待提交文件。使用现有`scripts/research_workspace_snapshot.py`建立本地只读清单：`.codex/maintenance/roadmap-2026-09-30/before.json`，snapshot SHA `7c49d4ea840d923a830b827339da2416446b93bc3aa615e62f3a910afc0485c1`。它不包含被Git忽略的大型运行目录的全量备份。

重写前先完整复制四份入口，源与副本SHA逐一相同；置于同目录以保留原相对链接：

| 原入口 → 历史副本 | 原字节SHA-256 |
|---|---|
| Roadmap → [HISTORY](../PROGRESS_RESEARCH_ROADMAP_HISTORY_2026-09-30.md) | `68491174f7fa6b1834ccfd67543eded81da85b21fa4d5adda0e4c4c85b9d4c10` |
| Roadmap 2 → [HISTORY](../PROGRESS_RESEARCH_ROADMAP_2_HISTORY_2026-09-30.md) | `6fd0bff37398d4a044e54e92abf301b67befa36743b0aa05e90a87157418bbf0` |
| 研究README → [HISTORY](README_HISTORY_2026-09-30.md) | `3c7d41ef015d8183c648187d569fe3e7327725fdacf7cce1762e710186f24374` |
| 旧交接 → [HISTORY](NEXT_SESSION_HANDOFF_HISTORY_2026-09-30.md) | `c152b2cb6406be42159df1bbbd228780cea254bc2388a169af6bf08ceee4f49f` |

没有删除、移动已有源码、实验freeze、结果、失败账本、镜像缓存或本机配置。旧`.codex`运行证据保留原位。没有执行git clean/reset、Docker prune、WSL卸载、VHDX操作或tunnel变更。整理采用“入口重写+原文快照+索引”，避免改路径破坏冻结代码。

## 2. 整理后的职责

- 根README：明确上游归属和本分支研究入口，原上游说明保留。
- Roadmap 1：项目总览、实质实现、证据与结论边界。
- Roadmap 2：唯一当前状态、阻塞和条件式待办。
- 研究README：精简导航。
- NEXT_SESSION_HANDOFF：云端和本机职责、可执行命令及回传要求。
- 一周计划：有来源的研究假设、同预算消融、每日任务、失败分支。
- 逐轮流水继续写原集中日志及9月27日续档；历史freeze/result不重写。

## 3. 本次验证

| 检查 | 本次结果 |
|---|---|
| AGENTS指定六文件Ruff | 通过 |
| 全仓Ruff（包含大量历史脚本） | 失败：2,225条既有风格/导入等问题；未为造绿批量改写冻结代码 |
| 预算与V3 runner专项 | 18 passed / 4 warnings |
| 完整pytest | **1084 passed / 4 skipped / 33 warnings / 0 failed，53.96秒** |
| 单独V3 compact preflight | 失败：Windows子进程非UTF-8输出导致reader线程UnicodeDecodeError，随后stdout=None引发TypeError；未调用provider |
| 当前canary v2方法 | 14份文件与原freeze SHA一致；不因重整重新冻结 |

完整测试命令：`uv run --frozen --offline python -X utf8 -m pytest -q`。四项skip来自既有测试配置，未新增skip或放宽断言。完整pytest通过不替代独立preflight结果，也不证明真实修复或Docker端到端已过。全仓Ruff不通过，因此不能宣称全部质量检查或GitHub CI已绿；历史脚本的lint债务需在保持冻结原件的条件下单独处理。

V3 preflight遗留项进入一周D1：定位子进程编码来源，以新修复记录解决；本次未改动冻结实验方法来消除它。历史冷启动超时原记录保留，本次单次回归确为零失败。

## 4. 发布与本地保留

发布候选由精确路径清单选择，包括待提交研究源码、测试、协议、公开元数据和结果摘要；进行大小、UTF-8/历史编码、常见provider/GitHub token、私钥与带凭据URL检查。扫描是启发式检查，不是绝对无泄漏证明；不打印可能的密钥值。

本地保留：`.env*`、`.codex/`、`.external/`、原始评分材料、镜像和`data/wave_b_sealed_task_spec.json`；另有含原始旧DEV题面的`data/e1c_strict_successor_typed_contract_old_dev_inputs.json`保留本地。新`.gitignore`防止这些内容误入提交；没有删除它们。既有Git历史不重写。两份历史文档有原编码异常，保留原字节，避免为了展示而损坏冻结证据。

新增`.gitattributes`让研究身份相关文件禁用自动换行转换；不对冻结源码运行renormalize或批量格式化。三个当前入口/配置文件定向重新入索引，以保存其原字节；Linux/Windows新clone仍须按freeze核验身份。

本次公开文件的精确路径和原始字节SHA见[发布清单](../../data/research_publication_manifest_2026-09-30.json)。清单不自我哈希；本地原始证据仍按既有协议保留。整理后原907个文件无缺失，除五份入口/续档文档的预期改写或追加外，其余原文件哈希未变。

GitHub同步目标是用户fork `qr7896/agent-service-toolkit`，不写上游。直连GitHub超时，使用现有本地7892代理仅用于小型Git同步；无系统代理修改，无镜像下载。本次提交SHA以Git历史为准，发布成功须另核远端引用，不能仅凭本地commit宣称已同步。

## 5. 给审阅者的说明

仓库公开的是实现、协议、摘要与哈希索引；本地原始任务、容器和provider日志不自动公开。缺少这些材料时，可以复跑工程测试，但不能声称独立复现付费实验。结果中的人工语义审核、开发集污染、环境失败、负结果均在新入口披露。

一周的目标是可验收工程和有信息价值的实验证据；30/30仍是未完成的质量目标。研究技能影响了本次组织方式：明确区分观测、规划与假设，保留候选比较及有限文献核验，不把已有的issue-to-test流程包装成首创。
