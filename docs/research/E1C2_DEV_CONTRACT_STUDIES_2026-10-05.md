# DEV 行为合同研究：结果、成本与下一门槛

## Material Passport

日期2026-10-05；项目project20260827；mode=run；来源：本机冻结输入、响应、provider ledger、离线base/Gold结果。固定DEV12：官方双准入9/12，另3题仍占分母。结果是补丁前复现，不是Agent repair。未打开sealed TEST/C5/Fresh30。未上传Gold、测试正文、凭证或本机原始响应。

## 实验结果

| 单独身份 | 请求/实际tokens | Gold区分 / 固定12 | 解释 |
|---|---|---|---|
| contract-ab-dev-v1 A | 9 / 19,256 | 3/12 | 原source生成格式；完成9条 |
| contract-ab-dev-v1 B | 8开始、7完成 / 16,344完成usage + 4,281错误携带usage | 1/12，部分评分 | 第8条SDK JSON解析LengthFinishReasonError中断；第9条未调用；不自动重试，不作完整A/B比较 |
| contract-ab-dev-v2 A | 9 / 17,545 | 1/12 | 自动生产窗口统一重整后的新身份 |
| contract-ab-dev-v2 B | 9 / 19,253 | 1/12 | raw JSON计量保存截断；无SDK解析中断；与A成功任务不同 |
| source-contract-replay-dev-v1 A/B | 0新增调用 | 各2/12 | v2原响应零调用回放；完整生产import与构造目标重分期；开发证据 |
| hybrid-dev-v1 新生成 | 15 / 29,864 | 3/12 | B优先、只按评分前base失败决定A回退；缺日期基线，原preservation gate未过 |
| hybrid-oracle-replay-dev-v1 | 0新增调用 | 4/12 | 新controller v2贯穿原合同到A，缓存开发证据；不可改称新付费/独立结果 |

新controller缓存可信4/12包括人工issue语义审核，底层机器`trusted_reproducer=false`保持不变。四条为scikit-learn-13496/26289、Marshmallow-1252/1359，跨两个仓库。历史v4也有4/12（8请求/25,424tokens），因此当前不证明优于历史v4；不同输入/方法/时间且存在缓存，不作因果或显著性结论。未拼接版本best-of，也未按Gold重选候选。

## 实质改进与限制

1. **自动生产覆盖**：过滤docs/bench、区分公开类构造与泛化`__init__`，按公开API/traceback线索选四个exact-base窗口，无任务ID→文件映射。提升覆盖仍未证明普遍定位正确。
2. **响应完整性**：用已有SDK raw响应保存截断/usage/模型alias，解析拒绝与provider失败分账；原SDK失败不回填、不重试。
3. **源合同**：从选中生产文件的真实import证明缺可选包前提；AST签名证明目标构造不应放在fixture阶段，重分期保持目标程序AST不变。不是任务专用fixture表。
4. **评分前控制器**：正对照两次成功后执行目标；第一个稳定base失败即STOP，之后才Gold，不看Gold挑A/B。
5. **oracle一致性**：A回退不应擅自增加原call_completes合同未要求的返回值断言；严格结构可证明时保留API程序，仅编译到达检查。value_relation不降级。该改动在DEV上形成，必须由新canary验证，不以语法检查冒充语义证明。

pytest类CLI行为仍受禁止子进程/任务上下文不足制约；复杂数值/跨模块行为与fixture不可靠仍为瓶颈。不能为30/30逐题添加公开断言或特例。尚未生成Agent补丁，新独立门槛未过，不能宣称“完美”。

## 成本与证据

本组DEV累计50请求开始、49完成、1次SDK处理失败：已完成usage **102,262 tokens**，加错误所带4,281可见usage为 **106,543**。错误usage不在原ledger完成事件中，是state.error独立补记，不等同已核账单。各单独冻结实验均未超过其90,000/100,000上限，无自动重试。加本日canary v2的13,783为 **120,326可见tokens**；不把这个累计冒充单实验用量，系列预算不是无限额度。

原始证据均留`.codex/e1c/evaluation_2/`，子目录与表中身份同名；未提交到GitHub。provider ledger SHA依次：

| 目录 | SHA256 |
|---|---|
| contract-ab-dev-v1/A | a87ec8f896a800ba860098f3fc7d31779712de27c19ce7c903b24836e2f0f253 |
| contract-ab-dev-v1/B | 6872e4c63dfd0059621abfd70222e06b3ca21665923937ea993e456a794d6ee0 |
| contract-ab-dev-v2/A | e9c76acc1694f5ae3afb210d204fc1923516666d4108f4043a45fed24b344a70 |
| contract-ab-dev-v2/B | 8cd67eaaddcdd994d926eb7752b04235f26b415a957873dff663ee5ce078aa96 |
| hybrid-dev-v1 | 4ff6d2ff1b9bce026d3679d1805df6b8c48d435bfd161852043b9c4ec500033d |

开发门槛与源证据hash另见[data gate](../../data/e1c_evaluation_2_hybrid_controller_v2_dev_gate.json)。原来v1/v2/hybrid-v1冻结身份、负结果、状态和失败response均未删除或重写。

### canary v2模型记录更正（不改 sealed 原件）

先前公共结果标`returned_model_identifier_recorded=false`表述过宽。重新核查原完成ledger，存在`response_model=deepseek-flash`，因此**记录了返回alias，未记录可独立验证的不可变版本snapshot**。此处追加更正，原sealed公共JSON和本机final_result不覆写；0/3结果不变。

## 下一步

新的[hybrid canary v3协议](E1C2_HYBRID_CANARY_V3_METHOD_2026-10-05.md)在选题前冻结；3题身份只看metadata，排除旧DEV/两批canary/历史污染。官方及直连镜像站摘要已3/3匹配，只有26,299官方正文bytes/7请求，经授权7892；blob调用0。任务为Flask-5063、PyVista-4226、SymPy-17150。压缩4,575,379,722bytes≈4.261GiB，大文件用户直连下载；新canary provider calls=0、issue未打开。

先下载→官方离线Base/Gold双准入→公开输入→preflight；之后Flash最多6请求/60,000tokens，不重试。可信≥2/3才另冻修复配对实验，否则封存回DEV。下载命令与时长见[接手说明](NEXT_SESSION_HANDOFF.md)。工程回归单次1115 passed/4 skipped/33 warnings/0 failed，50.61秒；指定重点18 passed/Ruff通过，V3规定原preflight退出0。与上表复现效果不同口径。
