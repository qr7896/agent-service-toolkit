# Hybrid controller v2完整方法

2026-10-05。DEV hybrid-v1的新生成pilot为九题一次执行、最多B合同/A基础两策略，评分前选择，15请求；三条Gold可区分，但缺少预注册需要保留的日期任务。新controller v2把已接受的B行为合同贯穿到A回退，防止回退加入issue未要求的返回值/时区属性断言。旧pilot和缓存结果保留，不重写成绩。

固定机制：允许issue投影 → production coverage v2-ready四窗口（每窗口2500、context≤23,000）→生产文件SHA核验→从实际生产import恢复公开缺包前提→Flash B JSON合同→source AST证明的目标构造边界重分期（目标程序AST不变）→两次正对照→两次base目标→第一个稳定失败候选锁定。B不能提供候选才最多一次A请求，固定同一输入/预算。若B合同逐字跨度合法且oracle=call_completes，A末尾只有一个断言且最后API调用匹配B目标callee，编译器保留完整API程序，只用到达检查替换额外返回值断言；无法证明结构的情况不猜测。value_relation不编译弱化，语义仍需独立审核。

选择不读Gold，Gold失败不回头选另一个候选。SDK raw JSON保留截断/空内容/usage，单策略不自动重试；网络/权限/预算错误中断。模型deepseek-flash、non-thinking、temperature0、输出单次3000、每题最多2请求；DEV联合单题20,000/整批100,000。未知canary预注册固定三题、最多6请求、单题20,000/整批60,000，fallback按实际用量+reserve在线守卫，预算阻塞保留分母。

生成与判别隔离，容器network none/pull never/不可变official image ID；不读公开测试断言、Gold、评分日志生成代码，不人工选文件，无任务ID特例。正对照/语法/跨度只是结构约束，不自动证明语义正确。只有两次base稳定失败、同一候选Gold区分、issue语义吻合才计可信；不是Agent修复成绩。

本方法先在全部旧DEV缓存上单独回放验证，标记开发证据、零新增模型调用，不包装成独立泛化。未来确认集只能方法/协议/代码SHA先冻，再按固定metadata盐选择与DEV/两批旧canary/历史identity均不重叠三题；固定分母3、无替补、一次可信≥2/3。失败封存，禁止在确认集调规则后重称独立。通过后另冻Agent repair对照；TEST/C5/Fresh30继续关闭。

当前DEV v2付费入口（除非另冻新trial，不重用既有身份）：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_controller_v2 preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_controller_v2 run
```

本页同时作为下一批独立canary的完整方法附件；canary的身份/基础设施/执行适配器必须一起纳入其freeze，未完成镜像/官方双准入/公开输入前不运行模型。
