# Scoped resume：已完成封存与评分，质量门槛尚未通过

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: VERIFIED（续接/封存/独立评分）；质量未达标
- Version Label: scoped_resume_results_v1

[收据与原始摘要](../../data/e1c_evaluation_2_scoped_resume_results.json) · [续接协议](E1C2_SCOPED_RESUME_PROTOCOL_2026-10-08.md) · [依赖反馈修复协议](E1C2_DEPENDENCY_FEEDBACK_PROTOCOL_2026-10-08.md)。

## 1. 已完成的授权范围

用户明确允许只续接未调用步骤。新resume身份冻结原109文件、完整method/投影/协议、source/image/base/Oracle与账本；实际零调用smoke重建两缓存轮次，第三轮消息通过，0新probe/container/模型。原1完成row及candidate/probe字节复用，明确不叫新生成；第二题两次原请求仅缓存AIMessage回放，旧probe执行被硬阻断，原Oracle和输入逐项比较。原trial仍INTERRUPTED且所有109文件未改。

新账本复制原6事件字节前缀并沿用原ledger_run_id记消费；不通过改run_id清零预算。保留累计50000/task24000/max4calls/task/output2000/retry0与未来首请求保护。新运行真实完成7请求/29996tokens，加旧3请求/13706，共10请求/43702，剩6298；无未结/重复请求。四screen行全部得到终局状态，新generation seal绑定255产物，完成后才独立Gold。seal完成不代表四题通过或E1-C全部完成。

## 2. 逐题结果与独立评分

| 任务 | 模型请求与token | 终局 | 独立评分 / 限制 |
|---|---:|---|---|
| SK13496 | 复用旧1 / 3908；新增0 | 原完成prefix，Boolean子义务候选 | Gold施加后rc0，消除通过；不是新生成/Agent repair或完整issue证书 |
| SK26289 | 旧2+新1；累计15351 | 下一第四请求task reserve不足 | 15351+11985>24000，未调用；第三轮正常target通过但未形成故障候选 |
| MM1252 | 新3 / 12498 | 下一第四请求protected global reserve不足 | 31757+10154>41520，未调用；已执行候选因生产依赖未暴露而unknown，不独立评分 |
| MM1359 | 新3 / 11945 | repeated-unsuccessful-action stop | 三轮normal control失败，下一重复动作不再付费；不是已验证目标bug失败 |

只有1个复用prefix候选进入独立Gold，1/1消除通过；固定screen4中为1个Gold候选，新增生成的合格候选0。全issue machine trusted仍0，Agent patch/official resolved未做。不得称“新生成1/4成功”“repair1/4”或把旧Gold4/4拼入当前；预算与控制失败也不是任务正确率。

## 3. 实证瓶颈与零调用修复

1. **预算按reserve停机**：两个任务实际未用满预算，但下一请求保守预留不符合task或保护未来首请求的global ceiling。不能通过增timeout/预算/放宽断言获得绿灯。下一版先去掉重复诊断/context内容，实测保留全部必需证据的prompt reserve再决定新预算。
2. **缺证分支丢提示**：MM1252尚无production binding，observer未创建，verdict.program有未暴露Schema，但action_gate只从qualification.program_evidence取建议，三个真实反馈都是空requests。新route只把该program转为unknown/rejected资格视图，复用已有gate；原拒绝/未知保留，不支持repair/trust。4专项后对已封存三反馈做新shadow audit，Schema检索建议均恢复。0模型/容器/Gold读，不改旧结果。尚未接future live，不能声称模型已采用修复。
3. **策略未落实补证**：SK26289第三轮没有落实先前DecisionTreeClassifier检索建议，改为新probe，target通过。原轮次的public argument为Name、公开fixture事实为空，新probe自身feature-name绑定为List；这不证明原问题解决，也不能仅据此断言公开原始输入一定是哪种容器。下一版明确pending source acquisition和失败假设类型约束，不能把改输入获得pass当bug修复。
4. **控制/范围仍不足**：MM1359重复normal失败；MM1252公共namespace/fixture与Schema定位未闭合。完整issue承诺、输入状态、source/version witness仍分账，不借先前旧版诊断或Gold去补本轮证明。

## 4. 接下来按顺序推进

1. 新完整producer接入已验dependency route，未知依赖自动有界production-symbol检索（无人工文件表）；保留SHA、重复/总读取预算。只增强建议不够，需验证实际执行/返回窗口。
2. 把过长消息与动作历史问题一并处理：压缩重复身份诊断，不损失rejected/unknown/原期待与公开source；按实际prior action给消息，不能在先前是probe时仍说“检索已完成”。用两份预算停止实际上下文做零调用reserve验收。
3. 正负例/完整source/预算freeze后再单版DEV。当前原50000预算只剩6298、已完成所有授权续接；不再直接run/gold当前namespace，不自动追加新付费批次。任何新实验先列命令/Flash/调用次数/预算，保留当前负结果。
4. 四参考有限范围质量闭合后，才完整九准入DEV/native（固定12分母），再未参与调参新canary≥2/3。之后才Agent patch/独立official、DEV30、另授权Fresh30/E2。当前没有可信gate或新canary/repair命令，不能保证30/30或一周完美。

## 5. 保全与工程

原109中断prefix、原更早201producer文件和全部frozen method保持，原state/ledger无改，新ledger旧事件前缀逐字节同一。smoke/dependency诊断无新容器；评分只独立隔离容器。无下载/删除/系统Docker重启/IPC/VHD/registry/代理/tunnel/key修改，TEST/C5/Fresh30仍关闭。raw/probe/Gold/key留本机，公开安全源/专项/协议/脱敏收据。

新增resume13+router4共17专项，重点36/Ruff/合成preflight通过，初完整1611passed/4skipped/33warnings87.85秒XML保留；最终1615passed/4skipped/33warnings79.10秒/XML SHA见收据final_regression，不算研究成功率。[WebCodex交接](NEXT_SESSION_HANDOFF.md)只给安全检查与新method待办，不让云端误重跑已封存实验。
