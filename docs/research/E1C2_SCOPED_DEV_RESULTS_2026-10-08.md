# Scoped DEV：真实三次Flash调用、中断原因与零调用修复

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: VERIFIED（零调用管道/消息回路）；真实整批INTERRUPTED
- Version Label: scoped_dev_results_v1

[完整哈希与预算收据](../../data/e1c_evaluation_2_scoped_dev_results.json) · [Scope协议](E1C2_SCOPED_CONTROLLER_PROTOCOL_2026-10-08.md) · [真实试验协议](E1C2_SCOPED_DEV_TRIAL_PROTOCOL_2026-10-08.md) · [反馈修复协议](E1C2_FEEDBACK_PROJECTION_PROTOCOL_2026-10-08.md)。

## 1. 本轮实质进展

参数声明不再只按函数名取同文件的多个同名构造器：精确冻结header行号+AST owner唯一绑定；缺/错行号或owner不符保持unknown、不给声明。class/guard/nested helper不当函数参数证书，生产host SHA/LF/base blob照旧验证。目标API意图不因定义来源唯一而自动获证。

新scope action gate真正接实际Controller：程序/行为unknown返回 `ACQUIRE_EVIDENCE_OR_ABSTAIN` 而不是提前保存终局candidate；最多两个源自未暴露production绑定的symbol检索建议。oracle/raw candidate/原执行保留；支持子义务或conditional report只能独立DEV评分，repair/canary/full issue仍false。

新身份两类真实正常正例、真实合成构造参数失败分支通过；正/负只是plumbing，非真实task成绩。四份既有qualification-v3/behavior缓存SHA核验后shadow audit：3份DEV-grade-only、1份补证/弃答、0修复权限，不回填旧资格或当新生成。

## 2. 新真实试验的实际结果

命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_scoped_dev_trial run`。模型及provider返回标识均deepseek-flash；预算50000/单题24000/output2000、最多16请求、retry0，首请求保护37737。只旧DEV四参考，不新canary。

| 任务 | 本轮调用/token | 实际状态 | 不可升级的结论 |
|---|---:|---|---|
| SK13496 | 1 / 3908 | 两次normal通过、两次target失败、真实observer/qualification；Boolean构造参数子义务候选 | default/增量/完整issue未证明；未Gold评分/不是repair |
| SK26289 | 2 / 9798 | 新gate要求补DecisionTreeClassifier生产依赖，阻止terminal选择；第三请求前中断 | 不是task失败/不计resolved0；public对照仍conditional |
| MM1252 | 0 / 0 | 未开始 | 不填0分 |
| MM1359 | 0 / 0 | 未开始 | 不借旧版本诊断当新输出 |

合计3真实完成请求/13706tokens，ledger6条started/completed，未超预算/无请求retry。state为`interrupted_no_auto_retry`、仅1完成row；整批成绩=null。固定DEV12/九准入/screen4不变，新Gold成绩=null，全issue machine trusted0。原Gold4/4/异常3/4仍是之前的独立记录，不覆盖或与本轮拼分。

## 3. 为什么中断，以及修复验证了什么

第二题unknown被新gate抑制terminal选择后，原链终于需要把selected-but-uncertified诊断送入下一轮messages。qualification/behavior各带本地`Gold_used: false`标记，serialized marker规则看到字段名便抛BlindBoundaryViolation。是METHOD_FEEDBACK_METADATA_BOUNDARY_COLLISION，不是Docker/网络/余额错误；没有实际Gold读取或泄漏。正/负synthetic smoke的terminal模式未覆盖这一非终局下一消息，是本次真实试验暴露的覆盖缺口。

不改任何已冻scope/trial/boundary源。不再调用或重试旧trial；新增零调用投影，仅移除两个已知schema中严格为False的诊断键。true/null/0/字符串/未知schema拒绝，其他位置marker或真实Gold文本仍由原边界拒绝；不做全字符串清洗，unknown/scope/oracle/原观察不变。

对原失败feedback的实际roundtrip一次通过：source/state/ledger SHA先冻结，核验production route，进入所有实际messages层，最终Human JSON14857字符通过原边界；nested projection hook存在，补证要求未变。新container/provider/tokens/Gold读取均0。结果只证明这份反馈可安全进入下一消息，不是原试验已恢复，也不是新付费producer已冻。

## 4. 安全、工程与可接手入口

31新增专项（scope15/trial6/projection10）；最终重点50/Ruff/合成compact preflight ready=true，完整1598 passed/4 skipped/33warnings、82.09秒。先前1588/117.56秒XML也保留。pytest不是repair rate。

原producer201产物与qualified/scoped/trial三个冻结method SHA均匹配，原中断state/ledger在零修复后未变。无镜像下载/删除/Docker重启/IPC/VHD/registry/代理/tunnel/key修改。raw/probe/输出/Gold/密钥本机保全，不上Git；仅源/专项/协议/脱敏收据公开。不打开TEST/C5/Fresh30或新canary，E1-C未封板、E2未启动。

当前Cloud可执行[交接](NEXT_SESSION_HANDOFF.md)中的零模型tests，不能直接run旧trial或gold（未complete/seal）。新增代码不自动扩bridge白名单或授予Docker裸访问；缺私有原prefix/镜像/credentials时明确INFRA_BLOCKED。

## 5. 下一步：只续接未调用步骤，不能整批重跑

1. 获得中断后续接决定；先写新resume-only协议/source/身份，不原地改scope/trial或绕过started guard。现无可直接执行的resume CLI。
2. 冻结原3已完成请求/1完成row、第二题两份response/非终局feedback、source/image/base/oracle及全部prefix SHA。保留原失败，严格区分缓存prefix与新模型调用；不重新执行原probe/container或付费请求。
3. 把投影纳入完整新method freeze；零调用验证原第二题第三轮消息与预算，最后列精确付费命令。最多再36294tokens（累计≤50000）；当前SK26289最多2未调用轮次/14202tokens、另两题各最多4请求/24000，全新请求最多10。首请求保护和全局余额同时检查，不能改run_id重置已用额度。
4. 只推进未调用步骤；结束后新prefix-aware完整producer seal才独立Gold，原试验仍INTERRUPTED。已完成第一题复用须证明原始byte/probe/image/评分范围，不叫新生成，不best-of。
5. 真实结果再决定按需production依赖/paired input/object/版本witness的通用接线。限定证据与完整issue覆盖分账；如果覆盖不达标，不扩canary/DEV30，回DEV改方法另版冻结。
6. 真正达到预注册质量门槛才历史全排除新canary一次≥2/3，再Agent patch/official、DEV30、另授权Fresh30/E2。无法预先保证30/30或一周完美。
