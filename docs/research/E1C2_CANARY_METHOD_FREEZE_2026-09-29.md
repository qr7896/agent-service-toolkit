# E1-C evaluation_2 独立 canary 方法冻结

状态：待 `freeze-method` 写入代码与本文件摘要，之后才按既有预注册盐选择任务。本文是方法协议，不含任何 canary 任务 ID、正文、Gold 或结果；选题后不得因结果改规则并保留“独立”标签。

## 固定机制

1. 固定三条不同仓库、无结果替补的 primary canary。选择依 `E1C_EVALUATION_2_CANARY_PREREG_2026-09-29.md`：先核验元数据池与旧污染/DEV12 摘要，再扫描现有 cohort/canary 身份，按盐对仓库和题目分别排序；在读取题目正文前输出身份及排除源摘要。
2. 每题先取得官方冻结 `task.yaml` 元数据与官方镜像 manifest 摘要，确认本地镜像 digest、exact-base 源码及离线容器可用。镜像、源码或官方准入失败时原位记环境/准入失败，不替换题目。官方测试、Gold、评分日志只放 grader-only 路径；生成侧仅可见公开 `problem_statement.md` 和冻结 base 的生产源码。内容须与官方冻结 Git blob SHA 一致。
3. 定位统一使用 `freeze_input(..., balanced=True)` 的结构/词法交错窗口与 v4 精确 CLI 选项加权；每题最多四个生产源码窗口、24,000 字符 issue/source 上下文。禁用测试目录、Gold/评分材料和任务 ID 的模型输入。若无候选生产窗口，原位记失败，不补人工路径。
4. 生成路由固定为 `e1c_evaluation_2_unified_dev_v1.route`：公开 issue 中唯一明确的布尔构造参数请求走零模型确定性规则；其余任务用 `e1c_evaluation_2_unified_dev_v2.prompt` 向 `deepseek-flash` 非 thinking、temperature 0 请求一次可执行 Python probe。模型仅可根据 issue 推定行为，并用生产 API 构造最小合法 fixture；不能自造结果、警告或异常。无充分公开行为 oracle 时弃答。无反馈回合、无同题重试、无人工选文件。
5. 固定 `validate_candidate` 的 AST/导入/泄漏审计。通过者在已验镜像内以 `--network none --pull=never`、exact-base、无新权限运行；若出现非 setup 失败，再运行同一 probe 第二次并比较日志 SHA。公开 issue 明言缺失、且生产窗口有对应 import 的可选依赖，才使用任务无关的隔离导入阻断。任何 setup、超时、base 通过、不同日志或未执行候选都记失败。
6. 对重复 base 失败只在 grader-only 环境应用官方 Gold 补丁并运行**同一 probe**。仅当补丁已应用、Gold 退出 0，且失败行为与公开 issue 语义一致、非自造 fixture/环境错误，才计可信复现。语义裁定按候选源码、公开 issue 与 base 错误检查；有歧义一律不计。Gold/测试不得用于修改候选、提示、定位或重跑本批。保持生成阶段候选、Gold 区分和最终可信三层分账。
7. 固定分母 3，至少 2 个可信复现才过 canary 门槛；前两项使最高可能成绩小于 2/3 时可提前停机，余项记未运行而非删分母。过门槛只允许另立、另冻结修复实验，不将复现率称为 patch success。未过则封存负结果，回旧 DEV 改通用方法；这三题不得再次充当独立 canary。

## 付费预算与停机

- 模型 `deepseek-flash`；最多每题 1 请求、整批 3 请求，SDK 重试 0；单请求最多输出 2,600 tokens。
- 单题 provider tokens 硬上限 14,000；整批硬上限 42,000。预估预留沿用现有 `estimate_tokens × 1.4 + 2,600`，若某题超上限则该题在调用前原位记预算准入失败，不提升上限或换题。整批实际 token 以 provider ledger 为准。
- 镜像/元数据网络只用于获取公开基准基础设施；真实 probe 与官方评分容器禁网。绝不访问生产系统、测试漏洞利用或打开 sealed TEST/Fresh30。
- 真正发送模型请求前还须核验全部代码/提示摘要、精确 live 命令与用户授权；中断不自动重试，也不覆盖原账本。

证据强度边界：DEV 上 3/12 可信只支持可行性，不预测 canary ≥2/3；canary 失败不能靠在本批改规则“修好”后仍宣称盲态通过。
