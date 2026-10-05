# 旧DEV source-contract零模型回放

此回放使用已完成的contract-ab-dev-v2两臂全部九条缓存输出，不重新请求模型。固定DEV12分母，另外三条官方准入失败仍计分母；不是新独立任务、不是新版付费生成效果。

先冻缓存响应/原freeze/state、新代码/协议、同一issue-only输入/镜像。控制器仅从候选窗口对应的已验生产文件恢复可选依赖import证据；明确公开issue声明缺包时按该module隔离，避免窗口重排丢前提。任何额外生产元数据读保留source SHA与行号，未进入生成模型。

第二条规则仅对setup中的直接导入构造调用生效：生产AST签名唯一且不接受某keyword时，将该构造及后续setup语句移到目标阶段。原setup+target的AST必须完全一致，expected_quote/oracle/断言不改，control_action不改。它区分正常fixture和报告中的目标构造失败，没有task ID特例。其他模糊签名、**kwargs或基线调用本身不合法仍拒绝，不补造control。

两次正对照须通过才运行B目标；两次目标失败锁定后独立Gold评分。不读取测试答案/Gold生成probe，不修当前canary、不改变旧A/B分数。新产物`source-contract-replay-dev-v1/A,B`与旧输出分离，provider_calls=0。比较按同一缓存源逐题列状态，保留失败，不能汇总best-of。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_source_contract_replay preflight --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_source_contract_replay preflight --arm B
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_source_contract_replay run --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_source_contract_replay run --arm B
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_source_contract_replay gold --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_source_contract_replay gold --arm B
```

即使回放有改进，也只能证明DEV控制器修订对缓存输出有作用；新模型一口气生成及新任务泛化仍待另冻验证。两批canary、sealed TEST/C5/Fresh30仍封存/关闭。
