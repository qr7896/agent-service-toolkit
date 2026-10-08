# Controller 实际接线：零调用结果与剩余门槛

日期：2026-10-08。[冻结协议](E1C2_QUALIFIED_CONTROLLER_V1_PROTOCOL_2026-10-08.md) · [脱敏哈希收据](../../data/e1c_evaluation_2_qualified_controller_results.json)。

## 本轮完成

已有 Parameters 声明、程序结构资格、公开期待锚、异常 observer、有限行为判别正式接到新 Controller；真实嵌套 runner hook 单测确认没有被内部配置覆盖。复用原 compiler、oracle lock、预算和执行器，未改旧冻结源码，不新增依赖或独立 collector。

真实容器正例验证已完成：sklearn 和 Marshmallow 两组合成公开 regression issue，retrieve→probe→abstain。每组 normal 两次 rc0，target 一次 rc0（通过后不需要第二次失败确认），Controller admission 与 post-verdict 留存，反馈被下一轮消费，均未选作故障。原 issue 的 fixture 义务不进入合成 issue。2/2 是管道正例，不是两个 benchmark 成功或修复率。

adapter/source/protocol/输入/预算已冻结在 `qualified-controller-dev-v1`，smoke 已封存在 `qualified-controller-zero-smoke-v1`；均不重跑或原地改源。固定DEV12/九准入/screen4分别保留。Flash候选预算为最多16次调用、整批50,000/单任务24,000 tokens、retry0，首轮预留合计36,101。CLI 只开放 smoke/freeze，`real_provider_run_enabled=false`，并未形成可执行的新付费 producer 命令。

11新增专项、重点30项、Ruff及合成compact preflight ready=true；完整1561 passed/4 skipped/33 warnings，118.45秒，XML SHA见收据。前置 mock test 曾因 Behavior 的 git_blob 未 mock 而1 failed/9 passed；仅补同一合成源的 canonical mock，原断言未改，后10/10再11/11通过。此失败在任何研究 freeze 前，不是 task 失败。工程计数不算复现/修复率。

## 结果不变与安全

本轮新增模型调用/token 0/0，E1-C Gold读取0、新镜像下载0。原producer seal及201个产物摘要全部未变，所有本轮冻结模块SHA未变。旧Gold4/4、异常对应3/4、资格分类、MM1359历史版本单点实证均保持；全issue machine trusted仍0。

仅普通无网络容器；不重启Docker、不改IPC/VHD/registry/代理/tunnel/key，不删除旧记录。源/专项/协议/收据公开；raw输入/probe/driver/log/Gold/测试答案/key留本机。V3 mandatory synthetic plumbing检查与本轮E1-C材料分账。

## 后续同轮追加：真实 selected-candidate 分支通过

按[独立零调用验证协议](E1C2_CONTROLLER_FAILURE_SMOKE_PROTOCOL_2026-10-08.md)，没有改Controller v1，用新 `qualified-controller-failure-smoke-v1` 身份一次完成合成构造参数请求反例。retrieve自动定位构造方法；normal×2 rc0、target×2 rc1、实际observer rc1，Controller qualification=`mechanism_supported_candidate`且无unknown、有限Boolean子义务支持。完整issue trusted仍false。6新增反例验收单测与重点36项通过，全部provider/tokens0/0、无Gold。

此结果解除了“真实selected分支未触发”的管道缺口，原正常smoke结果不回填。合成故障不是benchmark新生成、不是原公开issue或三个真实任务成功，也不把该参数名加入真实task规则。结果/driver/protocol/freeze/observation/verdict SHA见同一收据。

最终完整回归1567 passed/4 skipped/33warnings、102.02秒，新XML SHA见收据`final_regression`；前1561 XML与结果保留。所有冻结method/新driver/两protocol和原201产物摘要再次匹配。两Roadmap/交接反映此最终状态。

## 尚未完成与唯一下一步

1. Controller正常/失败实际分支均已完成有限验收；不重跑三个smoke/freeze namespace，不在旧v1改源。此处不再重复扩管道或运行同类示例。
2. 定义 `full issue / sub-obligation / conditional hypothesis / unknown` 与明确剩余义务的动作gate；未暴露辅助依赖须有界取得或保持unknown。最多两个文件不是完整动态依赖证明。

   参数声明匹配在window缺owner元数据时仅按函数名匹配已核验文件，可能出现多个同名定义；这不是唯一target-API绑定证书。下一完整producer须按窗口行号/AST所属类验证唯一范围，不据这些声明授予语义可信；冻结v1不原地修补。
3. paired inputs、对象关系、历史witness尚未自动接入；仅按判别真正需要的证据接线，失败保留，不把已有旁路诊断当新模型产物。没有可用旧版本源就明确不可用。
4. 完整方法、输入、范围、预算和失败处理冻结后才新Flash旧DEV生成；先四参考有限screen，再九准入，固定12分母、Gold/有限候选/语义/原机制分账。
5. DEV门槛真正通过才选历史全排除的新canary一次≥2/3；再Agent写补丁/独立official，旧DEV30与另授权Fresh30/E2。当前不抽第6批、不打开TEST/C5/Fresh30，不承诺30/30。

这是实际接线进展，不是E1-C evaluation_2封板。用户不需要下载任何新镜像。
