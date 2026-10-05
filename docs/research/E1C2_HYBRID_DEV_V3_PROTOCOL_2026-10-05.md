# 旧DEV hybrid v3：弃答STOP与生产路径线索

## Material Passport

2026-10-05，开发实验，固定原DEV12（双准入9题模型、3题留分母）；非独立验证。新canary v3已1/3负结果封存，不能在其上调参后报独立。仅原DEV12输入、生产源码、新响应与自己的执行反馈；不读取公开测试断言/Gold正文生成代码。

先在合成夹具及旧DEV零调用预检证明：公开issue中的准确现存生产相对路径与行号先取得一个源码窗口，路径越界/测试/文档/非Python/不存在/非法语法拒绝；仍4窗口、2500字符每窗、23000context。其他规则复用冻结production coverage。无任务ID特殊表、人工选文件、扩大输入预算。路径只提供定位证据，不据此生成oracle。

B模型合同明确弃答时直接STOP，不再花A请求“救活”不支持的行为。B格式/fixture失败或目标通过但未形成重复失败时，最多一次A，保留controller v2的原合同oracle守卫。第一个base重复失败候选锁定，评分之后不回头重选；结构检查和Gold区分均不替代issue语义审核。

模型deepseek-flash、non-thinking、temperature0、SDK重试0；最多18请求、单题≤2、输出3000、单题provider tokens20000、整批80000，实际usage+reserve守卫。显式弃答避免A调用，应分别报告省调用与可信覆盖是否退化，不能称新算法SOTA。冻结输入/代码/方法后运行一次新生成，不借旧缓存最好成绩。

精确零调用命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_dev_v3 preflight`。

精确付费命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_dev_v3 run`；先列模型/次数/预算，使用用户已有单批≤100000许可。失败不自动重试。

精确独立零调用评分：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_dev_v3 gold`。旧DEV grader目录不输入模型，probe在network none/pull never不可变镜像内运行。新输出`.codex/e1c/evaluation_2/hybrid-dev-v3/`，旧身份及失败记录不改。

开发审查门槛：保留四条参考可信覆盖、跨两仓库；弃答不计通过。未达到则如实记负结果，不扩独立样本；达到也必须新方法完全冻结后再选与全部历史身份不重叠的canary。此前独立1/3不被开发成绩覆盖，Agent repair、sealed TEST/C5/Fresh30仍关闭。
