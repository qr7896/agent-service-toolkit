# E1-C evaluation_2 第二批独立 canary：方法与预算预冻结

状态：本文件与方法代码的摘要先于第二批任务身份选择封存；不含第二批任务正文、Gold 或结果。上一批三题已封存为 1/3 的负结果，永久排除于本批独立样本之外。第二批只检验当前冻结机制，不能在见过结果后修订并仍称独立。

## 旧 DEV 根据与固定机制

在既有冻结 DEV12 中，统一 v4 Flash 方法对 9 条官方 Base/Gold 双准入任务运行：8 次模型请求、25,424 provider tokens，零自动重试。5 个候选两次同日志补丁前失败，grader-only Gold 对其中 4 个消除失败；公开 issue 语义核查后，4 个可信补丁前复现分属 scikit-learn 与 Marshmallow。新增加的 scikit-learn-26289 使用公开报告中的 NumPy 数组类型作为 `feature_names`，而非先前偏离问题的输入；其同一 probe 在 Gold 后通过。另两条 Marshmallow 的公开问题只要求 API 调用不抛异常，v4 用调用后到达标记而不是编造返回值或内部属性断言。此为开发集结果，不是独立泛化或修复率。先前 v3 试验保留，不用它的额外强断言作为晋升依据。

第二批统一沿用 `e1c_evaluation_2_unified_dev_v1.route`、v4 的公开 issue + exact-base 生产源码提示、v4 之前已冻结的自动源码窗口、原静态审计及离线执行器。明确布尔构造参数走任务无关确定性路由；其他题最多一次 `deepseek-flash` 非 thinking、temperature 0 请求，要求恰好一个 issue-grounded 行为断言；缺少明确可观测行为时弃答。生成侧不得读取任务 ID、官方测试、Gold 补丁或评分日志。候选在不可变官方等价镜像中 `--network none --pull=never` 执行；两次一致的补丁前失败只算候选。只有 grader-only 同一 probe 的 Gold 区分成功，且人工语义审核确认失败与公开 issue 一致、不是自造 fixture/额外断言，才计可信。语义有歧义一律不计。

仅使用冻结元数据池选题：盐 `e1c-evaluation-2-independent-canary-v2-2026-09-30`，先按 `sha256(salt + NUL + repo + NUL + repo_name)` 排三仓库，再各按 `sha256(salt + NUL + task + NUL + instance_id)` 选一题。排除冻结 DEV12、旧 canary、污染账本及所有扫描到的既有身份；不读候选题正文或结果后挑选。固定三题、三个仓库、无替补，包含环境/镜像/准入失败在内的固定分母 3。若有至少 2 个可信复现才过门槛；否则封存负结果，不运行新版 repair live 或 Fresh30，也不在这三题上补规则后重称独立。

## 传输、预算与停机

先从官方冻结 `task.yaml` 取得小型元数据，再要求 Docker Hub 官方与直连镜像站的顶层和 linux/amd64 manifest 摘要完全相同；镜像层按官方大小/SHA-256、解压 diff-id、导入后 image ID 逐层核对。不允许用相似镜像、跳过摘要或自动拉取替补。新下载脚本显式关闭 Python urllib 代理，并只请求 `docker.1panel.live` 的已核摘要层；Docker 导入通过本地 daemon，用户自行在终端执行大文件下载。**应用层绕过代理不能保证操作系统 VPN/TUN 不接管路由**；用户应在下载前关闭 VPN 全局/TUN 并核对网络出口。若官方 manifest 直连不可达，停止，不以非权威镜像站自证身份。

模型最多每题 1 请求、整批 3 请求，SDK 重试 0；单次输出最多 2,600 provider tokens。单题硬上限 14,000、整批硬上限 42,000；预留规则为估计提示 tokens ×1.4 再加输出上限。超预算、镜像错误、源码身份错误、官方 Base/Gold 不过，均原位记失败，不增预算、不换题。正式模型命令须在本地镜像/准入/公开输入完成后单独预检、核验冻结代码摘要再运行；中断不自动重试。sealed TEST、C5 和 Fresh30 保持关闭；修复实验只有第二批独立门槛过后另立协议。
