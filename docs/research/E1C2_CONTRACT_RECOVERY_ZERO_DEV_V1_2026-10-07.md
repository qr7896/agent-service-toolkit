# 原V4 first-probe 零调用合同恢复

本轮只读旧DEV已封存三个仓库的原V4输出，按原manifest每题第一份probe，**不按Gold/成功筛选、不补新的模型角色、不重跑旧namespace**。provider0/tokens0，原所有freeze/state/ledger/response/source保持不变。新`contract-recovery-zero-dev-v1`另立一次freeze/state/generation seal；完成producer后才允许独立Gold区分，评分不反馈给生成或编译。

唯一新兼容：value_relation的assertion字段若为单一Compare表达式，将同一predicate包成Assert。数字/变量/运算符/quote不改，predicate AST SHA恒等；已有Assert不改，多表达式/裸True/调用/同式比较仍拒绝。**原无Assert程序与新Assert程序不等价**，这属于新合同语法解释，不能回填旧invalid合同为成功。之后复用既有source-proven unsupported-constructor-keyword前沿，检查setup+完整target_action AST恒等、oracle/quotes/control_action不改，不人工选源码/修输入。

同时只审计自己的生成control trace，要求probe SHA一致、frame为/e1c2_probe.py并对应顶层AST，分setup/control_action/controller_check，未知留unknown。原件已经显示MM首次ISO +00:00失败在control_action，不在setup；不能用“移动setup故障”的猜测给它造正常日期。pytest自然语言CLI动作不自动转为代码或解除native fixture禁止。SK的表达式语法可兼容、构造前沿有生产证据；它是否可运行及Gold区分必须实际执行，语义忠实程度仍单列。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_recovery_zero zero
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_recovery_zero gold
```

两个命令是零模型，Docker/image健康才运行；已经开始则不自动重跑。使用原readonly/network-none/pull-never执行器、两次正控制通过才target、timeout/identity/transport停。3题screen、原DEV分母12，得到候选/Gold区分也只是**缓存合同恢复**，不是新生成、独立canary或修复率，机器trusted=false。保持TEST/C5/Fresh30/private Test500/Agent repair/E2关闭。控制器合成单测通过不表示方法已可支持所有任务；native generated fixture仍待实现。
