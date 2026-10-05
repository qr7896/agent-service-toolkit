# Counterfactual独立canary v4：完整冻结协议

## Material Passport

2026-10-05；任务身份未知；开发依据为旧DEV一次新生成13请求/26762tokens、Gold及人工可观察行为审查4/12，非独立、非修复率。array病例证明参数兼容性，未声称原报告同一错误行/栈。机制附件[counterfactual](E1C2_COUNTERFACTUAL_DEV_PROTOCOL_2026-10-05.md)、[输入执行适配](E1C2_COUNTERFACTUAL_FAST_INPUT_2026-10-05.md)、[原controller v2](E1C2_HYBRID_CONTROLLER_V2_METHOD_2026-10-05.md)。

先冻结全部方法文件与预算/DEV结果SHA，再从原metadata池按固定盐`e1c2-counterfactual-independent-canary-v4-2026-10-05`排序，repo优先/task次序各前三仓库各一题；排除DEV/三批canary/所有历史identity/污染ledger。选题时不读issue/源码/答案；固定分母3、无替补。方法或预算不得在读新任务后修改。

生成只读允许issue投影、exact-base生产源码：原自动production coverage加准确issue路径/行号锚点，四窗口/每窗2500/context23000，不人工挑文件/使用taskID分支。公开输入物化时定位，随后冻结字节；每次live核验seed SHA、窗口生产SHA、干净Git/HEAD与官方等价不可变image ID，避免重复重建索引。无公开测试断言/Gold/评分日志入模型。

B七字段合同逐字引用issue，fixture不得凭空捏造；source AST重分期保留target；literal容器对照保持元素/顺序/长度，未知状态不伪装静态证明。生产guard仅作来源证据，派生对照在原base两次执行失败则fixture拒绝STOP，不跑target/A；B明确abstain亦STOP。其他fixture/格式失败最多一次A，原controller v2保持合同oracle；value_relation不弱化。target两次稳定失败才锁定，随后Gold只判同一probe，不按Gold重选候选。

独立可信须同probe base稳定失败、Gold消除失败、issue可观察行为语义吻合；机器/人工审查分别记录，静态可比性不代替语义。固定3题≥2/3才另冻Agent repair小对照；负结果封存，不能后验补规则再称独立。3样本不证明完美或SOTA。sealed TEST/C5/Fresh30保持关闭。

模型deepseek-flash、non-thinking、temperature0，返回alias记录但无snapshot声明；最多6请求/每题2、输出3000、单题20000/整批60000provider tokens，实际usage+reserve守卫、SDK重试0；请求失败中断不续调。现场eligible可能<3但分母不减。新runner直接使用60000与分母3，不借用DEV的80000/12。

基础设施：仅官方token/manifest经127.0.0.1:7892，白名单/无redirect/无重试/9请求/2MB；mirror manifest/blob显式空代理直连，官方摘要须完全匹配；用户终端下载大文件，关闭VPN全局/TUN、Docker No proxy。下载不读Gold，admit/Gold独立grader-only；容器network none/pull never，不改宿主/镜像/VHD/tunnel配置。

统一入口`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_counterfactual_canary_v4`：`freeze-method`→`select`→`metadata`→`transport`→用户`download --timeout-per-image 21600`→`admit --timeout 900`→`public`→`preflight`→报告精确命令/模型/6请求/60000后`run`→独立`gold`→语义审查/封存。除run外零模型。输出counterfactual-canary-v4目录；旧三批原件保留，不调用旧入口。
