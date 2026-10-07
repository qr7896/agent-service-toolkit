# 原文引用编号 DEV：实验前协议

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（本协议不回填实验成绩）
- Version Label: referenced-runtime-old-dev-v1

基于同日已封存compiled-runtime完整旧DEV实验，保持原12分母/九准入/四参考、不换题、不重跑旧命名空间。新方法只改变公开issue显示与引用解析：逐原始行、超长行按1400字符切段，保留每个字符与原offset/issue SHA；编号不按task/期望关键词或答案排序。生成器选择两个有效整数ID，Controller解析为原文，setup/control/target/oracle/assertion不变，然后运行同一编译器/控制/重复失败/独立Gold链。兼容原严格字符串引用，不模糊匹配或修改旧失效quote。原模型伪造的expected错误消息不能在评分后补成原文。

原文ID只能证明来源，不能证明其支持oracle；整段可能含观察/建议而非期待，需要后续忠实性证据，机器trusted仍false。canonical锁定先于执行；原raw/引用证明/编译记录/输入全部保留与seal绑定。之前3个Gold区分是开发结果，不是独立gate、Agent修复或30/30；新方案不引入原测试断言、人工文件选择或native动作。pytest生成skip仍只合成，未知CLI/原test收集拒绝。

其余依[统一运行协议](E1C2_COMPILED_RUNTIME_DEV_V1_PROTOCOL_2026-10-07.md)：Flash only、thinking off、温度0，整批100000、每题20000、输出2000、最多4/题36/批，保守reserve1.4和后续初始reserve保护不降低；真实engine/source/image检查，失败无自动retry。先新零调用单测/完整回归/真实两仓库smoke、代码提交、预检freeze，再展示精确run命令使用用户现有≤100000实验授权。三个非准入题保持分母，四参考必须逐项报告，不best-of。若未达到四参考/跨仓库忠实性门槛，不抽新canary。

工作目录`D:\codex\working\project20260827`；各阶段命令只执行一次：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_referenced_runtime_dev smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_referenced_runtime_dev preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_referenced_runtime_dev run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_referenced_runtime_dev gold
```

输出`.codex/e1c/evaluation_2/referenced-runtime-old-dev-v1/`，smoke另目录。没有新下载/删除/IPC/VHD/registry/proxy/tunnel/key修改；tunnel旧白名单仍不支持本入口，云端缺本机素材即INFRA_BLOCKED。任何已有namespace不可重跑；canary/repair/sealed TEST/C5/Fresh30/private Test500/E2仍关闭，负结果封存。
