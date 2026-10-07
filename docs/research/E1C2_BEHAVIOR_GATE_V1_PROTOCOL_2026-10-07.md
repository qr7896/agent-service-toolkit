# 有限行为资格分支 v1（零调用DEV预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: behavior_gate_v1

命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_behavior_gate audit-dev`；provider calls/tokens=0/0、Gold读取0，无新容器或旧实验重跑。新namespace `.codex/e1c/evaluation_2/behavior-gate-zero-v1/`存在即拒绝重放。全部四参考缓存按固定分母处理，生产seal/原probe/资格v3/exception-v2/pair/doc结果均用已有公开哈希收据绑定，不输入Gold或官方测试答案。

## 分支与证据

1. **显式变更请求**优先于base参数文档；旧文档不支持新接口不能自动否定请求。v1仅支持一个子义务：显式公开bool构造器keyword接受。必须有精确公共请求quote、公开bool域、唯一qualified API（不能仅按类名）、目标bool literal、去掉请求keyword后与normal完整AST相同、闭合构造器签名缺该keyword且无**kwargs、原host/LF/base身份、原编译probe构造器AST一致，以及该调用行真正的owned-probe TypeError/相同missing keyword。旧资格拒绝或unknown不提升。支持也只叫`支持bool keyword子义务`，不证明default值、增量训练、其他功能/请求。
2. **源码参数文档支持**作为独立输入域证据，不当全文语义权威。只支持有限词汇、声明行/源SHA，不看Examples/断言/答案；明确公共修改请求可覆盖旧文档。list声明和实际ndarray的缺口不是非法输入判决，也不能用normal API宽松行为补成target承诺。
3. **比较报告**始终标completion假设；报告实际共享keyword与其他输入状态、文档支持缺口分开，任何部分未知保持。**回归报告**标旧版本行为假设，不因quote有效或异常对应就证明完整版本/依赖/行为义务。

现有oracle仅call_completes+空模型assertion；其他oracle未知。Wrong observation/probe、程序拒绝、原源变化拒绝；错误module/行/exception/keyword、改normal非请求参数、bool/int混同、编译probe不同、开放签名、隐式域等不支持。用三个合成API名验证规则是数据驱动，不当三条真实任务或新独立样本。

所有分支`full_issue_obligations_verified=false`、`trusted_reproducer=false`；子义务支持数不报可信率或repair rate，不回填旧资格/Gold。冻结本分类器不是完整live方法freeze，不接付费、不给新canary放行。专项/Ruff通过后一次四缓存审计，之后再设计完整义务覆盖与必要probe操作，不按task-ID补规则。

当前仍不开canary/TEST/C5/Fresh30/privateTest500/repair/E2，不动Docker/IPC/VHD/registry/proxy/tunnel/key，无下载需求；未来新付费命令必须另列Flash/次数/≤100,000 tokens/retry0。
