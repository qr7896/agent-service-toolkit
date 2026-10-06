# Faithful public input＋terminal API：旧DEV开发协议

## Material Passport

2026-10-06，原DEV12，实际双准入9题、固定分母12。四批canary都未达到独立门槛，v4 0/3封存；本版不重跑已看canary/TEST/C5/Fresh30。只在原DEV与合成数据开发，无任务ID→文件/规则表。

旧投影的代码围栏启发式会删除输入构造/dtype；新事实通道只序列化公开输入AST，不执行代码，不序列化断言、比较、测试导入/函数/类、答案变量、进程/网络能力，doctest只保留输入提示行，输出行不保留。常见断言别名（含numpy.testing）整块拒绝。纯声明fixture类、切片、构造参数、seed/dtype以JSON描述，unknown/预算不足拒绝不猜。此为保守语法边界，不声称能识别所有任意辅助函数的语义；当前旧DEV被接受块均来自已核SHA的官方public issue，不能补入test/Gold正文。

导入/重导出绑定public API所属生产文件，末端调用优先于setter/构造器；继承方法按父类跟随，import≤4跳、inheritance≤2、歧义弃置。生产包源码仅AST解析，不import/执行。明确关系type/depth/origin(seed)与source SHA、分段行号；省略docstring但不假造连续窗口。总4窗口、每窗≤2500字符，prose+windows+facts序列化≤23000；没有提高原证据预算或人工挑文件。

零调用完整原DEV九题审计中，3题保留共4个safe输入块，其余6题拒绝/无块，不代表它们通过；其中MultiTaskLassoCV原n/d/X/y/seed输入得以保留，并找到实际继承fit方法。四条参考必须在新生成中重新证实；旧缓存/旧成绩不补入本次。

继续复用counterfactual/positive-control/abstention STOP/oracle守卫；新输入先冻结，之后一次全九题新生成，再独立Gold评分和人工issue语义审核。模型deepseek-flash、non-thinking、temperature0、最多18请求/每题2、输出3000、单题20000/整批80000provider tokens、重试0、actual usage+reserve在线守卫；预算预检不够就停，不借用/提高上限。

零调用：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_faithful_dev preflight`。

唯一付费：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_faithful_dev run`，先列精确命令/Flash/18请求/80000，使用用户单实验≤100000的已有许可。

独立零调用：同模块`gold`。输出`.codex/e1c/evaluation_2/faithful-input-dev-v1/`；此前所有投影/locator/模型/评分/失败原件保留，不改既有冻结源码。

新生成需保留四条参考、跨两仓库，并对本版新增输入/定位有明确证据或可信覆盖/成本改善；没有改善则封存，不继续抽题。通过才完整冻结下一独立method（含事实通道/locator/预算/执行器），metadata-only选择与全部历史不重叠canary一次≥2/3。Agent repair、DEV30/Fresh30/E2仍有独立质量门槛，pytest不计修复率。
