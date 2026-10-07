# 公共API对照的调用前输入摘要 v1（零模型预注册）

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（运行前协议）
- Version Label: caller_input_pair_v1

命令：`uv run --frozen --offline python -X utf8 -m evals.e1c_evaluation_2_pair_input_observer audit-dev`。provider calls/tokens=0/0，Gold读取0。新namespace `.codex/e1c/evaluation_2/pair-input-observation-zero-v1/`存在即拒绝重跑；仅诊断原四缓存中语法准入的公共normal/target API对照，不手选task/文件，不生成新模型probe、不改变旧评分。

原producer seal和全部生产侧文件SHA先核验；复用公开works-for/but-not-for语法与来源解析，自动找固定两API及原normal/target脚本。目标可能在参数装饰器中被拒，因此观察点为原probe单一顶层调用行之前，而不是假称进入生产函数体。只支持所有参数均为local Name或Constant的无副作用调用；共享keywords及positional均列出，不遗漏未知接收对象。

在两个新离线只读容器中各运行一次已封存原normal/target probe，独立readonly挂载；复用transport、官方等价冻结image、nonce/源SHA/90秒硬超时。network none/pull never，不需要下载；生产API文件须runtime原字节==exact-base Git blob==host LF投影。两个原probe字节不改，不重新运行旧实验namespace，不自动retry。

快照仅输出类型/typed SHA/origin，不输出参数值或repr/getattr。精确builtin primitive/list/tuple/string-key dict支持，限制深度4/nodes64/string8192/int2048bits；循环、subclass、custom对象未知。仅精确ndarray的数值/固定字符串kind `biufcSU`且≤64KiB支持，摘要包含dtype/shape/C-order bytes；object、void、StringDType等保持unknown。C-order原始bytes及kind分类依据[NumPy tobytes](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.tobytes.html)、[dtype.kind](https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html)；摘要方案是本项目限定设计，不是NumPy提供的语义相等证书。

normal须rc0、target须rc1且各单一快照；两个角色每个共享keyword的typed SHA相同才`shared_keywords_supported`。positional/custom对象未知则`all_inputs_match=false`，不能改叫所有输入一致。frozen literal与实际local分别标origin。hash摘要相同仅支持捕获瞬间的限定表示一致，不证明原公开fixture、callee被执行、装饰器未改参数、完整行为/语义或抵抗恶意Python；低熵hash不是保密加密。

专项/Ruff通过后才执行。固定4缓存/DEV12分母，其他任务not applicable，失败保存freeze/driver/log/failure。成功也不提升machine trusted；随后有限行为义务及反例校准、完整method freeze/同版DEV。不开canary/TEST/C5/Fresh30/privateTest500/repair/E2，不动Docker后台/IPC/VHD/registry/proxy/tunnel/密钥。
