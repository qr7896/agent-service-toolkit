# E1-C evaluation_2：报告锚4/4与运行时异常对应

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run / analysis
- Origin Date: 2026-10-07
- Verification Status: ANALYZED（账本/seal/独立评分与源码身份、异常观察核对；语义可信性未认证）
- Version Label: report-anchors-and-exception-observation-results-v1

## 1. 本轮结论

新报告锚版本 **Gold区分4/4**，并实际执行了公开A/B双接口对照；零模型异常观察在 **3/4** 取得公共异常或缺失接口参数对应证据。两者不是同一指标，**machine trusted仍0，不是修复率/完整DEV/独立成绩/30题全过**，E1-C未封板。

精确命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_report_anchor_dev run`；目录`D:\codex\working\project20260827`，completed/exit0，producer seal完整核对后独立`gold`，attempted4/区分4。仅deepseek-flash/non-thinking/temperature0/retry0；上限50,000/题24,000/output2,000/≤16请求，实际 **6请求21,400 provider tokens**。本轮只有一个paid版本，无Pro/请求重试/追加采样；10月5日起可见777,229 tokens，非账单核验，非整个项目总账。

原固定12/九准入/screen4分账。前版严格期待3/4保留；新协议明确允许公开比较/回归支持“完成假设”，口径不同，不能将恢复4/4称为严格前版过关。新数据包、连贯提示与假设准入一起改变，不声称单因素因果，也不best-of合并。

## 2. 逐项证据

| 旧DEV参考 | 生成/独立Gold | 期待来源 | 零模型异常观察 |
|---|---|---|---|
| scikit-learn-13496 | turn2，区分 | 明确接口请求 | 1条缺失constructor keyword对应记录 |
| scikit-learn-26289 | turn1，区分；normal A与target B实际源绑定/共享参数对照 | 公共比较报告的完成假设 | 0条对应；实际参数校验失败，原报guard机制仍未证 |
| marshmallow-1252 | turn1，区分 | 公共回归报告的完成假设 | 2条公共parser消息对应记录；保留缺dateutil环境 |
| marshmallow-1359 | turn2，区分 | 公共回归报告的完成假设 | 5条公共AttributeError消息对应记录 |

2/5记录是同一个异常在不同帧传播，不是额外成功任务。0条是受限观察未找到对应，不是全局无异常/无关证明。期待假设不是原报告明说的保证，也不是report-exact输入；same-expression并不证明任意对象/状态的实际值等价。

## 3. 实质机制

**公共报告锚**：复用精确catalogue ID和有限constructor/works-for比较语法，另将previous/earlier/used-to/before/<=与work/without-raising的prose共现标作有限回归报告。明确请求、比较、回归与unknown分账；trace/code不给锚，未知不自动可信。初始Human新增来源标签，原字段/原文不改；拒绝反馈仍附已识别比较事实，不因bad quote拒绝丢掉结构化关系。System和下一turn同步修订，七字段DTO、bad quote在lock前拒、source/控制/目标/预算保持，Controller不改模型程序或期待。旧九响应与四输入零调用全审，四输入各一个锚，原字段保持；真实两repo synthetic正常control通过。

**受限运行时异常观察**：复用已验证probe/image/base/nonce/超时/只读无网络的执行传输，新controller-owned固定driver监听实际Python exception事件。只处理四种精确builtin exception身份和单str参数；只输出公共消息SHA匹配/已声明缺失keyword匹配、源位置，不输出原始消息或输入值。限两生产文件/八条记录，其他类型未知；不调用模型repr/getattr/自定义异常字符串化，不伪造driver的model safe_static_check，不接入paid生成或给予trust verdict。

observer v1首题在source SHA前置核验中断，尚未执行模型probe，失败freeze/driver/log完整保留，未重试。只读核验确认两个容器文件都等于相应Git base blob；本机暴露副本CRLF、容器LF，投影LF摘要完全相同。不是跳过source guard，也不修改原副本。另版v2双摘要（原暴露摘要＋LF有效摘要），在容器同时验证有效文件与Git canonical blob，任何非换行实际变化仍拒绝；修正旧Python不支持str.removeprefix的问题。v2独立namespace跑四probe，无模型/Gold读取，optional import blocker照原环境挂载，均rc1（原故障复现，不是infra失败）。

观察器改变执行filename/instrumentation/timing，未证明全面语义等价；nonce和匹配日志不是抵抗任意恶意Python程序的安全证明。源帧与异常对应也不自动证明用户意图、输入合法性或全部issue义务；因此3/4对应不能包装可信3/4。

## 4. 下一步门槛与停止条件

不再付费调提示追回数字。本轮四参考数值gate已过，下一步先零模型合并**公开输入约束、production调用/alias绑定、期待来源、真实异常对应**，明确支持的证书范围与unknown。反例至少包括：同消息但错误fixture、import/alias影射、生产对象被修改、参数/shape偏离公共约束、仅API兼容而未达原报机制、观察时环境/源码变化。只做字符串匹配或Gold消除不够。

分类器校准与跨repo反例通过后，把observer/双源码身份纳入完整方法freeze，做同版四参考/九准入DEV（保留固定12分母）；行为与机制两个scope分别评分。只有可信/行为gate真正达成，才预注册全历史排除的新canary一次≥2/3，再Agent patch/独立official grade、同版DEV30，最后另授权Fresh30 one-shot。当前不抽第6canary、不做repair/E2、不承诺一周/30题完美。

## 5. 工程与保全

- 最终完整回归 **1436 passed、4 skipped、33 warnings，104.66秒**；Ruff/规定预算V3重点/compact preflight ready=true。未弱化assertion/timeout/skip，不当repair rate。
- [公开收据](../../data/e1c_evaluation_2_report_anchor_results.json)绑定freeze/state/ledger/seal、Gold、真实锚/对照/grounding、异常v1失败与v2观察、source projection和XML；raw/probe/Gold/test/key不上Git。
- paid代码先提交`e220a87`，freeze SHA`ce751cec630abc95601048a30a522cfc13daf0f9898c9b753cdd7c28860d7b51`。所有已started run/smoke/audit/Gold禁止重跑或改旧源，observer v1/v2各自保留。
- 本轮未下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key更改，当前无下载需求。TEST/C5/Fresh30/private Test500/repair/E2未开，旧备份和历史全保留。
- WebCodex可接源码/无模型单测，缺本机private evidence/source/images/runtime报INFRA_BLOCKED；旧bridge白名单不扩，不假称新paid端到端云接线已验。
