# Controller generation V4：输出格式修复，研究质量未提升

## Material Passport

2026-10-06；旧DEV12固定分母、九题eligible，非独立确认。V2新生成3/12、V3缓存3/12原样保留；本V4是真新生成，不混缓存/旧成功数。只有公开issue/生产源码/无断言fixture描述输入，无网络不可变镜像执行，Gold/test仅独立评分；五批canary/TEST/C5/Fresh30不打开。

## 一次新生成与评分

先提交完整代码与协议f7693b7，现场freeze40cd232e56945628f8c1f6e0946d3b1f659bb574081c252e1aaa51029c3ef2fb，Flash≤18/80000/每题20000/输出3000、primary70238、temperature0/disabled thinking/retry0。展示精确controller_generation_dev run命令和预算后按已有≤100000许可一次运行。14请求35889tokens全完成，无provider失败/重试。五个base稳定候选，独立Gold五项2真3假：ISO-Z与List(DateTime)消除失败，ndarray/generator/pytest候选仍失败，warm_start主动弃答、Lasso无稳定失败。

**最终Gold2/12，未保留四参考、开发门槛失败。** 机器trusted仍0、语义审核未逐题封板，不称自动可信/Agent修复或独立泛化。[状态/账本/freeze绑定](../../data/e1c_evaluation_2_controller_generation_v4_result.json)。原V2/V4全部source/response/ledger/state/独立评分一字不改。

## 有效工程改进与限制

本版将A可信指令System、公开数据Human、末尾显式请求输出；controller-owned execution grammar不要求模型填写能力manifest，仍拒绝输入echo与native/未知fixtures。A五份均返回source且执行，不再input echo；这是格式指标改善，不是质量净提升，不能从不同试验的1/3→5/5推断严格因果。prompt变更未增加窗口/预算，完整回归1181passed/4skipped/33warnings/0failed（68.70秒），重点和原V3 preflight通过；工程通过不算研究成功。

独立评分后的仅生产/生成源码诊断：ndarray候选训练X四行一列却传三项feature_names，属于fixture维度不一致，不能将其稳定失败当原issue复现；pytest候选构造FakeConfig/FakeItem，最后assert True，生产hook触发的异常Gold仍在，也不代表collection/skip-location原问题。generator仍有返回形态/重复调用与期望关系未建立的问题，不能用Gold答案补断言。warm_start因“base缺参数/fit窗口不足”弃答，揭示特性请求与真实行为前提需分开判别；不得写任务ID特例或人工补文件。

## 后续停止条件与实施重点

不继续付费重复提示微调、不抽第6批，先做零调用生产前置条件/正对照机制：从API签名/guard/生产返回结构约束fixture，优先证明控制样例有效；A fallback不能因为JSON可解析就绕过fixture与oracle约束。对可证明的类型/表示对照保持literal/长度/调用不变，控制失败即停。不能自动改输入维度“让它过”，未证明关系保留unknown；在合成＋旧DEV验证，不在本批已看canary上改规则重称独立。

还需可信generated-fixture/native harness与文档/特性请求的任务无关路由，明确哪些当前语法不能支持；不能以改变分母/删除失败/拼接版本实现30/30。只有新零调用机制真通过、旧DEV单版四参考保持并有新增实证，才完整冻结下一独立方法，再按历史全排除选三题一次≥2/3；Agent repair/DEV30/Fresh30/E2随后有独立门槛。

本轮两次新生成12+14=26请求，36689+35889=72578provider tokens；V3缓存新增0。10月5日起可见累计304489（含旧SDK错误4281，非账单核验）。Docker已恢复，全12镜像与本机bridge status健康；15旧canary镜像缓存清理收据保留、原始记录源码未删除。本次没有新镜像下载/额外FS清理，原IPC目录仅备份改名。
