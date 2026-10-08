# 自动补证/合理context预算：新Flash旧DEV校准

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: UNVERIFIED（执行前）
- Version Label: acquisition_dev_v1

按用户最新要求，查[DeepSeek官方context规格](https://api-docs.deepseek.com/quick_start/pricing/)与[SWE-agent分层model配置](https://swe-agent.com/latest/reference/model_config/)，以本项目实际预算停止和零调用取得资料定新预算，而不是装满1M window。来源/取舍见[context协议](E1C2_ACQUISITION_CONTEXT_PROTOCOL_2026-10-08.md)。

完整新method：projector→program/q分支缺证route→Controller静态resolve import的production定义→host/LF/base SHA→最多2自动symbol/issue/base→effective overlay→下一messages/execute。初始输入不mutate，原probe资格不回填；未知/拒绝不提升。公开issue spans/facts/原期待/source/参数声明完整保留；system策略合并，重复原动作/反馈仅一次，实际prior-action不会错称retrieval。语义oracle、双normal/target、原compiler/scope gate与独立评分隔离保持。

zero-check旧身份因缓存compiler未物化在首次acquisition前停止，原source/freeze不改；新zero-resume view仅原SHA绑定缓存补齐，2真实生产依赖读取/下一Human暴露、两预算样本reserve下降均完成。新paid freeze核验完整zero method/协议/结果SHA，nested实际hook/预算专项先过。旧trial/resume/score/state/ledger/source保持，不复用旧费用为新样本，不best-of。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_acquisition_dev freeze
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_acquisition_dev run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_acquisition_dev gold
```

新namespace acquisition-context-flash-dev-v1；Flash非思考、temperature0、最多16请求/4task×4，整批硬限80000、单题软目标32000/可用闲置pool但硬限48000、input软目标12000/estimated硬限24000/output2000，字符安全限96000；保守预留multiplier1.4，未开始任务首请求保护，retry0。soft目标是提示性，不按soft硬停止；实际全局/token ledger才成本边界。上下文技术1M上限不代表实际消费。此批提升方法/context/预算多个因素，不能归因单一算法。

按用户明确单试验≤100000已授权且最新允许合理扩大context，本批≤80000；执行前会话列精确paid命令/模型/次数/上限。freeze/Gold=0provider，run不能自动重试，generation seal后才独立Gold，不回流模型。输入仅旧四参考公开issue/production source，不读测试/Gold/旧独立成绩；fixed12/九准入/screen4分账。取得source可用不代表full issue trusted，repair/canary权限false。

网络仅主机Flash API；容器network-none/pull-never、无新镜像下载/系统Docker/代理/tunnel/key修改。全部旧负记录与备份保留，raw/probe/Gold/key不上Git。未达质量gate不抽新canary、不打开TEST/C5/Fresh30，不保证30/30或一周完美。
