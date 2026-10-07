# 模块限定构造器关系 v2（零调用预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: module_constructor_relationship_v2

v1已封存：Schema无直接`__init__`，整体unknown，未运行容器。v2是新范围/源码/namespace，不重跑v1。命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_object_observer_v2 audit-dev`；provider calls/tokens=0/0，Gold读取0；新目录`.codex/e1c/evaluation_2/object-observation-zero-v2/`存在即拒绝。

不按框架名或helper名解包元类/继承。由冻结export末端模块自动列出全部顶层class中的未装饰`__init__(self,...)`候选行（每binding最多32行、2binding），观察实际call，再用该模块公开声明class与self类型的identity/MRO关系判定“关系出现”。v1的source/probe/base/image/nonce/路径/隔离/超时/原dependency blocker门槛全保留。输出所有匹配构造器记录；非对应调用不抹除。按每个声明binding是否存在关系记录汇总，不按task结果best-of，不将Schema子类误称exact type。

同一源码模块中存在某构造器不构成静态继承证明；factory/with_metaclass调用不执行或解释，只有实际MRO布尔支持关系。不存在、scope外模块、decorator/cls构造器或超预算保持unknown。此观察非公开namespace意图/行为可信证明，也不是抵抗恶意probe的attestation；instrumentation不能保证完全语义等价。固定四参考和DEV12分母不变，其余无条件binding为not applicable。

专项/Ruff通过后仅执行一次本命令。失败保留原freeze/driver/log/failure，不自动retry，不修Docker/IPC，不加模型预算，不开canary/TEST/Fresh30/repair/E2。成功后仍需有限公开行为义务校准、完整method freeze与同版DEV gate。
