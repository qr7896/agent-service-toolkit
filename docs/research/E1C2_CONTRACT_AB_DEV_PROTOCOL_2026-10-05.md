# 旧DEV：固定行为合同与正对照的同预算A/B协议

日期：2026-10-05。第二批canary 0/3已封存，本实验只回到原DEV12的9条官方双准入任务，另外3条环境失败保留在分母12。本版本不读取两批canary的题面/候选，不在它们上重放或补规则。

## 方法与配对

两臂自动准备同一份新输入：原公开issue允许投影、exact-base生产源码；从已有定位索引增加公开API定义/生产traceback线索的覆盖优先级，最多四窗口、每窗口2500字符、总context≤23,000字符。仅扫描生产文件，测试/评分路径拒绝。定位不接收任务ID，标签仅用于目录/账本；覆盖字段只代表语法线索命中，不代表根因已定位。

A臂使用原v4提示风格、单次source生成。B臂使用独立system指令和DeepSeek官方JSON模式，返回逐字issue/expected跨度、固定oracle类别、setup、正对照调用、目标调用和可选值关系断言。call_completes由控制器生成到达检查；value_relation仅允许一个比较断言。引用核验/AST校验只能证明结构与来源，不自动证明语义符合；独立Gold/语义审核继续必要。

B先在同一不可变镜像中运行正对照两次。自建fixture或基线调用失败时不执行目标、不计候选；仅当两次正对照都通过才运行目标。正对照、target禁止catch/raise或setup中的断言，明显builtin dummy调用拒绝；静态检查不能完整证明对照与目标是同一API，需在结论中披露。目标两次重复失败后单独锁定候选，才由独立Gold区分。不会向本次生成回传Gold或官方评分结果。容器network=none、pull=never；可选依赖前提只按公开issue隔离。

两臂都使用typed source/abstain/非法响应分类。A不走确定性构造路由，9题全部模型生成；这是v4风格的当轮匹配baseline，不是历史v4的逐字重跑。B是多组件treatment，若有增益不能仅归因JSON或定位。历史4/12只作历史参照，不拼接成功数。

## 冻结、预算与停止

每臂独立run身份 `e1c2-contract-ab-dev-v1-a/b`，每题各一次Flash请求，单题12,000、每臂90,000 provider tokens、单输出3000、temperature0、non-thinking、SDK retries0。两臂输入、候选数、模型与硬预算相同，提示长度不同导致预留不同，实际token成本单列。不使用Pro、训练或新下载。本轮最多18请求、两个单实验分别≤100,000；A/B中断原身份不自动重试或增加预算。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev preflight --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev preflight --arm B
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev run --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev run --arm B
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev gold --arm A
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_contract_ab_dev gold --arm B
```

preflight锁定源码/协议/输入/提示/镜像/预算，费用命令先向用户列明，按既有单实验≤100,000的权限执行。任何provider错误记录后中断，不自动重试；来源/身份/镜像错误原位停止，不替换任务。原DEV/两批canary记录保留。

主结果为固定DEV12逐题可信复现差、无依据/fixture失败数、正对照通过、弃答类别与实际tokens。小样本只做描述性配对，不宣称显著性或SOTA。B至少保留A的可信任务且有≥1新增可信，或在可信数不降低时明显降低无依据候选/成本，才考虑选择；否则封存无增益，不能扩新canary。即使DEV通过，新方法仍须完整先冻，再选不重叠新canary固定分母≥2/3；repair/TEST/Fresh30继续按门槛推进。

JSON模式依据：[DeepSeek官方JSON说明](https://api-docs.deepseek.com/guides/json_mode/)，文档提示仍可能返回空内容，本实验不因此重试。
