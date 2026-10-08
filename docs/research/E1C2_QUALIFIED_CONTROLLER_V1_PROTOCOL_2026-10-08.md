# Qualified Controller v1：旧 DEV 零调用接线协议

日期：2026-10-08。用途是把已有资格判别接到实际执行链，不是另一个旁路 collector，也不是已通过独立门槛的完整修复方法。

## 1. 材料与边界

- 仅复用旧 DEV 已核验的生产源码、公开 issue 投影、exact-base Git blob 与本地镜像；不下载、不读 Gold/原测试、不访问 sealed TEST/C5/Fresh30。
- 原 report-anchor 模块、namespace、probe、ledger、seal 和成绩保持不变。新 adapter 的 CLI 只有 `smoke` / `freeze`，不开放真实 provider run。
- 模型输入只补 NumPy-style Parameters 声明，不补 Examples、预期答案、评分日志或历史诊断结果。声明不能覆盖公开明确变更请求。
- 以已核验 base_commit 绑定 workspace，不建立 task-ID→文件规则。每次读取检查暴露源 SHA、LF 规范化后的 exact-base blob；单文件≤1 MB、至多8组声明/每定义8参数。

## 2. 实际执行链与有限覆盖

`verified inputs → messages/production parameter contracts → Controller policy → 原 compiler/oracle lock → normal×2/target×2 → bounded exception observer → qualification v2 → behavior gate → feedback`

在进入 compiler 前拒绝明确 alias 改写、生产对象修改、公开 fixture 变更、无唯一公开期待锚、非 completion oracle/非空 assertion。未暴露依赖仍 unknown，不伪称源被篡改。

原 compiler、正常控制、重复失败规则保持。只有原执行器选出 candidate 才观察；观察实际生成 probe，生产依赖最多两个文件，host/有效文件/Git blob 双身份绑定。`line=1` 是文件身份边界，不是定位到失败 guard 的声明。保存 admission、qualification、行为范围和未知项；完整 issue trusted 始终 false。受限候选可保留为 DEV 独立评分候选，但不能自动作为可信复现/repair 输入。

本版尚未自动接入 paired input、对象关系或历史版本 witness，也没有全动态依赖覆盖。旁路已有实证不回填当前候选。参数文档范围、normal API→target API 支持和子义务→整个 issue 推断均不得自动升级。

## 3. 零调用验收

11专项单测包含拒绝前执行阻断、源变更、mock delegate→observer→qualification→behavior、实际嵌套配置 hook、异常恢复和 synthetic issue 独立义务。mock 观察不算真实 runtime 证据。

真实容器 smoke 复用 sklearn/Marshmallow 两个已存在正常 API 示例。每例一个新的合成 regression issue，清空原 issue fixture obligations、更新 issue SHA；同一正常/目标调用，retrieve→probe→abstain。验证 inner Controller admission、两次正常控制、目标不被选作故障、post-execution verdict 和反馈消费。它只验证正例管道；不证明异常观察分支已在真实新生成 candidate 上执行，不计真实任务成绩。

精确命令（均 provider calls=0、tokens=0、无自动重试）：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_qualified_controller smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_qualified_controller freeze
```

新身份分别为 `.codex/e1c/evaluation_2/qualified-controller-zero-smoke-v1` 与 `qualified-controller-dev-v1`。已 started 不重跑，失败封存；协议/完整模块 SHA 先写入 smoke，freeze 必须确认 smoke gate 和源码未改变。协议冻结后不修改。

## 4. 预算与后续 gate

freeze 继承四参考 DEV 预算：模型候选 `deepseek-flash`，batch≤50,000 tokens、单任务≤24,000；实际任务/调用数以 preflight 的冻结 JSON 为准，本协议不授权运行旧模块 CLI 来绕过本版禁用。当前真实模型调用数为0。

只有完成剩余义务范围、缺证取得策略与真实 selected-candidate 异常分支验证，才能提出新的完整 producer。先列精确命令/Flash/调用数/≤100,000 tokens，在新未开始 namespace 上生成；独立 Gold 与语义资格分账。同版旧 DEV 门槛真正达成后才另冻结历史不重叠 canary。负 canary 封存，不在原批补规则后仍称独立；repair/official、旧 DEV30、Fresh30/E2 均尚未放行。不保证30/30或“一周完美”。
