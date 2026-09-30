# E1-C evaluation_2：独立 canary v1 结果（2026-09-29）

状态：`sealed_negative_below_preregistered_threshold`。本批固定三题、三仓库，不能替换、重跑或在看过结果后改规则再称为独立 canary。未打开 E1-B sealed TEST、C5 或 Fresh30；未运行新版 official repair。

## 冻结身份与执行

- 方法文件 `data/e1c_evaluation_2_canary_method_freeze.json` SHA-256：`e78f9670cf009596ef9f31f9aba5f04685be5c133c9cc3558a2f0e3598847013`；身份文件 `data/e1c_evaluation_2_canary_identity.json` SHA-256：`d078af8c0ba6da3c2a8945db4ab0461fd729bb2658c418eb8576be334d4f9551`。两者在结果后未改。
- 三张镜像均已按官方描述符、导入后不可变 image ID 核对。零模型官方 Base/Gold 准入：scikit-learn-10581 与 Marshmallow-1702 均通过；Sphinx-10320 的官方镜像 `/testbed` 有未提交的 `tox.ini` 修改，源码身份守卫在运行官方评分前返回 90。Sphinx 原位计准入失败，不替换、不放宽守卫。
- 两条已准入任务由公开 issue 与冻结 base 的生产源码自动生成输入，各有 4 个源码候选窗口；生成侧未读取评分补丁、官方测试或 grader 日志。Sphinx 未读取 issue。离线 probe 容器使用 `--network none --pull=never`。
- 付费命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_live run`；模型 `deepseek-flash`，最多 2 请求，单题硬上限 14,000、整批硬上限 42,000 provider tokens，输出最多 2,600，无自动重试。运行前预留 15,161；实发 2 请求，分别 3,336 和 2,419，合计 **5,755 provider tokens**，均未超限。live freeze SHA-256：`bbb5f8b96b75ca065086d9be88735dd747ec25c98bb71632ff9ae5010952bbf4`；调用账本 SHA-256：`64ed0cdfce715daa111e1c25dc3a8866d5f92641a6ee6ac1ea58b7e8356faf42`。原响应、账本与状态保留在 `.codex/e1c/evaluation_2/canary-v1/live/`。

| 固定任务 | 官方准入 | 生成与离线验证 | grader-only Gold | 最终可信 |
|---|---|---|---|---|
| `scikit-learn__scikit-learn-10581` | Base/Gold 通过 | 模型 probe 与公开 issue 中 `ElasticNet(..., copy_X=True).fit(..., check_input=False)` 修改输入 `X` 的行为一致；补丁前两次同一 `AssertionError`、日志 SHA-256 相同 | 同一 probe 在 Gold 应用成功后退出 0 | **是，1** |
| `marshmallow-code__marshmallow-1702` | Base/Gold 通过 | 模型按公开 RFC 缺少明确可断言的行为判据而弃答；冻结校验器无 Python `source`，未运行 probe | 不适用 | 否 |
| `sphinx-doc__sphinx-10320` | Base/Gold 均未过源码身份守卫 | 未读取 issue、未调用模型 | 不适用 | 否；固定分母保留 |

scikit-learn 的 `assertion_candidate` 本身不等于可信；最终晋升额外核查了公开 issue 语义、两次同日志 base 失败、Gold 补丁已应用且同一 probe 通过。Gold 判别记录 SHA-256：`29fe5597c136fb7d8e7f0ac36079fd3252c8ade07dea3d26c982b8161f6adadc`，评分材料没有进入模型输入。

## 结论与后续边界

预注册门槛是固定分母 **≥2/3**，实得 **1/3**，故未通过。它不是自动修复成功率，更不能推断旧 DEV30 或全新任务的表现。本批三题以后只能用于开发诊断，不能再次作为独立验证。下一轮仅可在旧 DEV/其他非 canary 开发材料上改进任务无关方法，另行冻结完整机制与预算，再从未读、未调参且不重叠的任务中选新独立 canary；未过新门槛前不得启动新版 repair live 或 Fresh30。代码全量回归 `1083 passed / 4 skipped`，仅证明软件回归通过，不是研究成绩。

优先开发顺序：先在旧 DEV 上预注册并测量“公开 issue 是否给出可执行行为判据”的任务无关准入，弃答与格式错误分账；再为官方镜像工作树不干净的问题设计不改变题目源码语义的隔离 clean checkout，并要求独立 Base/Gold 重过；最后针对 DEV 中重复失败却 Gold 不区分的题改进通用 probe 生成与语义裁定。每项先做零模型回归和消融，再冻结新方法。不能把本批 1/3 后验改成通过；新 canary 的镜像和任务内容只有在新方法冻结、选题后才获取。
