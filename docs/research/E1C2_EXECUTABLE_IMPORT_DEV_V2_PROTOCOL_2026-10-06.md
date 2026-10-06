# Executable import DEV v2：native fixture边界加固

## Material Passport

2026-10-06；仍为原DEV12、九题双准入开发，不重跑五批已封存canary/TEST/C5/Fresh30。v1完整方案/预检/离线合成/回归与源码提交f7d57d3保留，v1从未调用provider，不把后续改动回填它的freeze。新v2独立目录executable-import-dev-v2。

本版沿用[完整v1协议](E1C2_EXECUTABLE_IMPORT_DEV_PROTOCOL_2026-10-06.md)所有输入来源、窗口预算、显式执行、base/Gold同source、四参考/跨仓库验收与停止条件。补齐native fixture风险：仅声明fixture_source=generated_public_issue_only不够；目前没有可信生成文件/native harness适配器，禁止模型程序调用pytest.main（含import别名与_pytest.config.main）、runpytest/runpytest_subprocess/makepyfile/makeconftest，不让它默认跑仓库官方tests。B所有code字段与A source同样检查。既有静态I/O/网络/测试导入/动态调用拒绝继续有效，不增加执行权限。未知或绕不开native fixture的任务弃答，不猜参数，不声称支持所有pytest/CLI任务。

限定执行支持仍是direct_script与A的单个无装饰/无注解/零参数同步入口。仅函数定义无调用拒绝；显式入口只追加一次调用，生成检查保持原样且先过已有安全校验。检查本身是否真的走到、语义是否忠实不是普遍静态证明，仍需要独立评分与行为审核。所有旧负结果保留。

Flash nonthinking/temperature0，固定12/九eligible，≤18请求/每题2、批80000/每题20000、输出3000，SDK retry0/usage+reserve守卫。每请求前真实engine/image可用；当前Docker普通启动在旧IPC失败，**v2先完成零调用检查、恢复engine并重新预检后才可冻配置**。展示精确命令和现场reserve后使用用户≤100000既有许可，唯一新run仍为`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_executable_dev run`。如果方法/源码/输入变，不能继续旧freeze/补调用，另立版本。无需新镜像下载，原DEV12保留；15个历史封板canary镜像缓存已按用户允许移除，日志/源码/metadata全部保留。
