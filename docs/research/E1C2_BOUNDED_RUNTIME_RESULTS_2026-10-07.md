# 新受限运行反馈路线：真实试验结果与下一步

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent; implementation: ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: VERIFIED（仅这些真实运行/账本/工程结果，不表示研究目标已达成）
- Version Label: bounded-runtime-results-20261007

## 结果

新路线已从静态一次生成推进到受限生产retrieve/read、正控制、自己执行反馈与实际上一动作历史。**仍未产生合格候选，不能开启新canary/Agent repair/Fresh30/E2，也没有非公开断言、非人工定位30/30结果。** 原所有方法、输入、响应、预算、账本和negative不改。

| 版本 | 真实调用 / tokens | 结果 | 独立Gold评分 |
|---|---|---|---|
| v1 | 12 / 24976 | 模型附固定json_object格式标记，单键动作parser拒绝；三题turn_limit | attempted0，没有评分容器执行 |
| v2 | 0 / 0 | 仅typed动作codec、单测和真实合成smoke；未正确兼容实际格式标记，未freeze/run | 未运行 |
| v3 | 6 / 13341 | 格式正确，两个任务找到生产定义，但各重复query一次被无信息增益规则停下 | attempted0，没有评分容器执行 |
| v4 | 11 / 32660 | 真实上一动作/观察与末尾轮次请求后，模型已产生probe/使用真实控制反馈；三题仍不合格 | attempted0，没有评分容器执行 |

这些均为**旧DEV三仓库screen**，原DEV分母12不变、screen分母3，另外任务未运行，不能包装成整版DEV12或独立验证。v1工程接线失败不代表三个软件任务均不能复现；v4无有效candidate也不是Agent patch失败。所有自动trusted=false；不拼best-of。

本轮新增真实29请求/70977provider tokens，无provider失败/自动重试。v1/v3/v4费用分账，v2零费；三批总上限98317，实际未借额度。10月5日起可见usage375466（含旧SDK错误4281、非账单核验），不是整个项目/账单总量。仅使用deepseek-flash，没有Pro。各batch provider失败/余额/网络错误均中止而非重试。

## v4逐项瓶颈

- SK13496：retrieve真实IsolationForest.fit→read→probe，生成的value_relation未满足原一条comparison assert合同。已消费9913，余10087；下一次实际conversation的保守reserve10700，故在发请求前停。不是API没有响应。一次诊断误带入上一invalid probe为previous字段，随后按实际previous=None重算，公开收据只记正确数。不能削弱预算guard、增加旧freeze额度或补跑第4次。
- MM1252：probe→生产read→两次probe修订。控制共同程序已在DateTime Z load抛ValidationError，两次control均失败，target不得执行。反馈已真实进入下一调用，但未建立正常输入与故障触发的分离。这不是通过了原可信复现，也不能靠人工改日期或Gold答案补控。
- pytest7432：错误owner限定检索无结果，转plain Skipped找到生产定义，再read；最后生成代码语法不成立，被执行前拦住。受限native fixture边界仍未实现，不能拿FakeItem或放开pytest.main/全仓test发现来凑成功。

## 有实证的进展和未证明的东西

各新namespace真实无网络/只读/pull-never合成smoke均完成：scikit-learn/MM普通API controls两次通过、通过target不算bug、fake模型消费真实观察后弃答。这是人工编写synthetic fixtures的控制器验收，不是模型自动做对任务。新格式codec对原12缓存仅做解码，9retrieve/3probe，不是新复现分数。v4真实上一action/feedback原件接Assistant/Human数据、explicit turn请求后不再单纯重复同query；无收益于可信候选的证据，不能据此宣称算法效果提升。

最新完整工程单次1243passed/4skipped/33warnings/0failed（56.86秒），持久XML1247tests；重点50passed、Ruff通过，规定V3 compact preflight ready=true。没削弱旧断言/skip/timeout，工程数不是repair率。

## 接下来只做零调用根因验证，停止本轮付费扩批

1. **执行前置/故障边界：** 根据自己生成脚本的trace位置→生成AST语句，区分“合法fixture构造”与“实际被报告的API调用”。证明诊断/前沿移动保持完整target程序AST与oracle不变；source proof不够留unknown。不能按任务名或手选文件修日期/输入维度。先在合成与旧DEV证明两次正常控制通过、真正行为差异可观察，再考虑下一实验。
2. **预算与信息增益：** 压缩重复源码窗口/上一probe重复载荷，用hash保持来源、保留issue义务与oracle；先报告实际reserve与信息损失对照。不要因为任务未过就下调保守reserve，或向旧账本借预算。
3. **生成语法与受限fixture：** 在零调用记录上验证哪个合同字段不合法，统一明示代码块/AST格式。若要支持pytest业务，另建仅运行自己生成临时文件、禁existing test/conftest/默认发现的可信适配器；冻结前不解除原guard。它是未完成能力，不能说本轮已经支持。
4. 上述原型的跨仓库/四参考质量证据与完整回归达标后，再另冻同版旧DEV方法/预算。三题screen不足以保四参考，不直接扩大canary。开发有收益才完整旧DEV和不重叠独立canary≥2/3，再另冻Agent repair，最后同版对照/新任务一次性测试。未过则如实封存，不无限收费循环，不承诺一周30/30。

## 产物、安全与接手

本机原件分别`.codex/e1c/evaluation_2/bounded-runtime-dev-v1/`、`v3/`、`v4/`（实际完整目录名含bounded-runtime-dev前缀），均已state completed和generation seal；全部preflight/run/gold为历史，**禁止再执行**。v2只有真实zero-smoke，无paid run。公开摘要：[v1](../../data/e1c_evaluation_2_bounded_runtime_v1_result.json)、[v3](../../data/e1c_evaluation_2_bounded_runtime_v3_result.json)、[v4](../../data/e1c_evaluation_2_bounded_runtime_v4_result.json)，SHA绑定原state/ledger/freeze/seal，原响应/评分材料不上传。

Docker初始旧IPC失败；本轮用户明确授权后正常stop、只备份两个精确IPC目录（后缀ipc-backup-20261007-081928），普通start一次成功；全12immutable images已真实核验。所有历史备份/源码/记录保留；无镜像下载/删除、VHD/registry/代理/tunnel/key改动，不声称Web私有连接端到端已验。Cloud可接上述源码/单测/零调用分析；缺本机source/image/runtime必须INFRA_BLOCKED，不索要key或开放裸daemon，新paid入口未添加到原tunnel白名单。
