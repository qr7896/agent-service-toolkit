# 统一编译运行反馈 DEV v1：实验前协议

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（执行结果另存，不回填协议）
- Version Label: compiled-runtime-old-dev-v1

## 研究对象与方法

只运行已调参旧DEV，不声称独立验证。原12固定分母、九条双准入全部按旧freeze顺序保留，包含四条历史参考；其余三条未准入仍占分母。只读公开issue投影、原assertion-free fixture事实、自动selected生产源码、自己的离线执行反馈。不读原测试断言或Gold给生成器，不手选文件、不按task ID补规则。

新runner复用被冻结的retrieve/read、JSON固定metadata解码、实际上一Assistant行动/Controller观察与4轮界限。比较字段Expr→Assert保持谓词AST；生产构造前沿保持完整target程序AST；源码静态strptime格式只替换正常control，target/quote/oracle不改。每turn单独保存raw response、raw/canonical合同、编译证明、control和target，先canonical再oracle锁定。正常控制两次必须通过，target必须重复失败。语法规范化不声称原无assert程序等价；格式正常对照不证明时区语义等价/target格式绑定。独立Gold区分仍不等于机器可信复现。

本版不开放原生pytest CLI/生成fixture动作，生成skip组件仍只合成。需要原生能力的任务明确弃答/拒绝，不伪造safe_static_check、不运行原tests/conftest、不静默纳入旧pytest缓存成绩。无损source压缩实际只省6tokens，未接live。当前只是受限反馈实现，不是完整mini-SWE-agent/debugger/Agent修复。

## 固定预算与公平性

仅`deepseek-flash`、thinking disabled、temperature0；整批100000 provider tokens、每题20000、每次输出2000、每题最多4/整批最多36请求，SDK/provider自动重试0。每次真实engine/image/source核验，失败停止保留。预算估计系数1.4不降低；初始reserve合计必须≤100000，每项≤20000。早期task的动态整批ceiling扣除所有未运行task的初始reserve，保护它们至少一次调用机会（保守reserve不是对实际usage的绝对保证）；动态ceiling只收紧，从不超过整批上限。预算不足停止本题、不借旧实验预算或重试。每turn即时进度打印。

同名smoke/preflight/run/gold各仅一次；已started不得重跑，新方法必须另身份，不改旧方法/账本/冻结/响应。所有文件SHA在新freeze与generation seal绑定；producer完成seal后独立Python-only grader验证同一candidate。评分结果不回输入模型，trusted_reproducer=false保持，行为忠实性另审。

## 命令、输出与验收

工作目录`D:\codex\working\project20260827`。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_compiled_runtime_dev smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_compiled_runtime_dev preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_compiled_runtime_dev run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_compiled_runtime_dev gold
```

`--offline`只禁止uv取包，付费run仍需DeepSeek HTTPS；验证容器network none/read-only/pull never。输出`.codex/e1c/evaluation_2/compiled-runtime-old-dev-v1/`；smoke单独namespace。执行前需专项/Ruff、规定预算V3重点/preflight、完整非模型回归与两仓库真实合成控制验收。人工合成smoke不是task得分。

结果报告每task状态、实际calls/usage、两control/重复失败/Gold区分、四参考、固定分母12与九准入覆盖、机器可信数，不能拼接best-of或工程passed冒充修复。负结果保留并回DEV改通用机制，不抽新canary掩盖。开发有收益且行为门槛证据后才完整冻结新的不重叠独立canary；≥2/3且忠实性审查过才另冻Agent patch/官方评分，再同版DEV对照，最后新任务一次性测试。sealed TEST/C5/Fresh30/private Test500/E2保持关闭。

Docker/VHD/注册表/代理/隧道/密钥/镜像/IPC备份不修改，没有下载或删除计划。WebCodex可接源码/单测/公开摘要；缺本机环境即INFRA_BLOCKED，旧tunnel白名单不自动扩展到此paid入口。
