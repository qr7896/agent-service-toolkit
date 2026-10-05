# Counterfactual fixture contract：旧DEV开发协议

## Material Passport

2026-10-05，原DEV12，非独立样本。所有原trial/canary结果保留，不在canary调规则；不读公开测试断言/Gold生成代码。本协议只改变控制器处理和B通用指令，固定原自动生产窗口/issue预算。

先明确更正上一轮归因：DEV v3 export_text的control含feature_names一个标签，target六个标签；参数没有省略，类型与长度/值同时改变。不得把两因素混淆说成只改变numpy容器。旧说明保留，追加更正。

## 最小机制

标准库AST解析control/target最后API调用，只支持完全相同callee、参数结构且仅一个已知literal-container表示变化。解析未重赋值的top-level literal绑定与未遮蔽numpy.array导入，禁止eval/执行setup推断值；未知计算、dtype参数、多个变量变化、不同receiver/新增参数保留unproven，不假装语义已证明。numpy-array target与list/tuple control可生成元素/顺序/长度均相同的literal-list对照，完整target/setup/assertion/oracle不变。

引用生产文件SHA和其raise guard的file/line/predicate，但不声称静态解释了所有生产前置条件；真正的前置条件检查是派生对照在原network-none/pull-never不可变镜像中两次执行。若派生对照失败，STOP为fixture_contract_rejected，不跑target、不退回A绕过这一拒绝。编译之外的case复用原正对照和controller v2 oracle，明确保留unknown；不把unknown算PASS。B显式abstain仍STOP。

零调用`audit`读取完整已完成旧DEV v3九条B缓存，逐题记录派生证明/非支持/弃答，只在可编译case执行对照，无target/Gold读取。`replay`复用原完整hybrid-v1缓存和dummy cache model，加入新控制器，以新目录重做base/独立Gold；usage标记upstream，provider calls=0，开发4/12不是新生成或独立成绩。

## 运行/门槛

入口`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_dev`：先`audit`、`replay`。四条参考覆盖未保持不得开启付费。通过只证明合成/缓存范围，之后`preflight`冻结新输入与源码/协议SHA，再列精确`run`付费命令：deepseek-flash、non-thinking、temperature0、最多18请求、每题2、输出3000、单题20000/整批80000、SDK零重试，实际usage+reserve守卫。沿用用户单实验≤100000许可，不增加既有试验预算/重试。

完整新生成后同入口`gold`独立评分，固定分母12、环境失败3不移除、机器与人工语义审核分开；四条参考/两仓库仍必须保留。无净改善如实封存，不继续抽独立样本；有证据也只能先冻结完整新方法，再metadata选择排除所有旧DEV/三批canary/历史identity的新canary，一次≥2/3。Agent repair/TEST/C5/Fresh30/E2继续关闭。

产物目录counterfactual-audit-dev-v1、counterfactual-replay-dev-v1、counterfactual-dev-v1分开，均在`.codex/e1c/evaluation_2/`。过程日志只在集中续档追加；新结果不能覆写旧分数。不要为了全过强行改target、捏造值关系或隐藏未支持机制。
