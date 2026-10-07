# E1-C evaluation_2：期待门槛与公开对照实验

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run / analysis
- Origin Date: 2026-10-07
- Verification Status: ANALYZED（账本/seal/独立评分及零费对照核对；语义未验证）
- Version Label: expectation-contrast-dev-results-v1

## 1. 结果与未过门槛

**新版Gold区分3/4，未保留上一版4/4；机器可信复现0，E1-C未封板。** 不能把更多限制或代码回归说成质量已提高。原固定DEV12、九准入、screen4分账；不是完整DEV、独立canary、Agent patch或official resolved。

精确命令：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_expectation_dev run`，目录`D:\codex\working\project20260827`；completed/exit0、producer seal后独立`gold` attempted3/区分3。Flash only、non-thinking、temperature0、retry0；上限50,000/题24,000/output2,000/≤16请求，实际**9请求30,477 provider tokens**。本轮一个付费版本，没有Pro/请求重试/追加付费重采样。自10月5日起可见755,829 tokens，非账单核验，也不是整个项目总账。

| 旧DEV参考 | 本轮结果 | 独立Gold |
|---|---|---|
| scikit-learn-13496 | turn2候选 | 区分 |
| scikit-learn-26289 | 两份code-only期待被拒；turn3称缺期待而弃答 | 无候选，不评分 |
| marshmallow-1252 | turn1候选 | 区分 |
| marshmallow-1359 | turn3候选 | 区分 |

前版4/4保持原记录；不best-of拼分，本轮成本30,477高于前版11,909，覆盖也没有改善。三候选期待角色仅“未分类待语义证据”，不是自动可信。

## 2. 已实际落地

1. 期待角色检查在oracle lock前执行；trace、混合trace、代码/字面量、不完整guard/空期待不能直接当desired behavior。仅拒错角色，未知自然语言不获语义证书。
2. 一组明确works/succeeds for/with→but not for/with报告，可提取唯一公开A/B调用。若识别到，则要求模型真实normal A/target B、未影射import绑定、已暴露production SHA、共享参数不遗漏、自己简单表达式相同、公共literal约束不改。复杂/多义语法不猜；报告module alias与实际值仍未证。
3. 完整delegate链在内层runner保持；执行后grounding记录实际trace/公开guard与对照语法履行，Gold和语义分开。Controller的本轮gate不替模型改期待或输入；既有compiler控制转换仍存在。
4. 旧四响应零费全部审，拦一项、另外三项仅保留未知；四公开Human输入逐字不改。两个repo synthetic真实正常对照通过，passing target不选bug；不是任务成绩。

实际新生成仍未完成公开A/B对照：当期待先被拒，反馈contrast为null，模型未利用已有比较事实而弃答。原公共文本仍完整可见，**不是原文被删除**，也不能确定单靠加反馈就会恢复；只是已识别关系未被结构化附回这两轮拒绝反馈。该零费审计发现两份probe反馈缺少结构化contrast，所有输入/响应/负结果保留。

## 3. 零调用正常对照可行性

新增`public_normal_diagnostic.derive`只作诊断：从公开A/B关系和旧模型target的from-import绑定派生A调用，复制其原自有argument表达式，补公共A专有的literal参数；未知额外参数/影射/源未暴露不派生。其setup/control是Controller派生程序，**不是模型生成，不接入live，也不当Agent成绩**；原target/oracle及缓存响应不修改。

对本轮两份相关缓存probe自动派生、按源SHA验证并在同一immutable base无网络容器中各做两次normal调用，全部通过；无需Gold/新增模型请求。两份缓存的派生control相同：**1个旧task、1个唯一程序、4次normal执行**。仅证明这一已有输入的公开A正常对照可运行，不证明B应具备A全部能力、不证明原报exact数据或语义忠实性，也不能3+1拼4/4。

## 4. 下一步执行顺序

1. 先零调用将证据来源区分为**明确接口请求／公开回归报告／公开比较报告／unknown**。从公共catalogue给出精确prose锚与A/B关系，不从trace、Gold或原测试造期待。
2. 比较报告的“B也应完成”若作为研究方法假设，必须标`inferred_from_public_comparative_report`，不能叫原文明确承诺；literal期待值仍不得捏造。在新的方法协议中明确准入条件与反例，不能暗改本轮严格口径来追回4/4。
3. 把已识别的比较事实附在拒绝反馈中，让模型生成真实A/B对照；诊断派生程序只作feasibility材料，不回填成模型候选。源码binding、共享值表达式、实际执行、公开故障机制分别记状态。
4. 跨仓库正负例/正常配置/错误期待/未知语义先验收，再另冻一次四参考新生成。两个门槛过后才同版完整九准入/有限native、全历史排除的新canary可信≥2/3、Agent patch/official评分、旧DEV30，最后另授权Fresh30 one-shot。

本轮停止paid扩批；不马上抽第6canary，不保证一周/30题完美。当前没有新live/canary命令待执行。

## 5. 工程、收据与安全

- 最终单次**1419 passed、4 skipped、33 warnings，113.65秒**；Ruff/规定预算V3重点/compact preflight ready=true。无断言/skip/timeout削弱，不算修复率。
- [公开收据](../../data/e1c_evaluation_2_expectation_results.json)绑定freeze/state/ledger/seal/Gold、期待binding、零费输入/反馈/正常对照与XML；raw/probe/Gold/test/key不上Git。
- 代码先提交`9648a4f`，freeze SHA`0f04c414602c65c89362e419c061ba16abfc9774a93a6ccc54ab83431b1df543`。所有已started namespace不得重跑或修改。
- 本轮无下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key改动，旧记录和备份全保留。TEST/C5/Fresh30/private Test500/repair/E2未开；当前无下载需求。
- WebCodex可接source/zero单测/脱敏摘要，缺本机原始材料/source/image/runtime报INFRA_BLOCKED，旧bridge白名单不扩，不假称新paid已云端端到端验证。
