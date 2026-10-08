# 自动补证/context：预算调整已落地，真实JSON协议失败封存

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: VERIFIED（执行/预算/封存）；质量未达标
- Version Label: acquisition_results_v1

[哈希收据](../../data/e1c_evaluation_2_acquisition_results.json) · [方法/预算依据](E1C2_ACQUISITION_CONTEXT_PROTOCOL_2026-10-08.md) · [新paid协议](E1C2_ACQUISITION_DEV_PROTOCOL_2026-10-08.md) · [动作协议零修复](E1C2_ACTION_PROTOCOL_ZERO_2026-10-08.md)。

## 1. 上下文预算：官方上限不等于推荐消费

DeepSeek官方当前deepseek-flash支持1M context、最大384K输出；规范别名由现Flash服务，不用Pro。[官方模型规格](https://api-docs.deepseek.com/quick_start/pricing/)。SWE-agent将max_input/max_output、per-instance/total成本、调用数分别配置，未规定所有任务一个最优token量；mini默认也按成本/观察长度管控。[SWE-agent配置](https://swe-agent.com/latest/reference/model_config/)、[mini默认yaml](https://raw.githubusercontent.com/SWE-agent/mini-swe-agent/main/src/minisweagent/config/mini.yaml)。

项目新版采取input软目标12k/estimated硬限24k、output2k；字符安全限96k。单题soft目标32k/允许闲置pool但hard48k，四参考整批hard80k，最多16请求/retry0，future首请求预算保护。32k为提示性目标，真实成本受48k/80k与ledger保护；不偷偷重置旧额度。用户允许合理增context，此预算仍≤单试验100k。实际此批input仅2527–4610tokens，请求总消耗53212，未触发预算stop；并未每次消费24k，更没装满1M。

这是按本项目记录选择的工程预算，不是行业公认最佳值。模型窗口、每次输入、单题多轮累计和整批累计必须分清；char不等于token，provider usage为最终成本来源。

## 2. 自动源码补证的实际零调用验收

Controller从program/qualification内unexposed import binding静态resolve exact production定义，验证path、host/LF/base Git blob，最多2symbol/issue+base、1MB/file、depth4 import解析。独立view overlay不mutate初始输入，下一messages和下一execute均使用新的定义窗；补源本身不回填本轮probe资格或提升trusted。

真实取得DecisionTreeClassifier与Schema两个生产定义，源SHA/seed/depth保存并实际暴露到下一Human；原probe delegate只缓存，不执行模型/容器。两个旧预算停止样本在额外源也暴露的情况下，reserve11985→11100、10154→8471，Scope未知/行为义务未提升。这只是实际补证/消息接线证明，不能叫新模型成绩。

零checker v1在首次取得前因缓存turn2未复制compiler.json停止，source/freeze保留。新zero-resume仅用原109-prefix SHA补齐compiler/contract/execution bytes到generation-only view，旧seal255文件不变、不复制Gold目录；2 view专项后继续尚未执行补证，未重跑旧namespace/probe。nested conversation曾被内层配置覆盖，1failed/7passed留档；修复owner后全过，未弱化断言。两个unused import与测试新增语法gate均在其freeze前修正。

## 3. 新真实试验结果：不是预算不足

精确run：`uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_acquisition_dev run`。

四参考新生成，16Flash完成请求/53212tokens、无未结/自动retry；全部四题达到四轮终局（1 turn_limit、3 abstained），0合格candidate/0机器可信/0Agent repair，54generation文件seal。独立Gold命令完成后attempted0/discriminating0，因为没有候选，不运行任何Gold容器。旧scope/resume的1复用Gold候选保持，不拼到本轮。

记录响应发现两项共因：

- 三题共6probe逐字复制system JSON示例的setup描述`production imports and fixture`，不是可执行Python，syntax门槛拒绝。
- 另一题四回复封装为type=json_object+action=dict，旧codec不认识；其中也有2份同类placeholder probe。故本批自动missing-dependency acquisition没有真正被模型有效probe触发，不能声称已验证live补证收益。

较大的预算消除了两类reserve停机，但没有解决协议产物有效性。方法/预算/策略同时变更，不作单因果归因；完成不等于四题通过，不能报“效果完美”。

## 4. 付费停止后零调用修复与下一步

不改已冻paid/policy/result，不rerun当前namespace。新action_protocol去掉所有probe代码字段示例值，改字段类型和真实Python要求，不替模型编代码；精确closed transport wrapper可剥，unknown wrapper不猜。沿用原7fields/quote ref/schema验证，再ast.parse前置；真评分marker/Oracle/Source/执行/范围边界不改。

7专项通过；其中一次decoder未做syntax的测试失败后，只实现语法前置，不改断言。新zero身份绑定全部原response/seal与source/协议，只读16响应：4wrapper恢复，8非probe动作语法有效，8坏probe仍SyntaxError，**没有把旧坏代码修成成功**。尚未接新producer/验证新模型不会回显。

下一步唯一顺序：把无示例值policy+codec整体接新producer → 实际最终消息/decoder输入同轮检查（不能仅mock transport）→ 四参考≤80k另版freeze/new generation → candidate/normal/target/observer/scope分账 → 完整九准入DEV（fixed12）→ 真质量gate后才新canary≥2/3/Agentpatch official/DEV30/Fresh30/E2。当前不自动追加下一批，未打开TEST/C5/Fresh30，不保证一周或30/30。

## 5. 安全与工程

新增acquisition9/view2/budget3/protocol7共21专项，重点40/Ruff/合成preflight ready=true；初完整1629passed/4skipped/33warnings107.46s XML保留，最终1636passed/4skipped/33warnings81.43s/XML SHA另绑定收据。passed不是repair rate。原201/109/255等记录与所有源/ledger/negative保存。无镜像下载/删除/系统Docker重启/IPC/VHD/registry/代理/tunnel/key修改。raw/probe/Gold/key不上Git，源码/专项/协议/脱敏收据公开。
