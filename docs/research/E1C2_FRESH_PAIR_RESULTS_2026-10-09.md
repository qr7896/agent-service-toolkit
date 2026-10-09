# 两来源 issue-first 新生成链完成：原成绩 1/2，零调用解码审计另有一题通过

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-09
- Verification Status: UNVERIFIED（已核对执行/评分收据，未独立重新生成）
- Version Label: fresh_pair_results_v1

## 1. 这次实际完成了什么

用户精确授权 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_fresh_pair_pipeline run`。新身份 `e1c2-fresh-pair-repair-dev-v1` 已完成，约106.57秒。

模型统一 `deepseek-flash`，实际 wire enabled/high/no-tools、每请求生成上限20k、HTTP300秒；**4 calls / 39,970 provider tokens**，含22,586 reasoning tokens，所有finish=stop。原100k预算未扩展，无retry/未知收费。reasoning正文不保存或公开。

输入来自新冻结的公开issue/生产源码自动检索与限定名补证，不使用旧probe/成功patch/评分答案；模型本轮新生成配对程序，再根据自产离线执行反馈新写生产patch。定位产物是前次零调用冻结，本次没有重新下载或重跑检索，不能称两个全新任务。两份输入canonical与首请求SHA继续与freeze相符。

| 旧DEV来源 | 新probe执行 | 原冻结repair/official | 本来源tokens |
|---|---|---|---:|
| scikit-learn-13496 | normal×2通过；target×2稳定TypeError，涉及公开要求的warm_start | raw多一个`type=json_object`元字段，被严格parser拒绝，未评分 | 17,896 |
| marshmallow-1252 | normal×2通过；target×2稳定失败，覆盖公开Z日期输入 | 非空新patch；自产normal/target各两次通过；F2P1/1、P2P37/37，resolved | 22,074 |

两来源生成全部seal后才独立官方评分，官方答案/Gold没有回流模型。**原冻结系统：pair执行门槛2/2，official resolved1/2。** 原pair不自动成为完整语义可信；自验证不是官方修复率。

本次Marshmallow模型patch不同于先前regex修复：利用已公开的ISO regex取得时区片段后剥离，再走原解析。没有人工编辑patch或根据官方测试改代码；新patch独立通过不等于所有公开范围已完备覆盖。

## 2. 失败根因与零调用改进

Scikit-learn 的失败不是没有生成补丁：原模型已给出两个生产精确替换，为构造器新增warm_start并传给已有BaseBagging。唯一root schema阻塞是已知metadata envelope。不能偷偷修改原parser后将原成绩改成2/2。

按[独立零调用协议](E1C2_FRESH_PAIR_CODEC_ZERO_2026-10-09.md)运行新身份 `fresh-pair-codec-zero-v1`：复用已有 `canonical_response`，仅当keys恰为type+edits且type=json_object时移除元字段；**path/old/new字符串、两个模型probe、正常控制和断言完全不改**。仍须公开暴露old/base唯一/AST等原检查。没有补写源文件、手动挑文件、重新请求模型或读取隐藏断言设计规则。

四次自产postpatch离线执行通过。整个零调用生成/执行再次seal后独立official：**F2P1/1、P2P19/19、源/log有效、rc0、resolved=true**。原成功Marshmallow不重复评分。新审计provider0，原完整producer seal/freeze/result/paid ledger再次核验字节未变。

结果应分别表述：原系统1/2；后验兼容解码新增候选1/1通过。**两个不同来源都有模型补丁官方通过证据，但没有同版冻结系统2/2结果，更不是30/30或独立泛化。** 下一版本有明确、任务无关、低成本改进：把已测试的精确metadata兼容器正式接入新的生成执行方法，在调用前冻结，而非事后挽救。

## 3. 当前仍欠缺的证据

Scikit-learn 的目标probe已检验warm_start增量训练及旧树对象保留，normal检验默认训练/评分形状；但默认False及所有训练语义并未完整自动认证。Marshmallow虽有真实缺失依赖blocker，生成probe又显式设置dateutil_available=False；这是有条件的fallback行为证据，不能包装成任意环境或所有ISO变体的完全可信证明。两题 full_issue_trusted 均保持false；没有修改旧资格常量。

这轮证明从公开输入生成的probe和执行反馈能支持两个库的真实修复，但样本仅两个已见DEV，方法也存在codec工程缺陷。创新价值仍需同版消融和未参与调参任务验证，不宣称SOTA或已有泛化优势。

## 4. 唯一后续顺序

1. 将精确兼容解码接入下一统一方法；为错误元字段/未知key/代码字符串不变/解析拒绝补实际调用链测试，原frozen源不修改。
2. 用公开行为义务核算normal/target与环境条件，不因official通过跳过缺证；明确“条件机制支持”“完整可信”“official修复”三个口径。
3. 冻结同版DEV12/九准入的定位、生成、判别、修复、完整成本；未准入/未调用/预算停止仍列固定12，不拼best-of。**预算须按整个cohort声明，不能把多个100k子批伪装成一个100k实验**；新付费仍需精确命令授权。
4. DEV质量门槛实际达成后才冻结全历史排除的新canary一次≥2/3及修复对照；失败封存回DEV。之后另授权新任务、Fresh30/E2。

没有当前可直接重跑的paid命令：原4次额度已消费，started身份不能恢复、改源或retry；codec审计也已完成不可重跑。TEST/C5/Fresh30/Test500均未打开。完整研究未完成，不保证30/30或一周完美。

## 5. 安全与接手

新零调用审计采用显式row/root的既有执行器/评分函数，不改全局OUT/preflight，无新依赖。10项组合专项通过（3新增）；重点回归37通过。初一测试错误使用不可覆盖的_save修改临时fixture，被正确拒绝；改成仅临时fixture覆盖，不改生产防覆盖规则/测试期望。工程完整回归与XML见[结果收据](../../data/e1c_evaluation_2_fresh_pair_results.json)。

本轮没有镜像下载/删除、Docker重启、IPC/VHD/注册表/代理/tunnel/密钥配置变更。Cloud可跑源码单测；本机私有原始产物/镜像/评分材料/凭证不随Git同步，缺材料报INFRA_BLOCKED，不扩tunnel白名单或开放裸Docker。结果、所有旧失败、readiness收据与XML保留；逐轮过程只写集中日志。
