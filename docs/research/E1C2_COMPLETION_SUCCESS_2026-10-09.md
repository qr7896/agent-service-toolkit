# 首个严格输入旧DEV模型修复成功，下一步转入从issue两来源验证

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-09
- Verification Status: UNVERIFIED（本次执行/独立评分收据核对，未独立重跑）
- Version Label: completion_success_v1

## 1. 获精确授权的真实模型试验

执行 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_thinking_completion_dev run`，完成、无retry。Flash enabled/high，生成上限24k、总上限40k；同v2严格组prompt SHA23e9624216d52f5de6519c066b90d6c07dd26bc379fb653baf18942c1e46b13f。

实际1call/19,840 provider tokens：input5,708、output14,132，其中reasoning13,897；最终JSON输出235tokens/729chars，finish_reason=stop。已核验实际wire mode/high/24k/no-tools与HTTP300；reasoning正文未保存/公开。模型自己生成一条生产编辑，去除ISO时区后缀再走既有小数秒解析；没有人工定位新文件或修改该补丁。

生成input/response/ledger/patch全seal后，独立无网络/no-pull容器official评分：**F2P1/1、P2P37/37、源身份/log有效、rc0、resolved=true**。与此前仅rc0而F2P0不同，这次实际目标确实通过。

这是**一个已经参与调参的旧DEV**，采用缓存自主检索窗口/自身probe/自产反例的修复校准；不是从issue重新完整生成、独立泛化、三组效应、30/30或canary gate。严格模型没输入现成测试断言或Gold，但shared准备为其他arm读base对象；不称整个进程未触碰测试。full_issue_trusted仍false，不能因official通过回填author namespace意图/全部语义证书。近期四次局部校准8calls/69,697tokens，仅这几次，不是项目全部费用。

## 2. 零调用补充验证与失败保全

在新的own-probes目录运行原control/target各两次，四次rc0、patch apply有效、同镜像/base/dateutil缺失条件；不改原probe、expectation或model patch，不读取official断言/Gold。

边界接线首次失败：修改sweep.OUT影响旧producer输入回查，尚未创建boundary目录；第二新dispatch在自身目录写freeze后，被legacy sweep当作started而停止，未启动任何矩阵容器。两个失败wrapper原源/记录/目录全部保留，不重跑、不修改冻结源。

第三个独立零调用身份`completion-public-sweep-zero-v3`在变更alias前验证paid完整snapshot，dispatch与未创建execution目录分离，完成首次真实边界批次：

| 同一组21个公开合成时间变体 | 完成 |
|---|---:|
| base | 6/21 |
| 新模型patch | 21/21 |
| 公开2.19.3包 | 21/21 |

此前10个条件反例在这个patch上消失。**21不是21个新task**；这里只比较完成/异常，不证明返回值等价。版本/path/manifest核验在phase driver，child继承同PYTHONPATH、非逐child attestation。原四次own probe未重播，provider0，所有paid/source SHA保持，旧0/3/8k截断结果不回填。

## 3. 下一步已经推进到哪里

零调用另从原两个已冻结library reference的**公开raw issue + exact-base clone**重新跑balanced structural/lexical检索，各4窗口；不使用旧effective windows/probe/patch/官方结果定位。这只完成fresh localization，不是模型生成或完整E2E。

检查发现SK四窗口含benchmark/example、bagging/forest，却漏掉题面字面`sklearn.ensemble.IsolationForest`本体。新通用规则只取反引号内合法限定名、最多4，静态解析production export/constructor/声明并核验host LF==base blob，无task-ID→文件表；实际补3窗口，SK变7窗口，找回iforest.py；BaseBagging/BaseForest未在该限定名下resolve，保留unknown，不猜文件。MM无此类限定名，仍4窗口。

`issue-qualified-reference-zero-v1`是检索补证，不授语义绑定/完整意图；附加输入尚须在下一整体模型方法里重建canonical身份，不能直接作为已获授权的paid命令。已做这些零调用推进，**本轮没有第二次模型调用**。

## 4. 接下来不可跳过的路线

1. 将fresh issue定位/限定名补证、必要依赖检索、probe/normal生成与公开自验证、patch写入与official评分接成同一方法；避免临时globals切换导致来源/输出耦合。所有最终messages和canonical身份在调用前核验。
2. 在两来源旧DEV先验证完整链（不沿用本次缓存补丁/定位作新从零结果）；明确输入/输出/推理和定位/probe成本，总预算冻结，先列精确Flash命令再授权。当前尚无新的完整paid命令，不能继续无限调这一题或直接抽新canary。
3. 通过后才扩固定12/九准入DEV；条件机制、完整可信、official resolved分别计；从issue方法真正稳定再整体freeze。
4. 所有历史已看task排除后，预注册新不重叠canary、一次运行，可信/修复门槛真实达成才另授权Fresh30/E2。失败封存回DEV，不能重称独立。

当前首个旧DEV补丁成功，不证明研究完成。**不要承诺一周或30/30完美**，不要把更高输出预算+thinking结果作纯因果改善。

## 5. 工程/交接/安全

最新工程数与各源SHA见[收据](../../data/e1c_evaluation_2_completion_success.json)，工程回归不作修复率。新增zero阶段曾有fixture临时ROOT不覆盖原PARENT的跨盘路径错误，正确mock父目录后原断言保留；不是弱化测试。

原raw/ledger/seal/源码/probe/Gold/key/所有负结果保全，日志仅集中续档，两Roadmap与WebCodex交接更新；没有下载/删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key修改，不用Pro，canary/C5/TEST/Fresh30/Test500/E2仍关闭。Cloud可运行无模型源码测试；缺本机private产物/镜像报INFRA_BLOCKED，新方法未完成/未远程接线验证，不扩大tunnel白名单或上传评分答案/密钥。
