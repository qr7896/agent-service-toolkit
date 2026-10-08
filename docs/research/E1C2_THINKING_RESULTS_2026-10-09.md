# Flash thinking实跑：模式有效，完整输出被8k截断

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-09
- Verification Status: UNVERIFIED（执行收据核对，未独立重跑）
- Version Label: thinking_results_v1

## 1. 精确授权的单请求结果

执行 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_flash_thinking_dev run`，退出0、原namespace封存，SDK retry0，无超额/未知收费。实际Flash1call：input5,708 + output8,000 = **13,708 provider tokens**，其中reasoning_tokens_reported=8,000；actual wire检查确认enabled/high、no-tools、8k生成上限。

finish_reason=length，response_status=truncated，JSON raw字符0；模型在预算耗尽前没有给最终补丁，producer据既定协议拒绝不完整输出。**没有候选进入官方容器，所以修复效果未测，不是“官方目标失败”或无能力证明。** thinking生效是实证；比非thinking准确率提高则尚未证实。reasoning正文未保存/公开，不从未完成输出手工编补丁；已结算账本不重复调用。

同一个旧DEV严格组prompt与v2完全同SHA，模型无现成base测试/官方断言/Gold，shared准备仍读取其他两组的base对象，不称整进程没访问test。10月8–9日这三次局部校准累计7calls/49,857tokens（两批三组+本单请求），不是整个项目成本，也不合并最佳得分；E1-C evaluation_2仍未完成。

## 2. 原摘要计数问题另立零调用核验

原legacy scorer固定写fixed_cells=3，但本trial freeze固定1、rows只有1、账本1。原result里的resolved=false保留，不能按3个case报失败率。新增 `flash-thinking-cardinality-zero-v1`核对原freeze/生成seal/源码后，保存独立verified-result：fixed1、raw_reported3、legacy_cardinality_consistent=false；原raw/分数/方法全部未改。

这只修正展示/审计口径，不制造模型成绩。新纯validator要求rows与freeze arm顺序/唯一性/task身份完全对应，缺行/错误arm/task/重复行拒绝。下一runner保留legacy raw，同时另写verified-result供发布，不再误用固定三组计数。

## 3. 新窗口准备（未付费）

[新完整协议](E1C2_THINKING_COMPLETION_PROTOCOL_2026-10-09.md)，身份 `e1c2-flash-thinking-completion-dev-v2`：same prompt/mode/high，不改源码输入/反例/提示词；生成从8k到24k（含reasoning/最终JSON），总provider40k，max1call、retry0；HTTP由120到300s，官方评分仍900s。实际SDK create明确timeout300，离线Mock核验HTTP body/timeout与推理计费。不改旧provider预算，只另冻未启动身份。

真实preflight已完成，reserve33,148≤40k，same strict SHA23e9624216d52f5de6519c066b90d6c07dd26bc379fb653baf18942c1e46b13f。**新paid0，须新精确命令授权：**

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_thinking_completion_dev run
```

增大输出窗口只因当前结果被审查性截断，不能保证修复，也非单因素thinking收益。若24k仍截断/无改动/局部，停止自动扩额，回旧DEV检查effort/context和公开自产自验证→限次修正闭环。配置/真正修复通过后才两来源从issue全链/完整成本、固定12九准入、全method freeze/不重叠canary；当前不启用TEST/Fresh30/E2。

## 4. 工程与安全

6新增专项/Ruff/重点33/合成compact preflight通过；完整1742passed/4skipped/33warnings、123.55秒，[本轮收据](../../data/e1c_evaluation_2_thinking_results.json)绑定XML与各阶段源SHA，工程数不作修复率。所有旧XML、源码、协议、raw/账本/seal/负结果保留，日志只集中续档。

无新增下载/删除/系统Docker重启或IPC/VHD/registry/proxy/tunnel/key改变；无Pro、canary/C5/TEST/Fresh30/Test500/E2，原full_issue_trusted false不提升。原raw/Gold/密钥不进Git；Cloud缺本机产物/镜像报INFRA_BLOCKED，新窗口付费和远程tunnel入口尚未验证，不保证完美/30题全过。
