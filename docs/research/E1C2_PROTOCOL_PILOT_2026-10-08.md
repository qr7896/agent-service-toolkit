# E1C2：实际协议链双来源小试验（预注册）

## Material Passport

- 日期：2026-10-08；类型：OLD DEV protocol diagnostic；状态：预注册，非独立验证。
- 问题：去掉可复制的代码说明示例、接入封闭 transport wrapper 与 AST 后，实际模型能否输出有效动作/真实 Python，而非协议模板？
- 来源：上一冻结四参考中，按原顺序每个 library family 取第一条，共两条。定位/生成仍任务无关；不按任务挑文件。
- 方法：现有 acquisition_context 的生产源与公开 issue 消息、action_protocol.policy/decode、原 Controller、原离线执行器；逐层实际 hook 检查。旧冻结文件与账本不改。

## 冻结命令与预算

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_protocol_pilot freeze
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_protocol_pilot run
```

模型 `deepseek-flash`，thinking disabled，最多 **2 次付费调用**（每题 1 次），总 provider tokens 硬上限 **20,000**，每题 **12,000**，每请求输出 **2,000**。输入估计硬上限 24,000，但还须通过 task/batch 预留检查，实际不是允许输入 24k 后突破本轮总额。未来首请求预算保留；reserve multiplier 1.4；retry=0。第二轮若需要调用，在预算层停止，不悄悄追加。仅在用户先前委托的单实验≤100,000授权范围内执行；运行前报告精确命令。

新目录 `.codex/e1c/evaluation_2/action-protocol-flash-pilot-v1/`；冻结后开始标记/ledger 禁止重试。异常如实保存，不重新运行同 namespace。2 条是协议诊断分母，仍保留 DEV12/准入9/历史参考4，不报告新成功率。

## 放行与边界

分别记录 JSON动作、代码 AST、真实 control/target 执行、Controller资格四层。有效非 probe 动作不是有效复现；budget stop 不是模型错误；Python有效也不是 trusted，更不是修复成功。只有真实输出协议与执行证据充分，才另立版本扩大 DEV；不自动扩批。格式/协议仍坏则先回到零模型修复。

只用公开 issue、exact-base生产源码、自身离线反馈；测试断言/Gold/官方评分不进入模型。无网络容器、无人工选文件、无 Gold 接口、无补丁生成。canary、C5、sealed TEST、Fresh30、E2 均关闭。无镜像下载或系统变更。
