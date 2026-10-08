# E1C2：生产检索之后的真实 probe 小阶段

## Material Passport

- 日期：2026-10-08；类型：OLD DEV 执行诊断；状态：预注册。
- 前置事实：协议 pilot 的两次真实 Flash 调用共 5,997 tokens，均为成功的生产检索动作；不是复现成功。原输出/策略/ledger/seal 全部只读。
- 新输入：同两条旧 DEV，直接使用已 seal 的 turn-2/input.json；核对 issue/base 不变、Git workspace/source SHA，并绑定父输入与新输入摘要。未重新执行旧 probe，没有旧 probe 或评分结果输入模型。
- 本阶段不是独立 canary，也不是中断后自动重试；上一阶段按预注册单调用上限正常完成，本阶段单独冻结身份与有限预算。方法不按单题补规则。

## 精确命令与限制

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_protocol_probe_stage freeze
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_protocol_probe_stage run
```

`deepseek-flash`，thinking disabled，最多 6 次调用、每题最多 3 次；本阶段 40,000 provider tokens、单题 24,000、单请求 output 2,000；input estimated hard24k、reserve1.4，保留未来首调用预算，retry0。上一阶段 5,997 单独记账，不拼成新成功率；新增调用不得超过本阶段限制。运行前公布命令，使用用户既有≤100k每实验委托。

协议 policy/decoder/执行器与上一阶段相同；真实 Python 输出、AST、normal control、target稳定失败、Controller 资格分别报告。遇到无资格/未知，不因为 Gold/旧参考有效就放行 trusted；本阶段不支持 repair/canary gate，不能叫 E1-C 已完成。结束后根据证据决定通用 DEV 修改；不自动追加请求，不恢复同 namespace，不打开 canary/C5/TEST/Fresh30，不访问 Gold。无镜像下载、系统操作。
