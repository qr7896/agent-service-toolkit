# 公开literal与生产解析边界的零调用差分覆盖诊断

日期：2026-10-08，身份 `public-temporal-boundary-zero-v1`。触发条件：原公开issue-derived target在保留模型补丁上已两次完成，而完整修复尚未证实。**不读取官方测试/Gold内容或失败断言**；操作符仅从公开原literal、生产源码ISO解析分支（分数秒/固定长度切片/时区支持）及公开引用旧版本派生。这是DEV看过之后设计的诊断，不称预注册独立泛化。

算子不含task-ID→文件表：自动要求原target AST中唯一、也在公开issue中出现的ISO时间字符串，以其年月日时间前缀和原小数数字，形成精度0..6 × `Z / +00:00 / -04:30` 共21个变体。仅替换此literal；原生产调用、fixture和执行完成guard保留。偏移变体是根据生产时间解析家族生成的**合成假设**，不是作者报告数据，支持范围仅此时间字符串家族，不声称可解决所有task。

这是预定义的时间字符串类通用算子：0..6与三个时区是本轮在运行前固定的参数，literal定位自动；并非程序已自动推导任意源码的语法。算子设计参考已暴露的生产解析分支，不使用官方失败断言。后续其他数据家族需独立定义/冻结，不能把本算子冒充通用完备覆盖。

在三个独立无网络/no-pull容器中，各运行21个子进程probe：未改base、原模型patch、公开2.19.3生产包。原missing dateutil条件一致；driver验证每变体源SHA、实际包导入路径、实际旧版本与14源manifest。public release只读挂载、host不安装；patch只写隔离容器层，宿主挂载只读。各批90秒/各子进程10秒上限，无自动retry。源码/协议/原probe/patch/版本来源先冻结，新namespace不重跑。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_public_precision_sweep
```

报告各相同变体的base/patch/release完成或异常及源SHA，找“旧版可完成而模型patch仍失败”的公开条件counterexample。完成状态不是返回值等价；旧版本可能丢失微秒，绝不强制把所有新版本值改回旧值。结果不提升full issue/namespace可信，不回填官方修复或原三cell成绩，不计21个独立task。

若发现counterexample，下一轮把这种自产失败trace与自动生产窗口补证接入修复反馈，避免只匹配原一条字符串；不是把评分测试当答案。任何新付费方法仍需完整新freeze和精确命令授权。不开TEST/Fresh30/canary/E2，不更改配置/代理/tunnel/密钥、不下载/删除。
