# Counterfactual DEV：输入缓存的零调用执行适配

2026-10-05。完整对照机制/预算沿用[E1C2_COUNTERFACTUAL_DEV_PROTOCOL_2026-10-05.md](E1C2_COUNTERFACTUAL_DEV_PROTOCOL_2026-10-05.md)，只新增执行身份，不改方法、任务、生产窗口、oracle、模型或预算。

原preflight/run/Gold每次重做全部生产定义索引，造成重复CPU开销。新入口消费完整旧DEV v3已冻结的九条输入；逐次重查freeze/state/文件SHA、exact-base干净Git、选中生产路径/SHA/AST及不可变image ID，不跳过隔离/完整性检查。模型输入与原counterfactual试验预检逐字相同；新增提示只是原已冻结counterfactual B指令。不手选文件，不读公开测试断言/Gold。原慢入口的零调用freeze保留，不能覆盖或伪装成已付费。

新目录`.codex/e1c/evaluation_2/counterfactual-fast-dev-v1/`；原audit/replay和Git提交37c84c8保留为零调用机制证据，helper/机制源码不变。先核对零调用gate四条参考保留，再preflight；输出绑定本适配器、本页、上游冻结输入与已完成state的SHA。

入口`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_fast_dev`，依次`preflight`→`run`→`gold`。唯一付费命令run，deepseek-flash、non-thinking、temperature0、最多18请求/每题2、输出3000、单题20000/整批80000、重试0；用户已有单实验≤100000许可，先列精确命令。原counterfactual-dev-v1仍未调用模型，不再运行其慢入口进行重复试验。

冻结原DEV12分母，实际九题；新生成/Gold/语义审核单列，缓存4/12不算本次新生成。四参考/跨仓库开发门槛未过则封存，不抽新canary；通过也要完整冻结新方法后再选择真正不重叠canary。现有三批canary、sealed TEST/C5/Fresh30不打开或重跑。
