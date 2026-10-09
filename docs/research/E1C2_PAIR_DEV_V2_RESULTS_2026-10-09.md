# DEV v2 已完成：另一旧 DEV 官方修复成功，引用锚仍是生成门槛

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-09
- Verification Status: UNVERIFIED（执行/独立官方评分收据核对，未独立重新生成）
- Version Label: pair_dev_v2_results_v1

## 1. 输入与真实执行

本轮先正式实现并冻结[DEV v2协议](E1C2_PAIR_DEV_V2_PROTOCOL_2026-10-09.md)，不是改原frozen源：响应在编译前做精确metadata兼容，raw/usage/canonical分别保存；拒绝probe改导入namespace制造条件，构造后的对象参数仍允许。已有Flash/budget/严格编译/离线执行/显式row-root独立评分函数复用，无新依赖或全局OUT/preflight重定向。

零调用按统一检索/限定名/global方法重建DEV12：**9份输入ready且既有双准入通过；3份PyVista缺本机source/issue，INFRA_BLOCKED**。固定12行保留，不拉镜像/复制源码或下载。逐window/source/issue Git blob/metadata/准入摘要/hash绑定；不是9题模型试验或9/12修复率。

按原frozen顺序排除上批所有已尝试两题、每repo第一ready且已准入，选Scikit-learn-26289与Marshmallow-1359。它们仍是已经参与其他开发方法的旧DEV，不是独立canary。输入/首消息SHA/源码/decoder/协议/预算全freeze，engine/images只读检查通过。

用户精确授权后一次执行：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_pair_dev_v2 run
```

完成约127.14秒。**Flash3calls/42,666 tokens**＝input13,537+output29,129，三次finish stop，实际enabled/high/no-tools、20k生成/HTTP300、SDK retry0。原最多4calls/100k预算未扩、未用余量补请求；不存在未知收费。MM repair output19,556（reasoning19,494），20k窗口接近用满；不自动扩大预算或改effort。

## 2. 同版固定两题结果

| 来源 | 本轮执行结果 | 独立官方 | 成本 |
|---|---|---|---:|
| Scikit-learn-26289 | 新pair JSON完整，但issue_quote拼接标题/省略号/trace，不是原文连续span；严格拒绝，未执行probe或调用repair | not_attempted，无补丁评分 | 1call/7,592 |
| Marshmallow-1359 | 新normal×2过、target×2稳定失败；一条新模型patch、相同normal/target各两次post过 | F2P1/1、P2P76/76、源/log有效、rc0、resolved | 2calls/35,074 |

**本版pair操作门槛1/2、official resolved1/2。** SK是生成证据锚拒绝，不是容器故障或官方测试失败。MM新patch把DateTime绑定读取从当前container的opts转为root schema的opts，修复List/Tuple内层字段问题；源码仅模型自行生成，不人工编辑、不改probe/断言，评分答案/Gold不进入actor。整个producer seal并核验freeze后才独立评分，不回流official反馈。

本次repair原本就是仅edits，canonical removed=false；实际执行兼容路径已事前接通，但**不能宣称本轮观察到了metadata兼容带来的因果准确率提升**。namespace检查也不替代完整语义证书，full_issue_trusted保持false。

前版原1/2与后验另1/1保留。本轮再有一个不同旧DEV成功；两个不同版本不拼同版最佳率、不叫DEV12/30全过。核心研究仍未完成。

## 3. 当前根因与已实现的零模型下一步

SK不是JSON envelope失败，也未观察其程序行为；它在执行前因“复制引用”错误被拒。不能事后人工改issue_quote、放宽verbatim约束或借未使用的第4次额度重试原身份。

新增小型`evals/e1c_evaluation_2_issue_anchor_codec.py`原型：**调用前**从公开投影issue按固定行序生成最多12个连续片段（每片≤300字符），绑定issue SHA与char offsets/片段SHA/稳定ID；未来模型返回 `issue_anchor_id`，解码器只按已冻结ID映射原文、normal/target字符串完全不改。未知ID/改registry/额外quote键拒绝，不对旧输出做最长匹配或事后纠正。5专项含实际接旧pair静态validator通过；假fixture，无模型/容器调用。

它只解决文本来源可追踪和复制格式错误，**不证明所选片段语义正确或覆盖完整公开意图**。目前仅原型/零模型接线，尚未纳入新的完整live方法/预算freeze，不能假称已在真实模型中修复SK或是V2分数。

## 4. 唯一后续路径

1. 把事前evidence ID表/模型输出schema/解码与预算正式接入下一完整方法；在实际请求中提供同一冻结registry，验证返回ID→原文→原probe校验链，不能改已运行V2源或quote。
2. 先旧DEV核算语义义务与缺证，确认正常控制/目标程序不是另一问题；校验新schema与预算是否足够，新paid需新精确命令授权。当前无可直接重跑命令，不换namespace暗中retry。
3. 再同版固定DEV12/九准入与完整费用冻结；未准入/未调用/预算停止都列明，不藏多个100k子批总额。新独立canary≥2/3门槛过后才独立修复对照、旧DEV与另授权Fresh30/E2。

不打开canary/C5/sealed TEST/Fresh30/privateTest500，不保证30/30、任何n/30或一周完美。已有输入9ready不等于语义/修复验收过关。

## 5. 验证与保全

10个V2专项/Ruff/预算V3重点29/合成compact preflight通过；首次全1779passed/4skipped/33warnings66.79秒。增加5个anchor原型专项后最终工程回归见[真实结果收据](../../data/e1c_evaluation_2_pair_dev_v2_results.json)；工程数不是修复率。原XML/readiness/所有失败/方法/输入/预算/ledger/seal不改，producer与旧paid封存已核对。

本轮零下载/删除/Docker重启、未动IPC/VHD/registry/proxy/tunnel/key。Cloud可跑源码单测，缺本机私有input/image/grader材料报INFRA_BLOCKED；未扩tunnel白名单或证明新远程live接线，不上传raw/Gold/key。当前两次两来源真实批次合计7calls/82,636 tokens，仅这两批费用，不是项目总费用或单批预算。过程只记集中日志。
