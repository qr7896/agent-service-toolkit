# 同一原probe的公开旧版本源码对照 v1（零模型预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: local_public_version_witness_v1

命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_version_witness audit-dev`；provider calls/tokens=0/0，Gold读取0。新namespace `.codex/e1c/evaluation_2/version-witness-zero-v1/`存在即拒绝。仅处理behavior-gate四缓存中regression分支，其余固定not applicable。

旧版本只从原expected_quote唯一`<=version`或`==version`约束提取；原public report anchor已分类regression。自动从冻结production windows派生唯一包根，无task-ID→文件表。优先本地相同版本tag，校验祖先关系与生产`__version__`字面值；无tag时最多80条本地包init历史/90秒查找同版最近祖先。不联网、不fetch、不挑执行成功的版本；找不到保持source unavailable。

只从该commit archive生产包中的常规Python文件，归档命令单次指定core.autocrlf=false/core.eol=lf，每份原始归档字节必须等canonical Git blob；不改全局Git配置。拒绝路径逃逸、symlink、tests/oracle路径、超预算；最多64文件、总源码≤2MB。不改原source/git工作树，旧快照只落新私有目录；不读旧版本测试/Gold。镜像仍为原已下载官方等价immutable image，基础/当前base/source检查照旧，不下载其他镜像。

原target probe字节不改，另一个readonly mount挂历史生产包，PYTHONPATH将历史源码置前，原optional dependency blocker优先。旧源码全部SHA核验，实际导入的`__version__`及`__file__`必须为该历史快照。各适用task只执行一次隔离net-none/read-only/pull-never、90秒硬超时；infra/source/import/version前置失败与真正旧probe失败分账，超时仅移除本轮临时容器，不自动retry。

旧rc0只支持“同一model程序在这个公开旧版本完成”；不是证明所有更早版本、原公开完整fixture、全部行为义务/恶意probe attestation或修复效果。不重跑当前base（已seal的执行结果单列），不回填behavior-gate/资格/Gold。机器trusted仍0；先收证据再另版完整方法，不开启canary/TEST/C5/Fresh30/privateTest500/repair/E2。

专项/Ruff通过后执行本命令。保留freeze/源码快照/driver/log/result；不重启Docker/改IPC/VHD/registry/proxy/tunnel/key，当前无镜像下载需求。
