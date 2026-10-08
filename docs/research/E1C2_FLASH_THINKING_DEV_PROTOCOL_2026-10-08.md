# Flash thinking 严格组单请求 DEV 配置诊断

日期：2026-10-08，身份 `e1c2-flash-thinking-strict-dev-v1`。此前两版各3请求均未修复目标；v2实际3calls/20,385tokens，standard保留局部Z补丁仍F2P0/1/P2P37/37，两个evidence组同值无改动。原v1/v2与所有zero结果不回填。

## 可检验的配置瓶颈

本地原runner显式`provider_disable_thinking=True`。官方说明Flash默认开启thinking/high；thinking中temperature不生效，普通无tools对话无需回传reasoning内容。[官方Thinking文档](https://api-docs.deepseek.com/guides/thinking_mode/)。不能因此断言关闭thinking就是失败原因；本轮只测配置可行性，不重复三组投钱。

同一旧DEV、**只跑v2 strict_evidence一个cell**，final messages SHA须与已seal v2严格组完全相同；没有新提示词/评分信息输入，仍不读取现成测试断言到模型。共享准备沿用v2为standard arms检索base tests，但仅strict payload发送，不声称整个进程未访问test对象。

## 精确配置/预算

- 模型仍`deepseek-flash`，不得Pro；明确`thinking enabled`、`reasoning_effort high`、不传tools。
- 新SDK适配器在HTTP之前验证真实payload中的模型/mode/effort/JSON格式和max_tokens；仅存配置/用量/推理存在标记，不保存或公布reasoning文本。
- 最多1次request、最多30,000 provider总tokens，含推理用量；生成上限8,000含reasoning/可见输出。输入估计×1.4+8k须≤30k。HTTP120s、SDK retry0、未知收费/started不自动重跑。
- 输出/批次预算也从v2提高，因此**不是单因素thinking因果试验**。temperature=0由既有adapter兼容保留，但thinking忽略它，不能宣称确定性解码。
- 原exact-edit/AST/source暴露约束、兼容外壳、全生成seal后official独立容器评分不变；Gold/新测试/评分日志不输入模型。预算gateway真实total tokens计费，不能只计JSON文字。

零调用预检：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_flash_thinking_dev preflight
```

**待新精确授权的付费命令（不沿用v2已消费的授权）：**

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_flash_thinking_dev run
```

离线MockTransport测试检查真实SDK HTTP JSON/模型/mode/8k上限，并验证reasoning被算入completion/total与ledger；这不是实际provider能力证书。预检全方法/预算/原seal/同prompt先freeze，缺私有材料报INFRA_BLOCKED。结果仍一个旧DEV配置校准，不能算独立泛化/三组效应或30/30。

若无改动/局部补丁/预算截断则封存，不自动扩额度；下一步才在公开自产反馈上建立可执行的补丁自验证→限次修正，而不是继续同样单次模板。通过配置与修复门槛后才两来源从issue完整链、固定12九准入、全方法freeze/不重叠canary；不启用TEST/Fresh30/E2、不改Docker/IPC/VHD/代理/tunnel/密钥或下载/删除。
