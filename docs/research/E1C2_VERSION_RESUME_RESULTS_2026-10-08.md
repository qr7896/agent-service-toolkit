# E1-C evaluation_2：公开旧版本对照续接实证

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-08
- Verification Status: ANALYZED（明确版本点与原probe的实际结果）
- Version Label: prepared_version_resume_results_v1

## 1. 结果

Docker只读健康检查恢复通过，未由本轮启动/重启或修改配置。按[resume-only预注册协议](E1C2_VERSION_RESUME_V1_PROTOCOL_2026-10-08.md)，完成此前从未执行的MM1359旧版本probe：

| 角色 | 程序 | 源码版本/环境 | 结果 |
|---|---|---|---|
| 封存当前base | 原target probe | 原immutable image/base | 历史两次rc1；本轮不重跑 |
| 新续接旧版 | 相同probe SHA，字节未改 | 同image、readonly旧生产包3.0.0rc8，其他隔离边界不变 | 实际导入版本/path核验通过，rc0 |

因此原model程序在公开旧版本点完成已得到实际证据，不再只是“旧版可能会成功”。这是**1份DEV缓存的1个明确版本点**，不是全DEV12、所有更早版本或新独立任务；也不是Agent patch成功。原public完整fixture、其他功能义务仍不自动认证，machine trusted保持0，旧资格/Gold4/4/exception3/4不回填。

新增model calls/tokens **0/0**，Gold读取0，生成新probe0，新诊断容器1。原11文件152,704bytes直接readonly复用，没有重新archive、下载镜像或复制原工作树。v1 freeze/failure保持；新namespace绑定公开failure收据，确认原driver/task freeze/run.log/result不存在、容器计数真实int0，然后一次执行。started记录与driver/log/result均保存，不自动retry。

## 2. 验证与安全

9专项覆盖已执行/错误phase拒绝、真实runtime产物、重复/变更/额外源文件及旧版/probe/path约束；重点28项/Ruff和合成preflight通过。没有触碰IPC/VHD/registry/代理/tunnel/key；没有Gold/test数据进入controller/model。原生产seal、两角色原probe与准备源码摘要在续接前核对，不能借continuation回填旧实验。

GitHub此前500恢复，先前两本地commits已成功同步到main；本轮结果随后安全同步。私有source/driver/log/model probe/Gold/test/key不上Git，只提交源码、专项、协议和[脱敏收据](../../data/e1c_evaluation_2_version_resume_results.json)。

## 3. 之后不再重复收集器

1. 旧版续接任务完成，不再运行该namespace或原version v1。MM1252没有本轮旧版执行证据，不能把本结果移植过去；若后续需要，先明确可用公开版本/本地源身份，缺源保持不可用。
2. 将显式keyword子义务、参数文档支持缺口、实际old/current版本witness合并为统一有限行为资格。规范每个支持结论的具体scope、输入/失败/normal证据与剩余义务；不要要求任意Python全语义证明，也不要把一个子义务直接叫全issue可信。
3. 当前gates/observer都是旁路审计，尚未统一接入新producer。下一实现是controller接线与完整方法/预算freeze、零模型adapter regression，再同版旧DEV小预算新生成；旧run/source/result不改，不继续独立堆collector。
4. 同版DEV可信gate真正达标才历史全排除的新canary一次≥2/3；通过后才Agent patch/official，最后旧DEV30/Fresh30/E2。当前不开canary/TEST/C5/Fresh30/privateTest500/repair/E2，无新的付费命令放行，不保证完美/30题全过。

未来模型仍Flash，先列精确命令/次数/≤100,000 provider tokens，retry0；真实模型预算与工程测试数分开。日志只集中续档，两Roadmap与WebCodex handoff更新单一当前入口。

最终Ruff/重点28项/合成compact preflight通过，完整回归 **1550 passed / 4 skipped / 33 warnings（106.43秒）**；XML/新冻结方法/原中断receipt及原当前执行SHA载于收据，不包装成修复率。
