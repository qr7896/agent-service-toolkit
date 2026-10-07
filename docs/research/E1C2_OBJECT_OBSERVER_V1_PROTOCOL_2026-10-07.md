# 构造器对象对应 v1（零模型离线预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: object_observation_v1

命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_object_observer audit-dev`。provider calls/tokens=0/0，无Gold读取；新namespace `.codex/e1c/evaluation_2/object-observation-zero-v1/`，存在即拒绝重跑。仅诊断已封存四参考中的条件引用，不产生新probe或新修复成绩，其余参考保留not applicable，不挑成功项改分母。

原producer seal/全部生产侧文件摘要、export链结果收据先核验。由静态链末端class的唯一、未装饰、直接`__init__(self,...)`自动定位；继承/装饰/非self参数等未知，不人工替换文件或构造器。原probe字节单独readonly挂载；复用现有离线执行器、镜像准入与90秒硬超时。容器network none、read-only、pull never；全部export链文件同时验证runtime原字节==exact-base Git blob==host LF摘要。保留原公开依赖缺失blocker，不改全局安装。

在生产构造器call事件核对filename/firstlineno/name及`self`类型与该模块声明class的identity/MRO关系；只输出路径、行、控制器symbol与布尔结果，不输出参数、对象属性、repr或异常raw消息。MRO通过内置type getset descriptor读取，避免调用实例自定义getter；不执行模型提供的追踪器或对driver伪造safe_static_check。普通缺陷研究边界，不是任意恶意Python下的attestation，instrumentation可能影响时序/filename，不能保证语义等价。

观察成功只报告`constructor_binding_observed`，Schema子类可报告MRO包含而非exact type。缺观察、错误对象、infra/source失败分开；没有自动retry，不借此清除公开namespace意图unknown或授予trusted。目标是两条件引用的真实构造器关系，不是整DEV12或30/30修复。失败保留freeze/driver/log与failure；不重启Docker/改IPC/下载或动代理/tunnel/key。

专项反例通过后才执行本命令；随后先校准有限公开行为义务再完整method freeze与同版DEV。可信gate真正达成才另注册新canary，不开sealed TEST/C5/Fresh30/private Test500/repair/E2。
