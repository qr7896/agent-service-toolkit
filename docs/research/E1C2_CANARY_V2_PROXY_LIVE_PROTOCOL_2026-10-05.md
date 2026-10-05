# 第二批 canary：传输修订后的 Flash 一次执行协议

日期：2026-10-05。三张镜像完成不可变 image ID 核验，六项官方 Base/Gold 离线准入均通过；三条公开 issue 与 exact-base 生产源码已按原方法自动物化，各四个源码窗口。生成侧不读取官方评分文件、Gold 或 grader 日志。

固定样本仍为 v2 原选三题，分母3、无替补。原14份方法文件和原选择身份保持逐字节冻结；本轮仅新增桥接适配器，将原 v4 路由/提示/静态审计/离线执行器接到 `canary-v2-metadata-proxy-v1` 产物目录。它是同一 cohort 的已声明基础设施修订，不是新抽样或在结果后修订生成机制。

执行身份：`e1c2-independent-canary-v2-metadata-proxy-v1-flash`。冻结除原生成方法、issue-only 输入、不可变镜像、预算外，还绑定传输修订/传输seal、本协议、桥接/Gold适配器、六份官方准入结果的SHA。原 v2 live freeze/state/ledger 不写入或复用。

模型仅 `deepseek-flash`，non-thinking、temperature0、输出单次≤2600，SDK retries0。三题各最多一次请求，每题硬上限14,000 provider tokens，整批42,000；估计提示tokens×1.4+最大输出作为预留，放不下则原位计预算失败。没有模型失败重试、备用模型、第二候选或预算挪用。公开输入不足时弃答，固定分母保留。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_live preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_live run
```

preflight 为零调用。run 是新的精确付费命令，须按当前用户授权和仓库 AGENTS.md 核验后才执行。模型 API 客户端 `trust_env=False`，不使用官方元数据的7892代理。容器 `--network none --pull=never`，凭据不挂载。候选生成后先锁定源码SHA，两次base失败仅形成候选；其后独立grader使用同一候选作Gold区分：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_canary_v2_proxy_gold
```

Gold区分和公开issue语义审核都通过才计可信；现有语义审核仍包含人工判断，须披露，不回填旧生成器的`trusted_reproducer=false`。固定三条可信复现≥2/3才过门槛，不能把未运行/环境失败从分母移除。失败封存，返回旧DEV改通用方法，已看过样本不重称独立；成功后另冻Agent修复配对协议。sealed TEST/C5/Fresh30仍关闭，Gold-Pass或工程测试通过不等于Agent修复成功。
