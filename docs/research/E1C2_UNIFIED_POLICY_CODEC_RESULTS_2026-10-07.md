# E1-C evaluation_2：单一政策与接口兼容实验

后续接线更正：旧runner内部配置覆盖外层API/类型executor，不能把preflight声明当实际gate证书；本页原2/4/接口负结果不变。另版已修复并得到四参考Gold4/4，但语义门槛仍未通过，见[新结果与真实hook证据](E1C2_EXECUTION_PLAN_RESULTS_2026-10-07.md)。

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run / analysis
- Origin Date: 2026-10-07
- Verification Status: ANALYZED（账本、seal与独立评分已核对；语义可信性未验证）
- Version Label: unified-policy-codec-dev-results-v1

## 1. 结论

接口回归已修复，但复现质量未提升到开发门槛。两个新版本分别保留负结果，不取最好结果拼分：

| 冻结版本 | Flash实际调用 / tokens | 独立Gold判别 | 解释 |
|---|---|---|---|
| unified-policy-reference-dev-v1 | 9 / 25,928 | attempted 0，screen 0/4 | 平铺七字段动作与旧解析器不兼容；没有有效实验候选，不是四题软件修复失败 |
| unified-codec-reference-dev-v1 | 6 / 18,038 | attempted 2，区分 2/4 | 严格形状兼容后真正进入执行；另两题仍未通过 |

合计15请求、43,966 provider tokens；每个实验上限50,000，模型仅`deepseek-flash`、non-thinking、temperature 0、retry 0。本轮没有Pro、请求自动重试或第三个付费批次。自10月5日起可见记录累计713,443 tokens，包含历史错误请求，**未核对账单且不是整个项目总用量**。

screen分母4；原DEV固定分母12、九题准入；这不是完整DEV12实验。机器可信复现0，未写Agent补丁，没有official resolved成绩；工程测试不计为修复率。

## 2. 本次实质改动与证据

1. 将叠加System由5060字符整理为单一2863字符政策，公开Human输入保持原样。区分未知期待（不能捏造）与未知输入类型（允许显式假设，但不能叫原报告事实）；正常control必须验证，不凭提示授予可信性。
2. 第一轮9份真实响应使用完整ref字段的已知平铺selector，被原解析器拒绝。新版本只接受三种精确fieldset，再走原严格引用、源码、控制与目标门槛；未知/多字段/缺字段不猜测。
3. 零调用审计9/9解码，五个代码/oracle字符串逐字段不变。只改变DTO包装，不替模型选择文件、修正数值、类型、期待或程序。
4. 修订版加明确canonical JSON示例；它与codec兼容一同修改，**不是单因素因果实验**。两个真实仓库的正常对照合成smoke通过，不能算任务成绩。
5. 新`contrast_audit`只做静态诊断：control/target动作AST相同，以及裸Name条件涉及Python truth-testing协议。不执行表达式、不推断runtime type、不生成输入、不读取Gold。新批六响应中两份同动作control被标记；这不是两条可信故障，更不是状态独立性证明。

同动作在不同运行状态下也可能合理，诊断建议不是自动拒绝证书。不同AST也不证明控制独立；生产源码没有显式`raise`不代表隐式`__bool__`/`__len__`不会抛错。下一版须通过真实隔离执行与源码绑定核算这些关系，不能只加一句提示。

## 3. 修订版逐项结果

| 旧DEV参考 | 生成结果 | 独立Gold | 剩余原因 |
|---|---|---|---|
| scikit-learn-13496 | 正常control通过，目标两次constructor参数异常 | 区分 | 仍缺自动语义忠实性证书，不晋升machine trusted |
| scikit-learn-26289 | list输入目标通过；下一步弃答 | 未有候选 | 模型将当前输入通过推断成不存在支持的故障；缺source-consistent输入假设的可执行探索 |
| marshmallow-1252 | 正常control通过，目标两次日期ValidationError | 区分 | 仍缺自动行为对齐证书，不晋升machine trusted |
| marshmallow-1359 | 两轮control都落在同一故障Schema配置 | 不评分 | 重复control_failed停止；不是Gold修复失败 |

`repeatable_failure_candidate:false`与`repeatable_nonsetup_failure:true`是现有组件的不同标记，不改写为机器可信；独立评分仅依据既有严格验证与seal后的候选。

## 4. 可直接落地的下一步

1. **先零调用执行契约，不先抽新题。** 将新诊断与已有source SHA/入口义务/运行类型观测结合，产出一份可执行候选计划：公开约束、模型输入假设、正常配置、目标动作、未证项分栏；不能自动填某题日期、数组或断言。
2. **验证正常控制与目标状态。** 同动作须提供状态差异证据；不同动作仍须正常配置两次通过、独立进程/状态与目标API对应。fixture本身失败时不进入目标/Gold，未知不获证书。
3. **有限探索隐式协议。** 根据公开失败条件和生产AST识别操作需求，模型提出API-valid假设，自身执行反馈验证；只能称合成假设，不称原报告exact输入。设置有限动作数、无重复无效动作、无provider重试；不是手选题型输入。
4. **先做跨仓库零调用正负例。** 有效normal control、同故障假control、共享setup故障、真实类型与模型声称冲突、未知表达式/入口均覆盖。诊断helper尚未接live，不能宣称改进有效。
5. **另立版本冻结后再一次旧四参考screen。** 原两个已started namespace全部禁止重跑。预算仍须逐实验明确≤100,000；质量与忠实性门槛通过后才同版完整九准入DEV，失败继续保留固定12分母。
6. **再做独立验证与修复。** 完整方法先冻结、历史身份全排除的新canary预注册一次、可信复现≥2/3并行为一致；失败封存回DEV。通过才冻结Agent补丁/官方评分，同版DEV30，最后另授权Fresh30 one-shot。五批旧canary结果不改、不重称独立。

不承诺30/30或一周完美。本次付费screen已经给出负证据，继续无机制验证的重采样不构成研究进展。

## 5. 验证、保全与WebCodex接手

- 完整回归1388 passed、4 skipped、33 warnings，93.81秒；Ruff、预算/V3重点及规定compact preflight ready=true。没有降低断言、扩大timeout或新增skip。
- [公开机器收据](../../data/e1c_evaluation_2_unified_policy_codec_results.json)绑定两个freeze/state/ledger/seal、Gold结果、零调用审计与工程XML；候选源码、raw响应、Gold/test/key不上传。
- 代码提交先于paid：single-policy `f06fda7`、codec `86dbefc`。freeze分别`b8c5d2281a58988c784528bc741b82a6b7991484a7882aa79cbc5e2622a47447`、`672dd2504b2f55357473b3eab69b4dd32d1b0ba2d51f095254c7f041ab1b9a0b`。
- `.codex/e1c/evaluation_2/`中上述run/smoke/audit/Gold都已开始或封存，不能“继续”命令重跑；下一轮必须新namespace，不修改已冻结源或账本。
- 本轮未下载/删除镜像，未重启Docker、改IPC/VHD/registry/proxy/tunnel/密钥，全部旧记录和备份保留。没有新下载需求。
- WebCodex可接源码与无模型单测；运行本机实验必须具备exact-base生产源、私有原始证据与Docker执行器。缺少材料报`INFRA_BLOCKED`；本机bridge旧白名单未扩，不宣称新paid入口已云端端到端验证，不暴露Docker daemon。
- sealed TEST、C5、Fresh30、SERBench private Test500、Agent repair和E2仍未开放。
