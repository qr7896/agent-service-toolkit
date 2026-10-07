# 生产API参数文档与观察类型分账 v1（零调用预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: parameter_doc_contract_v1

命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_parameter_contract audit-dev`；provider calls/tokens=0/0、Gold读取0，不执行新容器。新namespace `.codex/e1c/evaluation_2/parameter-contract-zero-v1/`存在即拒绝；只读pair-input审计所列公共API、生产源码与已观察类型，不手选文件，不改原模型输入/结果。

原producer seal/产物SHA先验证；API source原host SHA与LF/exact-base Git blob相等。仅提取NumPy-style Parameters节中已观察共享keyword的声明行，带源行/路径/SHA；Returns/Examples/断言/输出答案不序列化。有限词汇仅支持list of str与int/float/bool/str；列表元素、其他文档语法等未知。

观察ndarray而文档仅说list of str时报告`observed_type_not_explicitly_documented`，不说“ndarray非法”或“这个task不是bug”。源码文档可能过时，明确公共API改动请求可覆盖当前文档；公共比较报告的completion仍是有条件扩展假设，不能靠normal API接受就认定target承诺同一类型。status只是规格支持缺口，不授machine trusted，不重写Gold或原资格。

这是资格校准前的独立证据，不是已经接入live的完整新方法。专项/Ruff通过后一次审计；不重跑已started namespace，不打开canary/TEST/C5/Fresh30/privateTest500/repair/E2，不动Docker后台/IPC/VHD/proxy/tunnel/key。
