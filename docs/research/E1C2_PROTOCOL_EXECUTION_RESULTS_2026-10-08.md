# E1C2：协议→生产检索→真实Python→离线反馈，最新结果

## Material Passport

- 日期：2026-10-08；类型：已授权 OLD DEV 方法开发；状态：三阶段均 completed/sealed，质量门槛未过。
- 材料：仅公开 issue、exact-base 生产源码、自身无网络容器反馈。独立评分未执行；未读原测试/Gold；非 canary。
- 固定分母：DEV12、准入9、本轮两个 library 来源。三个小阶段不是新独立样本，不累计成6题，更不拼历史 best-of。
- 收据：[摘要及SHA](../../data/e1c_evaluation_2_protocol_pilot_results.json)；原始 response/probe/ledger/seal 留本机。

## 1. 真实推进与费用

| 阶段 | 实际调用 / provider tokens | 观察 | 结论 |
|---|---:|---|---|
| 协议 pilot | 2 / 5,997 | 两次合法JSON检索，两生产定义找到；后续请求按单调用上限拦截 | wrapper/真实内层decoder接线有效，不是复现成功 |
| 执行小阶段 | 5 / 20,914 | 真实Python进入容器；一题normal因setup receiver移出后NameError，另一题重复检索 | 代码格式已进步，正常对照未合格 |
| frontier保护小迭代 | 6 / 26,797 | 两题最终abstained；其中一题normal×2=0、target×2=1，实际自动取得Schema | 运行时补证链首次在本轮live触发，但公开fixture/语义资格仍unknown |

本轮新增合计 **13 calls / 53,708 provider tokens**。三阶段独立硬限20k/40k/40k，实际不超额；每题调用上限1/3/3，output2k、reserve1.4、未来首调用保护、retry0。上一80k试验16/53,212仍独立保留，不清零也不混算。本轮无新增合格候选、机器可信0、Agent修复0；未运行Gold，因此没有新的官方修复或Gold消除成绩。

## 2. 为什么现在仍未过关

1. **协议已接实链**：去可复制说明、closed wrapper、严格quote/Oracle/AST；实际 nested parser/messages/executor单测验证，正常还原 hooks。模型已输出真实 Python，不能继续把全部0归因格式。
2. **正常对照的编译缺陷已做预防**：原模型把不支持的请求参数放shared setup；原compiler移到target后control丢receiver。新source-backed绑定保护在真实执行前拒绝此类结构，不帮模型造正常对象；复杂控制流保守不认证。对前一真实失败的零调用回归通过。最新模型没有再次走该错误结构，但弃权仍不算解决。
3. **自动补证确已live触发**：Marshmallow probe的两正常返回0、两target ValidationError返回1；Controller缺Schema，adapter取得对应生产定义。第三轮消息重组成的SHA与真实provider ledger prompt SHA完全一致，并含该窗口。输入原件不变；source取得不证明公开Foo继承、意图或完整行为。
4. **环境事实在本机，却没到模型**：三份执行记录一致标记missing_optional_import=dateutil；执行器只读挂载阻断模块，使control/target均导入失败。模型没看到此条件而弃权。新增 `environment_feedback.project_environment` 只投影matching、network_none/pull_never、有效运行记录，真实缓存零调用检查过；不声称自然卸载/实际guard值已观察、不授可信资格。**该投影尚未接入新付费producer**。
5. **接口请求被误判为不能测**：模型认为旧构造器没有请求参数便不能构造target；这是生成policy解释缺口。应允许公开明确请求的参数成为target失败入口，同时normal使用base支持的独立receiver，不能修改公共值、期待或调用入口来逃避问题。只证明参数接受也不证明默认值/增量行为等其他义务。

## 3. 接下来最短路线

1. 新未启动版本完整接 `project_environment` 到 execute反馈→compact Human消息，绑定生成前公开条件与执行后记录；正负测试检查一方不同条件/timeout/None均不可提升，记录事实不等于自然环境证明。
2. 同一方法加入任务无关的“feature request vs regression”说明：明确请求参数的base缺失可作为target现象；保留锁定期待、受支持normal与全部未覆盖义务。优先小额验证，不扩上下文和任务数。
3. 接入已有fixture scope/export/对象运行关系观察解决Foo/Schema来源unknown；只在真实身份和行为证据成立时升级有限资格。不得把静态unknown简单改True，或继续加入旁路collector冒充端到端改善。
4. **先2来源有效probe与资格，再同版四参考/九准入**：每次新方法/输入/预算freeze，精确命令/Flash/次数/≤100k预算公开后运行；不在started namespace重跑。有限子义务、重复base失败、Gold消除和完整可信分账。
5. 实际DEV门槛达成才全历史排除的新canary一次≥2/3，然后同版Agent patch/独立official grade、DEV30、另授权Fresh30/E2。不保证一周或30/30完美；未过就保留负结果回DEV，不消耗新独立样本调参。

## 4. 验证、安全与限制

新专项17项；Ruff、预算/V3重点及synthetic compact preflight ready=true。完整回归 **1653 passed / 4 skipped / 33 warnings，87.86秒**，XML SHA见收据；两次中间完整1642/1648的XML均保留。这些是工程验证，不是修复率。CLI只读核对第一次因import顺序缺agents失败，调整evals入口后通过；非付费重试。

新三seal分别11/39/52文件和方法SHA核验；旧201/255/54文件seal保持。全部失败/备份保留，未下载/删除镜像、未重启Docker、未改IPC/VHD/注册表/代理/tunnel/密钥；无API重试。canary/C5/TEST/Fresh30/privateTest500/Agent repair/E2仍关闭。研究执行规范使每批完整封存，最小改动规范使预算/检索/容器复用；没有新框架或依赖。
