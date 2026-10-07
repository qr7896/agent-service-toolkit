# 零调用缓存v2：生产格式见证的正常对照

沿用[v1 first-probe缓存/语法/前沿协议](E1C2_CONTRACT_RECOVERY_ZERO_DEV_V1_2026-10-07.md)，旧V4同三题同第一份probe，原target输入/源码/quote/预期不变。新方法只替换call_completes的control_action：从已选定且SHA验证的生产文件中收集stdlib datetime.datetime.strptime的静态完整日期时间格式，按source path/line排序；目标单一literal日期字符串经stdlib解析，按首个不同的生产格式表达为正常输入，再调用同一个target API。没有repo/task ID分支、手填日期、人工定位文件、Gold生成反馈；不知道receiver/格式/单一literal就保持unknown，不转换自然语言CLI或解除native guard。

源格式仅是candidate依据，**没有证明它是实际target绑定格式，也没有证明对照与目标时间语义等价**；时区/表示可不同。controller要原样运行此control两次，失败不产生候选，成功后才运行未改target，再独立Gold区分。原问题要求的目标输入和oracle不变；control改变是显式新方法身份，不假称v1同literal对照或旧实验已成功。仅用生产格式推导正常baseline，不修改生产源码、测试答案或Gold。

v1缓存合同恢复已经真实1重复失败候选/Gold1区分，provider0；这不是新模型、独立canary/repair或语义自动证明。v2另立`contract-recovery-zero-dev-v2`、producer freeze/state/generation seal，来源v4所有原件与v1不改。先专项、再一次zero，seal后才独立gold；最终报告cached candidate/control/Gold/semantic分开，screen3/原DEV12分母不换，无best-of合并。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_recovery_zero_v2 zero
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_recovery_zero_v2 gold
```

均零provider/tokens。readonly/network-none/pull-never、正常控制两次、现有静态安全、transport/identity/timeout停、已开始目录不能重跑。增加独立Gold评分只评已选旧DEV候选，不允许用结果再调本次control。尚未冻新paid方法、全旧DEV/四参考、独立canary≥2/3均未过gate；TEST/C5/Fresh30/private Test500/Agent repair/E2继续关闭。生产selected-file格式发现不是通用API语义证明，必须在全版及未见任务验证，不能把两个旧样本适配说成30/30。
