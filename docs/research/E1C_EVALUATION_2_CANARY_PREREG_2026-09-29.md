# E1-C evaluation_2：独立 canary 预注册方案（仅方案，未选题）

状态：`plan_frozen_only`。DEV12 的数量门槛为 2 个不同仓库的可信补丁前复现；一个来自保存的模型 probe，另一个来自确定性公开构造参数规则。它们不是同一生成机制的独立泛化证据。本文件**没有选择、读取或运行**任何新 canary；不授权 sealed TEST、Fresh30 或修复 live。

## 预注册选择

1. 候选池固定为 `data/e1c_strict_v20_clean_metadata_pool.json`，文件 SHA-256 `7f1b59aff7411df40ec5d877f726bcb4161e7238e961cda859fb3b489f764ab2`，只读身份、仓库名和冻结 Git 树中的 YAML blob 元数据，不读任务正文、测试或结果。
2. 排除 `data/e1c_strict_v5_contamination_ledger.json` 的 `identities`（SHA-256 `8468c2f4baa413351dd924f5d418a09857ea59d5a5e2890d3f405ff270e5022b`）、`data/e1c_reproducer_dev12_identity.json` 的全部 12 个 `tasks`（SHA-256 `3a374504aebcd88b935ac3d4f020a72a5e51a01f7fa46cf203fc7487c791fe4a`），以及后者冻结的 `exclusion_files` 中每个旧 cohort/canary 身份。选择前再次核对当前所有既有 cohort/canary 身份文件；若出现遗漏，先记录并修订方案，不能在看到候选内容或结果后替换个别任务。
3. 固定盐 `e1c-evaluation-2-independent-canary-2026-09-29`。对合格仓库以 `SHA256(UTF8(salt + "\0repo\0" + repo))` 升序，选前三个不同仓库；各仓库以 `SHA256(UTF8(salt + "\0task\0" + instance_id))` 升序选一题。相同摘要按原字符串字典序打破平局。仅身份满足条件时产生 3 个 primary；**本文件不计算或披露这三个 ID**。选择器、排除集合、源文件 SHA、身份输出须独立封存，且在查看 issue 前完成。

## 盲态门槛与停机

- 先固定完整生成器、定位器、候选静态审计、反馈分类器、模型配置与预算的代码/提示 SHA，并进行泄漏审计；目前只有上述选择**方案**冻结，完整方法冻结尚未完成。DEV 中两种产出来源须分别记账，不可混称单一模型命中率。
- canary 分母固定 3，不按镜像下载、官方 Base-Fail/Gold-Pass、可执行候选或结果后验替补。每题先核对权威镜像 digest、exact base、离线容器和官方准入；不满足则原位记环境/准入失败。生成只见公开 issue 与生产源码，测试/Gold 仅在独立 grader 使用。
- 可信复现需要两次同一补丁前故障、与公开 issue 一致、非环境/自造失败，且 grader-only Gold 消除该故障；**盲态至少 2/3** 才可讨论下一阶段。若前两题使理论上限低于 2/3，即停止；不得从该批结果反向调参后仍称独立。
- 未过门槛：封存负结果，回到既有 DEV 开发新通用方法，再预注册另一批完全不重叠的 canary。过门槛：先报告，不自动开启付费修复、sealed TEST 或 Fresh30；这些需另行冻结协议与精确命令。

截至本方案冻结：canary 身份 **未选择**，任务正文 **未打开**，provider 调用 **0**，盲态成绩 **无**。
