## Material Passport

- Origin Skill: academic-research-suite / experiment-agent; ponytail（最小实现）
- Origin Mode: experiment design + local metadata/projection verification
- Origin Date: 2026-09-27
- Verification Status: DEV12 身份与公开题面投影已本地核验；候选失败分类器已实现并回归，但生成器/真实复现**尚未实现或运行**
- Version Label: e1c-reproducer-dev-next-v1

# E1-C 下一版 DEV：先复现、后修复

## 当前证据与决策

旧 DEV30 的显式异常契约只有 2/30 可编译；此前 setup-closure / EFIL 真实运行又遭遇环境和依赖错误。source-contract 虽在旧 DEV 上产生两仓库 witness，但最近独立 canary 的 Django/SymPy 均为零可执行候选，2/3 门槛不可达。故不再扩充相似正则或在该 canary 上调参；研究层切到**任务无关、有限候选的复现测试生成与执行反馈筛选**。这不是已经验证有效的新系统。

补充开发身份先于题面读取冻结在 [`data/e1c_reproducer_dev12_identity.json`](../../data/e1c_reproducer_dev12_identity.json)：12 题、4 仓库、每仓库 3 题，由冻结 SWE-bench 任务树元数据与固定 salted-hash 规则产生。12/12 YAML blob SHA 与冻结 revision 匹配；本机官方 test/dev parquet 中 12/12 有公开题面，现有 `project_issue` 12/12 可投影。这里的 SWE-bench 公开 `test` split 只是上游数据集名称，**不是本项目尚未打开的 Fresh30**；所选 12 题从此仅为 DEV，永久排除后续独立 canary 与 Fresh30。暂未做 official Base/Gold、exact-base image、模型调用或修复结果；不得把可投影计作可复现。

## 可借鉴但不能照搬的研究方法

- [Issue2Test](https://arxiv.org/abs/2503.16320) 将 issue 理解、候选测试生成、编译/运行反馈修正拆开，强调失败必须与问题描述一致。
- [e-Otter++（ICSE 2026）](https://arxiv.org/abs/2508.06365) 采用异质提示增加候选多样性，并把补丁前断言失败与语法/fixture 等非目标错误区分；其更昂贵的多候选补丁测试选择只作为后续可选消融，不直接复制。
- [SWE-Tester 2026](https://arxiv.org/abs/2601.13713) 显示专门训练的模型可以提高测试生成能力，但其模型、数据和 benchmark 指标与本项目不同，不能把论文成功率当作 E1-C 预期值。

## 预注册的最小开发实验（尚未启动）

1. **输入冻结**：只向复现生成器提供断言剥离后的公开自然语言 issue、自动定位所得 exact-base 生产源码短窗口及生产 API 签名；禁止 `test.patch`、Gold、官方失败断言、评分日志、测试源码、任务 ID 规则。每题同一固定输入/预算，不人工挑文件。
2. **有限候选**：每题最多两种固定、任务无关提示视角（行为期望 / API 使用），每视角一个候选。候选只能是独立的临时 probe，不可修改生产源码；AST 安全检查、长度/调用预算、来源哈希先于执行。
3. **执行反馈**：在 immutable official image、exact-base、`--network none` 下逐个运行。语法错误、导入/缺依赖、fixture/setup 错误、超时和无关异常单列，均**不计可信复现**；只有可归因于公开需求的断言/显式异常失败才进入候选。最多一次固定规则的 setup 修正，不能依据 benchmark 断言补测例。
4. **盲态判别**：候选失败必须附 issue 文本证据跨度、失败位置、可见生产调用与重复运行一致性；不能仅因 exit code 非零就认作复现。尚无法自动判明语义一致时保留 `uncertain`，不晋升为 `trusted`。可在 DEV 对判别方法做人工审计，但人工结果不进入运行时提示或独立成绩。
5. **开发门槛**：在固定 DEV12 分母上记录 attempted / safe / executable / issue-aligned / trusted；至少 **2 个不同仓库的新增 trusted prepatch reproducer**，每题重复两次一致，0 泄漏、0 身份异常、0 意外网络、专项回归通过。旧 DEV30 作为额外开发对照，分别报告新旧机制覆盖；不得与 DEV12 结果拼分母。未过门槛则不冻结新独立 canary。
6. **后续顺序**：DEV 门槛过关 → 冻结生成器/判别器/模型/预算/代码 SHA → 从未看内容且不重叠的 metadata-only pool 冻结新 canary → official Base/Gold 与盲态 preflight → 若 ≥2/3 trusted 再展示**精确付费命令**请求授权 → 配对实验 → 通过后才考虑同版 DEV30 和 Fresh30。旧 source-contract canary 不重试、不后验修补。

为节省额度，先实现并零模型验证输入门禁、执行分类和账本，再做 DEV12 中的**预冻结小规模**模型 pilot；扩至 12 题前必须按固定停止规则检查净新增。当前 strict-v5 runner 仍是零 provider skeleton，不能把历史非盲态 live runner 直接拿来充当上述实验入口。

第一项最小代码已落地：[`evals/e1c_reproducer_dev_feedback.py`](../../evals/e1c_reproducer_dev_feedback.py) 将超时、未执行、环境/收集错误、无补丁前失败、显式公开异常匹配、断言候选及无关失败分开；**任何单次失败都不会被自动提升为 trusted reproducer**。这只是反馈门禁，不是测试生成器或模型实验。新旧相关专项回归 8 passed、Ruff clean。
