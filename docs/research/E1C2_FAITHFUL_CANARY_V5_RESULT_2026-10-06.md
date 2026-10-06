# Faithful独立canary v5：0/3完整负结果

## Material Passport

2026-10-06；方法与身份在新正文之前冻结；排除304历史身份，固定SymPy-22080/Sphinx-9180/pytest-7749，无替补。只公开issue/生产源码输入，容器无网络、pull never；Gold/test只独立评分。原方法、身份、输入、响应、账本与失败均保留。详见[公开结果与SHA](../../data/e1c_evaluation_2_faithful_canary_v5_result.json)。

## 执行与预算

用户完成3/3下载后，loaded/official manifest绑定及现场immutable image ID全部通过。六项Base/Gold准入，SymPy/pytest双准入；Sphinx两项source_identity_pass=false、退出90，官方日志无效。不是镜像未下载，不放宽源码身份、不送模型、不替补；仍留分母3。仅两题物化公开输入，production窗口/fixture facts自动产生，无人工选文件。

live freeze c70b66df87be7d91cf62a64245baa78412100b3984c90184805a479ad346739e，现场最多4请求、批60000、每题20000、输出3000，首轮reserve15726。先展示唯一命令`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_faithful_canary_v5 run`与Flash预算，使用用户单实验≤100000既有许可一次执行。实际3请求9642tokens，无provider失败/重试；每请求前真实engine/image核查。随后独立gold一次attempted0/discriminating0，因为没有稳定base失败候选。

## 逐题与结论

| 任务 | 实际发生 | 分数与局限 |
|---|---|---|
| SymPy-22080 | 公开输入块因unsupported_statement被整块拒绝、terminal窗口0；旧词法窗口四个同名symbols，缺Mod/lambdify/printing路径。B明确弃答，1请求1602tokens | 0；不在本批补定位再重跑 |
| Sphinx-9180 | 现场官方镜像可用，但Base/Gold源码身份前置检查均失败，退出90 | 0且留固定分母；不能把它当模型能力失败 |
| pytest-7749 | B格式化API候选base通过，未触发公开collection NameError问题；A生成test函数但直接python脚本只定义、不调用，base同样通过。2请求8040tokens | 0；不是证明原bug不存在或任务已修复 |

**最终可信0/3<2/3，独立门槛未过，封存。** 机器trusted0、人工审核通过0、Agent repair未运行；不把工程passed数或DEV5/12补进来。五批独立结果依次1/3、0/3、1/3、0/3、0/3，不能取best-of。没有TEST/C5/Fresh30/新版修复或E2结果。

## 仅事后诊断与回DEV路线

两项通用不足：输入整块拒绝时丢失安全的import来源，词法同名窗口占满；执行契约没有区分“已定义测试函数”与“已运行测试函数”。已有机器STOP和预算门槛正确停止，但不会自动解决定位/执行表达不足。不得用本批Gold/test答案开发规则；零调用新原型只回旧DEV与合成案例，v5不再称独立可调样本。

新增`import_seed_audit.py`只收公开代码块开头绝对from-import，遇任何非import语句即停止，不遍历断言/函数体/输出值；只AST解析生产文件/reexport归属，未知/歧义不猜。对旧DEV九题零调用审计，仅3题取得4个此前窗口中没有的定义窗口，这是结构可达性，不是修复或复现提升。v1执行代码在3cb7bf9保留，执行module SHA3d70e6eda76269f9d0b2d2b0301edd3a3cbd519dc99fe570302412d6fa185ebf；后续整理import格式、新增独立invocation诊断，并加固答案型import名称/别名/根拒绝，另立v2零调用审计。原v1不回填，不将后续改动写成已用于v5模型。

新invocation诊断保守标记“仅导入＋无装饰/默认值/注解副作用的函数定义，没有顶层调用”；不证明任意程序可达，也不自动执行未知入口。旧DEV8份候选中1份命中；v5的A命中只是事后解释，不加新分数。下一新版DEV需把诊断接入候选准入，明确manifest的执行模式/入口/fixture，并在离线合成案例证明真正触发检查。原冻结runner不修改、不复跑、不重新调用provider。

继续门槛：先同4窗/23000字符预算接入import fallback、保留原terminal优先；再证明执行器“函数-only拒绝、明确入口真执行、非法入口拒绝”。未完成这些零调用验收不新增付费。通过后另冻完整旧DEV方法/预算，一次Flash试验验证四参考保持、跨仓库及覆盖/成本；不承诺30/30，也不立即抽第六批。当前累计10月5日以来可见usage231911（含旧SDK错误4281，非账单核验），本批新增9642。
