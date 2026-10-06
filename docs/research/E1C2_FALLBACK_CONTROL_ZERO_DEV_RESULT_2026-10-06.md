# A fallback：零调用前置有效性审计

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-06
- Verification Status: VERIFIED（仅本次离线审计，不表示复现语义或修复已验证）
- Version Label: fallback-control-zero-dev-v1

## 结果与研究价值

固定 DEV12 中原九个准入任务，V4 有五份 A 候选。本次不重新生成、不读 Gold/test：**一份派生对照失败、一份常量断言被拒绝，另外三份不支持或未证明**。没有新增可信复现或修复成绩。V4 的 Gold2/12 与原 state/ledger/freeze 均保持不变，不能用本次筛查重算它。

最小机制复用已有 counterfactual compiler，将一个可证明的 numpy literal array 参数派生成同值、同顺序、同长度的 list 对照。候选必须是可提取的顶层调用；多因素、计算值、变异/逃逸、shadowing、重绑定调用、函数/fixture 注入或未知执行形态不猜。生产文件严格校验路径、SHA、exact-base；源码同名定义和 guard 只作结构证据，不宣称已经解决全部 import/call binding 或语义等价。

`scikit-learn-26289` 自动派生三项 feature_names 的 list 对照，不修改原 X、labels、target 或 oracle。两个独立无网络容器均退出1、日志SHA相同；生产 guard 报 `feature_names must contain 1 elements, got 3`。因此这份 A 不能绕过对照进入独立评分。对照失败一般只证明 fixture/表示差异尚未隔离，不自动证明 issue 不存在；本例日志明确暴露维度不匹配。

`pytest-7432` 中 `assert True` 被通用常量断言检查拒绝，未执行它的 FakeItem。该检查不等于验证所有可达断言：`assert done` 仍可能只是完成标记，比较式仍可能错用返回结构。其余三份保留 unknown，不把拒绝率当新修复率或召回率。

本次原型尚未接入任何冻结 live runner。新增代码无 task-ID 分支、不手选生产文件；审计入口只枚举原 DEV manifest。合成单测含人工编写的普通 fixtures，不能说成实际任务输入全自动正确。新方法仍缺跨仓库正对照、返回关系/消费次数和 generated native fixture 支持，**不足以开启新 canary 或付费扩批**。

## 命令、产物与保全

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_fallback_control_audit
```

命令已经完成，one-shot 目录存在即拒绝，不再次执行。本轮 provider0、tokens0、Gold读取0。控制使用既有 `execute_candidate`：immutable official-equivalent image、`--network none`、`--pull=never`、只读/资源限制不变，每次先检查 engine。没有下载、删除、重启 Docker 或触碰 VHD/注册表/代理/tunnel/密钥。

公开[机器摘要](../../data/e1c_evaluation_2_fallback_control_zero_dev_v1_result.json)绑定本机 `.codex/e1c/evaluation_2/fallback-control-zero-dev-v1/`：freeze SHA `9d78aafbcd3a6eae3686fe48023031cb580861708edc660a5a3e931f0e89afb2`、result SHA `7a74c894f10b6592de09f5aaebc048afc0e18b4994249c9c8a3e22c223d3ba28`。原完整输入、候选、日志留本机；不上传评分答案。

首次预检曾错误比较文件SHA与canonical payload SHA，执行前被guard拦住，未建运行目录/调用模型/执行容器。修正为原freeze中的文件SHA，再分别核候选canonical input SHA；新增回归覆盖这两个hash不得混淆。保留该异常说明，不回填旧结果。

## 接手验收与下一步

工程验证：新增/相关专项24passed，指定预算/V3重点18passed，Ruff通过，原V3 compact preflight `ready=true`。完整单次1201passed/4skipped/33warnings/0failed，79.82秒；持久XML1205tests。没有弱化旧断言/skip/timeout，工程通过数不是SWE修复率。Docker现场Server29.4.0；本次执行前九个准入immutable image ID均核验。没有测试Web私有连接端到端。

1. 保持本次方法/记录与全部旧 freeze 不变。只在另立版本中开发，不重跑五批已看 canary。
2. 用合成与旧 DEV 证明合法对照可两次通过、非法对照会拒绝；至少跨两仓库，不能只靠一个 numpy 容器转换。用公开 issue + 生产 signature/guard/返回结构，禁止 Gold/test 修 fixture。
3. 另立 runner，将 A 的 constant-oracle 和 derived-control 检查接在 target/Gold 之前；B/A unknown 明确区分，不让未知一律当有效，也不将不覆盖题偷偷移出分母。新增 regression 覆盖两次控制、source/transport/timeout 拒绝、不吞异常和原 oracle 不变。
4. 完整非模型回归和四参考/跨仓库机制验收后，再冻结统一新 DEV 方法与预算；只用 Flash，新实验实际≤100000tokens、0自动重试，先列唯一精确命令。不凭本轮两个拒绝启动付费。
5. 新 DEV 有质量证据才预注册不重叠 canary；可信≥2/3且行为一致才另冻 Agent repair。随后同版旧 DEV 对照，最后全新任务一次性测试。TEST/C5/Fresh30/E2 目前全部关闭，无法承诺一周30/30。
