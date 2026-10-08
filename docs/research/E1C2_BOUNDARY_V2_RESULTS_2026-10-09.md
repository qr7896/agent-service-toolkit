# 公开反例DEV v2结果与Flash thinking单请求准备

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-09（真实v2调用发生于10月8日晚）
- Verification Status: UNVERIFIED（执行收据已核对，未独立重跑）
- Version Label: boundary_v2_results_v1

## 1. 精确授权的真实v2试验已完成

执行 `uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_three_arm_boundary_dev run`，退出0，Flash3请求/20,385tokens，retry0、无超额/未知收费。固定同一个旧DEV/三个cell；不是独立新任务或完整从issue定位/生成的端到端。

| 组 | tokens | 实际产物 | 独立评分 |
|---|---:|---|---|
| standard | 6,312 | 非空局部Z补丁 | F2P0/1、P2P37/37、resolved=false |
| standard_evidence | 8,067 | old/new相同，无改动 | 未运行候选评分容器，resolved=false |
| strict_evidence | 6,006 | old/new相同，无改动 | 未运行候选评分容器，resolved=false |

三次输出均正规JSON，兼容外壳动作false。本轮不再有封装拒绝；但两个证据组没利用反例产出修改。**原v2固定三cell resolved0/3；不能说“3个软件测试都失败”，不能证明反例方法普遍无效。** 全生成先seal再评分，评分源码/断言/Gold不输入模型。

standard新patch SHA `c04994d5e98a16e99da39b9c7854d637d1efb12b3166c1d9ab182693157d8713`与前轮后验strict patch逐字节相同；因此可参考原同image/base/optional条件的21个public变体结果11完成/10失败，**这是已有cache引用，不是本轮重跑21个任务/变体**。本轮真实official候选评分再次独立完成，源身份/log有效；script rc0掩盖pytest目标失败，严格使用F2P/P2P判resolved。

10月8日两次三组校准合计6calls/36,149tokens；不是整个项目累计费用。原v1/v2/所有zero与分账不改，不best-of拼成功率。完整可信与正式Agent修复仍0，E1-C evaluation_2未完成。

## 2. 新的可检验配置瓶颈

读取真实caller与预算binder确认：一直显式`provider_disable_thinking=True`。官方Flash说明默认thinking开启/effort high，thinking忽略temperature；无tools普通对话无需回传reasoning正文。[官方文档](https://api-docs.deepseek.com/guides/thinking_mode/)。这只支持一个待测假设，**不证明关闭thinking就是失败原因，不保证开启便修复**。

本轮先准备最小诊断，不继续三组盲试。新身份 `e1c2-flash-thinking-strict-dev-v1`，只发送原v2严格组完全相同prompt，SHA `23e9624216d52f5de6519c066b90d6c07dd26bc379fb653baf18942c1e46b13f`。仍Flash、thinking enabled/high，最多1请求/30,000总tokens，含推理用量；生成上限8,000含reasoning/可见输出，retry0、HTTP120s。预算也增大，不能称孤立thinking因果试验或确定性采样。

新适配器在HTTP前检查实际SDK payload的模型/mode/effort/JSON/8k/no-tools；仅记录配置、reasoning用量/存在标记，不保存或公开reasoning正文。离线MockTransport检查真实SDK HTTP JSON及ledger把reasoning计入总额，非真实provider效果证明。初预检遇原三组helper固定读取standard而single-cell payload过滤过早，尚未创建namespace；补兼容测试，保留三组准备/只冻结发送strict后首次成功preflight。原代码/方法均未改。

[新协议](E1C2_FLASH_THINKING_DEV_PROTOCOL_2026-10-08.md)于10月8日晚准备，10月9日凌晨完成freeze：reserve17,148≤30k，maxcalls1，**新paid0，待精确命令授权**。共享准备仍会为standard读取base测试，实际model payload严格无该通道；不宣称整个进程没读取test对象。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_flash_thinking_dev run
```

若无改动/局部/截断则封存，不自动续费或扩预算；后续重点是公开自身反例的实际自验证→限次修正，不继续以同样one-shot模板扩批。真实修复/config质量门槛过后才两来源完整自动链/记全部成本→固定12九准入→完整freeze/不重叠canary一次→另授权Fresh30/E2。当前不开上述集合。

## 3. 工程/交接/安全

8新增专项；Ruff、预算/V3重点、合成compact preflight过；完整1736passed/4skipped/33warnings，119.91秒。旧XML保留（本轮XML名称沿用10月8日启动批次，实际完成跨日），不是修复率。[收据](../../data/e1c_evaluation_2_boundary_v2_results.json)绑定paid seal/ledger/result/候选、新freeze/XML。

日志只集中续档；两Roadmap/交接更新最新入口。没有新增模型、图像/镜像下载/删除或系统配置改变；Docker/tunnel/代理/密钥/VHD保全。原所有实验负结果保留，private raw/Gold/key不入Git。Cloud可做无模型检查，缺本机父产物/镜像时报INFRA_BLOCKED；新thinking入口尚未真实运行或通过tunnel远程接线，不声称可直接远程调用。模型仍Flash，不用Pro，不保证完美/30题全过。
