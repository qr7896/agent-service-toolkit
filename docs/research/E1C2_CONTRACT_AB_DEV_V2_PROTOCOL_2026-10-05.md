# 旧DEV A/B第二版：生产窗口与截断JSON兼容

日期2026-10-05。第一版A完成九题、B在第八请求触发SDK LengthFinishReasonError而中断，原freeze/state/ledger保留，不重试原身份。本版是旧DEV上的新方法实验，两臂使用同一套重新自动生成的生产窗口和相同硬预算；不是把未完成的第一版补成完整结果。

新增生产路径过滤（doc/docs、examples、bench/benchmarks、build/dist等）、构造函数class-owner关联、公开API模块别名和命名版本差异的有限前缀检索线索。仍只读取允许issue投影和exact-base生产源码，四窗口/每窗口2500字符/context≤23,000，无任务ID映射。前缀仅支持检索，不直接作为行为oracle。零调用准备的中间版本保留，活动输入在`contract-coverage-dev-v2-ready/inputs`。

A仍为v4风格提示。B复用第一版逐字引用合同、正对照两次通过才运行目标、控制器call_completes到达断言；明确允许按issue声明的类型/前提构造缺失的最小确定性fixture，不允许改预期。B使用RawJsonFlash的basic completion接口发送JSON模式，截断响应/usage保留给预算账本；截断不补写代码、不重试，解析失败按原位拒绝后可继续下一独立任务。transport/provider异常仍停止，无自动重试。

每臂9题各1请求，deepseek-flash non-thinking/temperature0，单输出3000，单题12,000、整臂90,000 provider tokens。两个实验各≤100,000，提示不同实际成本分别核算。preflight绑定本版适配器、raw JSON组件、production coverage组件、原runner/合同/隔离执行器、完整issue-only输入、镜像和协议SHA。原14份canary文件和旧trial原件不变。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev_v2 preflight --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev_v2 preflight --arm B
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev_v2 run --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev_v2 run --arm B
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev_v2 gold --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev_v2 gold --arm B
```

模型命令先列明后按用户已有≤100,000/实验权限执行。本轮可见provider用量控制在一周计划累计282,000停止线内；剩余预算不是消费目标。官方评分补丁/日志不输入模型，Gold仅在候选锁定后独立判别。源码/镜像/来源不符原位停止，不替补。

第一版和本版都保留固定DEV12分母（九条可生成+三条环境失败）。先比同版A/B逐题可信数、正对照/fixture拒绝、格式/截断/弃答和实际tokens。B须至少保留A可信题且有新增，或在可信数不降时有清楚的误报/成本收益，才考虑选择；否则封存未证实增益。本版也包含多组件改变，不能独立归因单一算法。人工语义审核须披露；工程测试数不作修复率。

两批独立canary仍封存，不能回调。新DEV有增益后，先冻完整方法和预算，再选与DEV/历史canary不重叠的新canary，一次≥2/3后才进入Agent repair。sealed TEST/C5/Fresh30保持关闭。
