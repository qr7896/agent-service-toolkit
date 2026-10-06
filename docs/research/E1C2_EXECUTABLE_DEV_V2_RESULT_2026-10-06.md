# Executable DEV V2：3/12与零付费兼容诊断

## Material Passport

2026-10-06。原DEV12开发、九题准入，非独立确认。用户准许正常停机同次备份两个IPC目录，13:58:13备份run与docker-secrets-engine后普通启动成功；真实engine/DEV12全12与现有bridge docker_status均健康，Docker29.4.0。未动VHD/代理/tunnel/密钥、未重新下载15个旧canary缓存。Web端到端连接未验证。

## 新生成真实结果

方法源码0cebf87已提交、V2现场新freeze c56411f586fbfcb59891f82fef1da7bc5aa81c8d308bb276ee694bdee5c75737；固定12/九题、Flash最多18/80000/每题20000/输出3000、primary reserve70519。先展示精确executable_dev run命令/模型/次数/预算后按已有≤100000许可一次运行。12请求36689tokens，全完成、无provider失败/重试。

四个稳定base候选（warm_start、Lasso、ISO-Z、generator）Gold三真一假；机器trusted仍false。**Gold3/12，未保原四参考，开发门槛失败，不抽第6批、不启动repair/E2/TEST/Fresh30。** 语义审核尚未逐项完成，不将Gold3称全自动可信。原5/12只是此前开发版本结果，不能best-of合并。[公开封存与SHA](../../data/e1c_evaluation_2_executable_dev_v2_result.json)。

失败分布：array与List(DateTime)回退A响应不是源代码，而是只有issue/windows键的输入回显；原B分别base通过/quote未落在允许issue内。三pytest任务按不支持native fixtures或公开可观察行为不足弃答；generator仍Gold后失败。它们不由网络/额度不足造成，不更换任务、不把未准入三项移出分母。

## 零付费机制诊断

新增controller_manifest将执行元数据从模型输出格式中分离：只接受旧source/七合同字段/弃答，唯一可忽略execution元数据，其他输入echo字段仍拒绝。普通direct或受限唯一零参同步入口由controller语法确定，仍拒绝未知fixtures/native API/I/O与非法入口，原oracle/counterfactual/STOP不变。原12响应逐字SHA、输入/方法逐项比较、cache-only dummy model不使用真实key，不发HTTP，新provider0、缺缓存0。新namespace完整回放同样Gold3/12；该负诊断封存，不能宣称提升，也不算新模型生成。所有原V2文件不变。

进一步只看被拒响应字段确认是issue/windows，不是已生成源码缺一个manifest；没有将source窗口或输入echo转换成候选。根因提示：旧A只有Human prompt，指令/大JSONcontext混在一起且可能后置facts；B有System且格式正常。新V4方案把可信A指令System、公开数据Human、末尾明确生成请求与固定输出schema，不把公开数据升为System。输入/窗口预算同版，controller-owned manifest和全部保护保留。此为待真实新生成验证的通用提示/协议修订，不是已证明输入echo必由角色安排导致；模型温度0也不能把观察当因果证据。

截至本轮可见usage231911+36689=268600（含旧SDK错误4281，非账单核验）。V3缓存0，不重复请求。下一完整新生成仅在源码/协议/回归/预算另冻、先列精确Flash命令后执行，不在旧源码上改freeze/补调用；支持可达性有限，不保证30/30。
