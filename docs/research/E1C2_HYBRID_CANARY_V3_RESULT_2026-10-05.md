# 独立 hybrid canary v3：可信1/3，负结果封存

## Material Passport

2026-10-05；普通软件缺陷复现；冻结方法/身份先于内容读取，无人工选题/文件、无公开测试断言或Gold输入模型。模型deepseek-flash返回alias，无不可变版本snapshot。原始数据在`.codex/e1c/evaluation_2/hybrid-canary-v3/`，公开摘要见[data result](../../data/e1c_evaluation_2_hybrid_canary_v3_result.json)。本批一次执行，无自动重试/换题/后验补规则；负结果不是Agent repair结果。

## 执行与固定分母

用户完成3张镜像下载，官方/镜像站摘要及本机不可变image ID全部核对。六项官方离线Base/Gold：Flask和SymPy双准入通过；PyVista Base源码身份/官方日志有效，但25个目标测试没有明确失败或通过记录，因此Base不满足严格门槛，Gold通过仍不能双准入。不改官方日志解析或手工豁免，不换题，固定分母3。PyVista issue未物化、不调用模型。

两个准入任务自动物化公开issue/exact-base源码及统一生产窗口，无手选。现场live freeze最多4请求、首轮reserve15031，整批上限60000/单题20000/输出3000，保持方法总上限6不增加。精确命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3 run`，用户已有每实验≤100000许可；完成3请求7280tokens、无失败/重试，随后同入口`gold`独立离线评分。

| 任务 | 准入 | 请求/tokens | 结果 |
|---|---|---|---|
| Flask-5063 | 双通过 | 2/5366 | B明确弃答；A测试subdomain匹配，不是issue要求的CLI routes展示；base两次失败，Gold后仍失败，语义不符，不可信 |
| PyVista-4226 | Base未满足 | 0/0 | 不进入生成，仍占固定分母；不算模型失败 |
| SymPy-17150 | 双通过 | 1/1914 | B值关系probe直接比较issue所述log表达式；正对照成功、两次base稳定失败，同probe Gold通过；语义审核通过 |

机器`trusted_reproducer_count=0`和底层`trusted_reproducer=false`不回填；Gold区分1，叠加人工语义审核可信**1/3 < 2/3**。不合并旧DEV成功数、不把PyVista移除成1/2，不称自动语义验收。Agent补丁/official resolved未运行，sealed TEST/C5/Fresh30保持关闭。

## 失败启示与下一步边界

明确弃答不是要求换一种prompt强行生成。在旧DEV另立v3评估“弃答即STOP”，可避免不支持issue行为的A回退。定位器还可能由重名符号窗口占满预算，遗漏issue明确的生产路径；仅在旧DEV与合成夹具开发通用路径锚点，不在本批源码逐题调规则，不重跑本批声称独立。

旧DEV v3另冻输入/方法/预算，Flash≤18请求/80000tokens；完整结果后再判断是否保留基线、降低成本。未达到开发门槛不能继续抽新题来寻找好看结果；本批即使基础设施未来可修复，原独立成绩也不变。

## 原件完整性

live freeze SHA `965cf82b5e9b4960750fa749461aa0d3d999acfdf41ac77158fd87aabe2d9da2`；state SHA `5398942927391a14a69324b28577a4b36040d8bf8997feec9e920dd5b52bf5e6`；ledger SHA `151b37049b21a0fb8cd1119b42f00757bca8b2207637ee0bc83a1c61106eb483`。各任务评分摘要hash见公开JSON。历史transport receipt描述封板时的0调用状态，保留不回写；当前状态由本结果补充。未改Docker/tunnel设置、镜像/VHD未清理；D盘现场42.2GiB。

工程：完整回归1118passed/4skipped/0failed（50.55秒，33warnings），不是修复率；指定重点含canary专项21passed，Ruff通过，V3规定原preflight ready=true。新DEV路径安全专项最初暴露被拒绝测试路径导致异常冒泡，修复catch边界异常（先拒绝、后跳过，未读取测试），原断言不变，7项通过。
