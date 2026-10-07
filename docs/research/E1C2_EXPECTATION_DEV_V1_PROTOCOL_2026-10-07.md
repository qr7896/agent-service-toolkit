# 期待引用角色与公开API对照：四参考实验前协议

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（结果另存）
- Version Label: expectation-reference-dev-v1

前版execution-plan v2四参考Gold4/4不回填；其中1项期待引用是trace，正常control省掉公开两API共同输入，实际参数校验失败不是公开guard故障点。新版本先在oracle lock前拒trace/code/literal/空期待（包括mixed trace和不完整guard）；未知prose不自动可信，反馈只列原catalogue可选prose ID，不替模型选择期待/改值。

仅识别一组明确works/succeeds for/with→but not for/with语法，每侧唯一顶层qualified call；多义/复杂语法not_applicable，不猜规则。已识别的对照要求模型control/target实际调用公开A/B端点，绑定自己未影射的from-import alias与已暴露production源码SHA；共享参数不能省掉，自己的简单argument表达式须相同，公共literal约束保留。原报模块alias/实际值/语义不自动证明，source未暴露或绑定不确定拒绝/反馈检索，不改输入/目标/原oracle。无task ID/手选文件/原测试/Gold规则；正常control/目标仍由模型生成。

source-bound实际trace/公开guard审计接在执行后，独立标记API对照语法履行与原报机制未证；不将位置差异当全局不可达，不因Gold区分授machine trusted。保持既有compiler控制转换与source入口/类型/正常两过/目标重复失败、严格DTO与源保护；compiled所有者和inner loop均绑定新executor，回归覆盖重入/恢复。

先全部前版四响应零调用角色/对照审计，不Gold挑；合成负例/跨仓库真实smoke、Ruff/预算V3/完整回归过，method/input/protocol/budget freeze与提交后，最多一次四参考新生成。数字Gold与语义分账；四参考/行为忠实性/cross-repo gate未全过停止本轮paid扩批，不抽第6canary。

Flash only deepseek-flash/non-thinking/temperature0；整批50,000/题24,000/output2,000/≤16请求（题4）/reserve1.4/待跑首reserve保护/retry0。先列精确命令后按用户≤100,000授权执行一次，不Pro/不provider retry；固定12/九准入/screen4，不是完整DEV/独立/repair。旧协议、source、预算、响应、账本、所有negative不改、不best-of。

```powershell
# D:\codex\working\project20260827；新namespace各阶段仅一次
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_expectation_dev smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_expectation_dev preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_expectation_dev run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_expectation_dev gold
```

producer完成且seal后独立Gold，评分答案不输入模型。TEST/C5/Fresh30/private Test500/canary/Agent repair/E2关闭。无新下载删除/重启Docker/IPC/VHD/registry/proxy/tunnel/key操作；原所有备份保留。Web接source/zero单测，缺本机私有材料/runtime报INFRA_BLOCKED，旧bridge白名单不扩，不声称新paid云端端到端已验。
