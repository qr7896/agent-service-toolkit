# Hybrid controller v2：独立 canary v3 预注册

## Material Passport

日期2026-10-05；类型：code experiment；当前任务身份未知；开发依据为旧DEV缓存回放4/12，包含人工语义审核；不是新模型实验成绩、不是独立泛化、不是修复率。原付费hybrid-v1为3/12，旧v4经审核4/12，不能宣称超过旧v4。生成与控制器方法见[完整附件](E1C2_HYBRID_CONTROLLER_V2_METHOD_2026-10-05.md)。

## 方法先冻，身份后选

先执行freeze-method，绑定完整方法、适配器、生成/评分隔离、预算以及开发证据SHA；再select。固定盐`e1c2-source-contract-hybrid-canary-v3-2026-10-05`；从既有冻结metadata池按repo再task的SHA排序选择三个仓库各一题。排除DEV12、原DEV30、两批canary、污染ledger与历史cohort/manifest/identity。只读身份metadata，不看issue/答案选题；分母3，无替补，下载或环境失败不换题。未知任务内容不得用于修改方法。

生成只读允许issue投影与exact-base生产源码；production coverage自动选四窗口，每窗2500字符/context≤23000，记录SHA。实际源码import恢复公开的缺可选包前提，不使用测试正文。B生成七字段合同，逐字issue引用和oracle固定；生产AST可证明的构造目标重分期保持程序AST不变；两次正对照后两次base执行。首次稳定失败即锁定；否则最多一次A回退。若B合同为call_completes且A满足严格结构证明，controller到达检查替代其多余返回值断言；value_relation不得降级。Gold只在选定后由独立grader判别，失败不得回头选其他候选。跨度检查和AST证明不自动替代语义审查。

## 基础设施与预算

官方Docker token/manifest仅经127.0.0.1:7892，URL白名单、无跳转、无重试、9请求/2MB累计响应正文上限；镜像manifest与层走显式空代理直连，官方/mirror摘要必须一致。大文件由用户终端下载，关闭VPN全局及TUN、Docker No proxy；空ProxyHandler不能绕过系统级TUN。先完成官方离线Base/Gold双准入，再物化公开输入。Gold材料留grader-only，不输入模型。

冻结模型deepseek-flash（服务返回alias记录，不声称不可变版本快照）、non-thinking、temperature0；最多6请求/每题2次，单请求输出3000，单题provider tokens≤20000、整批≤60000。在线实际用量+下一请求reserve守卫；不借预算、不自动重试、不在失败后增加上限。请求错误中断封存。运行前须报告精确命令/模型/次数/上限；用户已有单实验≤100000许可，不自动扩大系列累计预算。

## 判别与停止

同一不可变image ID、network none、pull never；两次base稳定非setup失败、同一probe Gold消除失败、issue语义吻合才计可信。固定3题须≥2/3，人工审核后结果与机器结果分别报告。任意失败如实保留，未运行不算通过；失败封存，本批不得调参后重称独立。通过才另冻Agent补丁配对实验，官方评分判resolved；不开放sealed TEST/C5/Fresh30。≤3样本只能作为小型门槛，不证明完美泛化。

## 命令顺序

入口均为`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_canary_v3`，依次加：

1. `freeze-method` → `select` → `metadata` → `transport`（零模型；只取小型metadata）。
2. 用户：`download --timeout-per-image 21600`（下载进度/断点/摘要核验/导入心跳均复用原入口）。
3. `admit --timeout 900` → `public` → `preflight`（零模型）。
4. `run`（唯一付费命令；Flash≤6请求/60000 tokens，无重试）。
5. `gold`（独立离线评分，零模型）；汇总机器判别/语义审核/固定分母后封存。

执行路径`.codex/e1c/evaluation_2/hybrid-canary-v3/`；public/源码、live响应/账本、grader-only各自分区。GitHub仅同步代码、SHA、公摘要、协议，缺本机原件必须报告INFRA_BLOCKED，不复制密钥或评分答案。旧批目录、失败记录及冻结方法原封保留。
