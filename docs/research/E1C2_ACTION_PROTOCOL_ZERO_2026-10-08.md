# 模板回显与封闭动作包装：零调用修复

2026-10-08，run mode，Verification Status UNVERIFIED（执行前），Origin Skill academic-research-suite / experiment-agent。

新80k/context批次完成16Flash调用后四任务无候选。已保存响应显示：三题各两probe将system JSON示例中的英文setup说明逐字照抄而不是Python，另题四回复type=json_object+action=dict未支持；新source acquisition未有机会执行。不是预算再次用尽，也不证明领域能力0。原paid/freeze/source/所有负输出保持。

新policy去掉全部probe代码字段示例值，改字段类型/真实生产Python要求；不提供task代码/预期答案，不把坏代码自行修成probe。decoder仅封闭外层{type:json_object,action:dict}且inner一个已知action时剥离transport metadata，其余不猜。原7字段/quote refs/schema依然由现decoder严格验证，新增ast.parse语法前置门槛；Oracle/执行/semantic gate不改。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_action_protocol
```

action-protocol-zero-v1源/协议/原seal先冻，对全部16个自身response只读syntax/包装审计，0provider/容器/Gold；原probe不执行、不重写。source测试与坏metadata/占位说明拒绝先过。通过不代表新模型不再回显；future必须protocol/messages/codec整体freeze和真实JSON smoke后再新DEV，不重跑本批，不开TEST/canary/Fresh30，不改Docker/镜像/代理/tunnel/key。
