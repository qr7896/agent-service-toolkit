# 旧DEV：source-contract与评分前回退的前瞻pilot

本轮之前完成了两版A/B和缓存source-contract回放。两臂各2/12但可信任务不同；评分前选择规则的事后DEV模拟得到3个Gold可区分候选。该模拟是在已见DEV结果后开发，不算独立或前瞻证据。本pilot另冻新身份，重新生成全部九条已准入旧DEV，不复用缓存响应；固定DEV12分母，三条环境失败保留。

输入为production coverage v2-ready，公开issue投影+exact-base生产源码，无测试断言/Gold输入。先用B合同提示、source-proven构造边界和完整生产import前提派生，正对照两次过后运行目标。B弃答/格式拒绝/控制失败/目标无稳定故障时最多一次A基础probe请求。第一个base重复失败的候选锁定即STOP；选择不读取Gold结果，不因Gold失败换A或重跑。这不是跨版本best-of。

模型仅deepseek-flash non-thinking/temperature0。最多18请求、每题2请求，输出单次3000，联合单题20,000、整批100,000 provider tokens，SDK retries0。只需主提示预留先放得下，fallback按真实已用tokens+本次reserve在线守卫；预算放不下中断并保留固定分母，不挪预算、不重试。本次前瞻DEV单实验≤100,000；累计已知用量继续计入一周282,000停止线。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_dev preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_dev run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_hybrid_dev gold
```

模型命令先列明，再按用户已有预算权限执行。原始两批canary和旧DEV身份不改；所有控制/目标/角色响应和usage留存。截断响应计费留档，可按预注册两策略逻辑尝试下一策略；不重试同策略provider失败。网络/权限/预算等异常中断，原身份不续费重跑。

前瞻pilot至少在两仓库达到≥2个语义审核可信复现，且支持保留缓存baseline两题并有新增，才考虑冻结新canary方法；门槛不满足则封存，不扩新的付费样本。收益只作DEV开发结果，新的独立canary需新身份/不重叠/先冻后读/固定分母一次≥2/3。repair/TEST/Fresh30继续关闭。
