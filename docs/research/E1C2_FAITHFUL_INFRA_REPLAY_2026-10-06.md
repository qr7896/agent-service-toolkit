# Faithful DEV验证引擎恢复：零新增模型回放

2026-10-06。原faithful-input-dev-v1生成16请求/37593tokens已完成，但Docker Linux Engine未运行，管道错误被旧执行器误记重复失败；Gold七条均未应用补丁，不能评价模型能力或当0/12能力结果。原freeze/响应/ledger/state/日志全部保留，结果标INFRA_INVALID。本次不是新生成，也不自动重试provider。

恢复只允许普通Docker Desktop启动，核验server/image ID；不删除socket/镜像/VHD、改注册表/代理/tunnel或更换依赖。先同一代码/输入/预算的preflight与原freeze逐项相等，绑定原全部缓存response SHA。然后新目录faithful-input-dev-v1-infra-replay-v1，dummy cache model、真实API钥匙不用、HTTP不发请求；所有usage标upstream，provider_calls=0。每个候选前检查Docker engine/image，执行JSON出现transport错误则立即中断，不把CLI失败记软件故障。

容器与评分协议不变，target/oracle/fixture/模型响应不得修改。恢复后控制器按实际正对照/target分支选择同一批已生成B/A缓存；没收集过的角色只记录controller cache-missing，不调用模型、不把合成弃答称模型输出/通过。单独公开缺缓存影响。旧错误state不回填；回放是DEV诊断，不是独立泛化或新模型成绩。

零模型入口`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_faithful_infra_replay`依次preflight/run/gold。新guard仅用于独立恢复适配器，不修改任何已冻结源文件。若Docker无法启动，停止验证并报告外部阻塞，不再新增付费。未来新付费身份必须将真实engine/image运行态准入纳入每任务/provider前置门槛；不能仅看磁盘loaded.json。
