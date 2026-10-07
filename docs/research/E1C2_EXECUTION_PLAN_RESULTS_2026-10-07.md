# E1-C evaluation_2：执行链修复与四参考4/4

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run / analysis
- Origin Date: 2026-10-07
- Verification Status: ANALYZED（执行链、账本、seal与独立评分核对；语义忠实性未验证）
- Version Label: execution-plan-hook-grounding-results-v1

## 1. 本轮结果

**新冻结版本四参考Gold区分4/4；机器可信复现仍0，E1-C尚未封板。** 原固定DEV12、九准入、四参考screen分别记账，不是完整DEV或独立成绩，不是Agent patch/official resolved，也不能报30/30。

精确命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_execution_plan_dev_v2 run`。工作目录`D:\codex\working\project20260827`，completed/exit0；之后producer seal完整核对，独立执行同模块`gold`，attempted4、区分4。

模型仅deepseek-flash，non-thinking、temperature0、retry0。上限50,000/题24,000/output2,000/最多16请求，**实际4请求11,909 provider tokens**；没有Pro或请求重试。本轮只一个付费版本；零费v1未调用模型。10月5日起可见725,352 tokens，未核账单且不是整个项目总用量。

| 旧DEV参考 | 新生成 | 独立Gold | 不可省略的边界 |
|---|---|---|---|
| scikit-learn-13496 | 正常配置通过；目标constructor参数两次异常 | 区分 | API入口义务已实际执行；语义trusted仍未授予 |
| scikit-learn-26289 | 正常配置通过；array目标两次参数校验错误 | 区分 | 未观察到公开报告的guard报错位置；期待引用是trace，不是desired behavior |
| marshmallow-1252 | 正常配置通过；目标两次ValidationError | 区分 | 生产格式control派生仍是既有机制，语义等价未证明 |
| marshmallow-1359 | 独立普通Schema配置通过；故障Schema两次AttributeError | 区分 | 新模型生成了有效normal配置，不是人工替换control；仍无自动语义证书 |

此前兼容版2/4不回填。新生成、计划反馈、执行接线一同改变，不能将4/4硬归因于某一个组件，也不best-of合并。

## 2. 找到并修复的真实根因

外层adapter只改`loop.execute_probe`，但paid runner内部再次进入`compiled.configured()`，把它重置成compiled所有者的ready-only执行器。零调用重现outer=true/inner=false；旧obligation、observed-type、unified-codec三个付费目录虽然有executed候选，API义务/类型观测产物仍0。此前“API gate/类型观测已经在付费链路生效”的解释不成立，源码与preflight声明不是执行证书。原分数、负结果、原文件完整保留；修正解释，不重写结果。

v2仅同时绑定compiled执行器所有者，以捕获delegate链避免递归；inner context和异常退出恢复均有回归。此前零费v1源码/smoke/audit保留，新v2 namespace与protocol另冻，不覆盖旧方法。

实际零费重执行上一封存批全部5份probe（不按Gold选择、不改响应/输入、不是新feedback-conditioned生成）：API义务、uncertainty、plan **5/5**产生；一项自身类型记录及公开source-bound implicit-operation hypothesis plan真正出现；两份无效control有正常配置计划。Gold读取0，不新评分或拼成绩。两个仓库synthetic真实正常control都过，passing target不选bug。

本次paid每题都出现API义务/uncertainty/plan，4/4；没有type-observer记录是因为四个目标都直接失败，适用条件未触发。不能称“类型观测造成4/4”。入口grammar有限、unknown不获证书；计划组件不改程序，既有compiler仍会派生control/移setup前沿，不能声称整个Controller从不转换代码。

## 3. Gold全过以后仍须完成的门槛

新增任务无关、零执行`witness_grounding_audit`，逐项审当前四候选，不使用Gold挑结果：

- 1/4期待引用是运行trace；trace/可执行片段不能直接证明期待行为。其余3项仅“未分类待语义证据”，不是自动通过。
- 同一项公开失败guard没有出现在两个实际失败trace中；标记not_observed，不声称该guard全局不可达或故障毫无关联。
- matching site、正常control、重复失败、Gold消除任一组合都不自动证明行为忠实性；machine trusted0保持。

因此只有**四参考Gold数值门槛**通过，语义门槛仍未通过；本轮停止付费扩批，不开第6canary/TEST/Fresh30/repair/E2。

下一轮具体顺序：①期待引用角色检查接在oracle lock前，trace/code-only标未知并要求公开自然语言/明确接口义务依据，不捏造期待；②生产调用链与实际失败位置对照，对提前参数校验失败给出“API义务候选/原故障机制未证”的双标签，不把位置不同一律当失败或通过；③跨仓库正负例证明既有有效候选不丢、错误期待不晋升；④另冻一次同四参考新生成，明确Gold与语义两个分母；⑤两门槛过后同版完整九准入、有限native harness，再新不重叠canary≥2/3；⑥Agent写patch/独立official评分、同版DEV30，最后另授权Fresh30 one-shot。不能保证一周或30/30完美。

## 4. 产物、工程验证与保全

- [公开收据](../../data/e1c_evaluation_2_execution_plan_results.json)：freeze/state/ledger/seal、每项Gold、真实hook文件、零费链/诊断/工程XML的SHA；raw/probe源码/Gold/test/key不上Git。
- paid身份`execution-plan-reference-dev-v2`，代码先提交`0c986a5`，freeze SHA`e676d9f37075c54fd8f47d9f16dae28ea21346a777a67e649a19af65b6dfe43e`。
- 最终单次完整回归**1402 passed、4 skipped、33 warnings，60.81秒**；Ruff、规定预算/V3重点与compact preflight ready=true。工程数不是修复率，无断言/skip/timeout削弱。
- `.codex/e1c/evaluation_2/`中的v1/v2 smoke/audit、v2 freeze/run/seal/Gold已开始或封存，全部禁止重跑；新方法必须新namespace。
- 未下载删除或重启Docker，未动IPC/VHD/registry/proxy/tunnel/密钥，所有旧文件/备份/负结果保留。当前无下载需求。
- WebCodex可接源码/无模型单测；本机private evidence/source/images/runtime不会随Git上传。旧bridge白名单不扩，不假称新模块云端端到端已验，缺材料报INFRA_BLOCKED。
