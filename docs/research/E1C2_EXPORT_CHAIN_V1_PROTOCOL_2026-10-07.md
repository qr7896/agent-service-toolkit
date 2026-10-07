# 静态重导出链身份 v1（零调用预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: export_chain_v1

命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_export_chain audit-scope`。预算provider calls/tokens=0/0，不执行容器或仓库代码；只读已经封存的reference-scope四缓存所列条件引用，自动推导模块/重导出文件，不按task-ID手选文件、不读Gold/test/grader。

新namespace `.codex/e1c/evaluation_2/export-chain-zero-v1/`，存在即拒绝重跑。冻结scope结果、源码和本协议摘要。每个链节点须唯一模块位置、受限生产路径、普通文件≤1MB、host LF投影等于exact-base Git blob。只有单一静态定义或绝对/相对from-import可延伸；普通module-import影射、赋值/条件/动态绑定、star export、多重绑定、循环/过深、缺失/歧义/源码变化均unknown或入口拒绝。

指标仅为`static_chain_supported`，不得称公开省略namespace的意图已证明、runtime对象相同或可信复现；machine trusted仍0。保留host与canonical两摘要。只做静态链身份，不认证装饰器、metaclass、副作用或任意Python行为。无新live完整方法冻结，不打开canary/TEST/Fresh30/repair/E2。
