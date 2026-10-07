# E1-C evaluation_2：受限运行反馈闭环，旧DEV三仓库筛查 v1

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent; implementation: ponytail
- Origin Mode: run（准备与零模型验证）
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（模型实验与真实容器门槛未完成前不标 VERIFIED）
- Version Label: bounded-runtime-dev-v1

## 方法与边界

从静态窗口一次生成转为最多四轮受限 observe/act：生产定义检索 → 必要源码窗口 → 带正对照的复现合同 → 自己生成脚本的离线执行反馈 → 有界修订。借鉴 [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) 的线性反馈循环、[ReProAgent](https://arxiv.org/abs/2607.09123) 的分阶段复现和 [SWE-Doctor](https://arxiv.org/abs/2607.00990) 的运行证据方向；**不是安装/复刻这些框架，不继承论文得分，也尚未实现完整debugger诊断或Agent修复**。不用论文原版existing-test检索、不训练、不新增graph服务或大镜像。

唯一JSON动作：`retrieve`（plain symbol/owner.symbol）、`read`（仅先前已暴露生产path与正整数起始行）、`probe`（原七字段B合同）、`abstain_reason`。无bash、网络/安装、补丁或原测试读取。源检索先排除test/docs/examples/hidden/oracle路径，再读取≤1MiB regular exact-base生产Python；AST扫描≤32MiB、每次≤3窗口、每窗≤3000字符，最多两次不同symbol检索；合并最多8窗，完整模型数据≤30000字符。源码SHA、path containment、clean exact-base与immutable image检查保留；read只允许已知生产path并核SHA。AST同名查找不是动态调用绑定证明，尚无语义检索/真实CodeGraph接线。

模型看到公开issue投影、原断言-free public fixture facts、生产源码、自生成执行输出；看不到task ID、旧成绩、Gold/test/官方评分。合同quote须来自原公开issue，oracle为call_completes或value_relation。原native runner/fixture禁用、动态/IO静态限制不放松。两次control通过后才执行target；控制失败只修fixture/API，不改原任务输入来强行造失败。首次静态有效合同的issue_quote/expected_quote/oracle/assertion锁定，后续改变即停止；同式比较拒绝。此锁定也可能锁住语义不正确的初始oracle，不能声称已经自动验证语义。

控制和target仅用既有readonly/network-none/pull-never执行器；交通/身份/超时中止，不回灌为软件bug，不自动retry provider。trace仅取自己生成程序的末1600字符并审计信息边界；被过滤就不提供其正文。target稳定失败只是candidate，机器trusted仍false，选择在Gold前；不读取评分结果修订候选。底层静态guard不是普遍Python能力安全证明，不为模型开放本机shell或密钥。

## 零模型门槛与身份

先合成单测证明 retrieve/read范围、两次控制、反馈修订、oracle锁定、native拒绝、transport/identity/timeout与provider失败无自动retry。然后两个仓库的真实隔离合成smoke：生产普通API正确控制通过两次、target通过不得计bug、观察反馈后明确弃答。合成fixture由开发者编写，只验证控制器能力，**不表示任务输入由模型全自动正确生成，不是SWE/修复得分**。零模型真实smoke的文件SHA/method SHA匹配后才允许preflight。

候选源仅旧V4已封存九题。选题规则在新模型运行前固定：按旧manifest顺序取每个repository的首个准入任务，不按Gold成绩挑成功题；三仓库分别scikit-learn、marshmallow、pytest。仍注明原DEV12分母12，本次screen分母3，另外9条为未运行/原未准入，不能写完整DEV12成绩，也不能算独立canary。四参考验证尚未完成，无收益不扩批。

## 预算、入口与封存

模型仅 `deepseek-flash`，temperature0、thinking disabled、SDK/provider retries0。三题最多12请求/每题4、整批80000 provider tokens/每题26000、单次输出2200。实际usage＋保守reserve控制，不借预算；未够reserve标budget_stop。初始窗口/四轮轨迹未必能在每题26000内全部执行，这不是悄悄提高上限的理由。

```powershell
# Docker健康后，零模型；各自one-shot，失败保留，不自动重跑
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev preflight
# 必须先展示模型/精确命令/实际冻结上限，按用户≤100000授权边界
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev run
# 只在run完整封存后独立评分，不能把结果输入生成循环
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_bounded_repro_dev gold
```

新目录 `.codex/e1c/evaluation_2/bounded-runtime-dev-v1/`；合成smoke另放 `bounded-runtime-zero-smoke-v1/`。freeze包含方法模块、原V4来源、输入/镜像、协议、smoke结果SHA。run有state/ledger就拒绝；每轮保存input/response/control/target/反馈，完成后整个generation产物hash seal，评分核seal和当前method/source。provider异常中止整批、不重试；budget不足只保留budget_stop，不当作失败复现。

旧V2/V4/fallback audit/五批canary均不变。新结果分别报告：自动定位覆盖、control合格、重复失败候选、Gold区分、人工语义审查、实际tokens；禁止best-of合并/工程passed当repair rate。有效正控制不是四参考/可信复现gate。开发证据有收益后才完整同版DEV与全新不重叠canary；≥2/3且行为一致才另冻Agent repair。TEST/C5/Fresh30/private Test500/E2继续关闭。

## 失败与交接

本机engine或image缺失时停在INFRA_BLOCKED；不要模型试跑，不用网络拉取、不自动IPC修复。Cloud可接源码/合成单测/协议，缺本机source/image/执行器明确报告缺什么；现有tunnel未授权本新模块，不能假称云端可直接调新paid入口。不得索取密钥、开放裸Docker端口、读取公开predictions来补当前任务答案。文献中的已阅读案例不得再纳入独立canary。

预计先筛查闭环是否比静态生成有实质收益；环境恢复时间不包含在开发估计中。不保证一周30/30、不用成功子集替换固定分母；若三题无收益，保留结果并研究错误归因，不能重复收费抽样求全过。
