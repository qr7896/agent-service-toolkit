# 执行绑定 setup 前沿：零调用旧 DEV 缓存协议

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（结果另存，不回填协议）
- Version Label: runtime-frontier-zero-reference-v1

只用已seal的ready-runtime四参考原响应，以原turn顺序回放，选第一次满足base执行候选条件的程序；不根据Gold选择，不补缺cache。不是新模型生成、不是对新反馈有因果效力的模型回放。原ready10请求32826/Gold2/4保持原件，原固定12/九准入/screen4分开报告，机器trusted不升级。provider0，不使用key/client/HTTP，cache记录原response SHA/upstream usage，新usage0。

仅control_failed且两次真实normal控制均失败，control source SHA/execution SHA与phased setup前缀匹配、相同顶层生成帧位于setup的Assign(Call)，才将该语句及后缀移到target。完整setup+target AST恒等，normal control/quote/oracle/assertion不改。若control读取被移动suffix写入的任何名字则拒绝；该free-name检查只覆盖静态名字，不证明alias/global状态无依赖，不声明control语义等价。trace不可信，不能当语义证书；移动后仍须新的control两次通过与target重复失败，infra/identity/timeout不进入变换。

新目录`.codex/e1c/evaluation_2/runtime-frontier-zero-reference-v1/`，各turn最初控制原件及frontier-validation子目录都保留，不覆盖已开始路径。原候选与证明source/window/image/base/input冻结；producer完成seal后Gold独立判别，任何raw/Gold/测试不进生成模型或Git。pytest native仍不支持，不新增值、返回属性、数组类型或task ID规则。

专项/完整回归先验，通过后仅执行一次以下零模型命令：

```powershell
# D:\codex\working\project20260827
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_runtime_frontier_zero run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_runtime_frontier_zero gold
```

不自动retry容器/模型，已开始入口不重跑；缺源cache明确报告，不从另一turn/batch挑best-of补题。即使cache开发收益，也须完整新live方法/输入/预算另冻，再同四参考真实生成，四参考/跨仓库/忠实性gate后才完整DEV与不重叠canary。sealed TEST/C5/Fresh30/private Test500/repair/E2不打开；本轮不下载/删除/改Docker/VHD/IPC/registry/proxy/tunnel/key/备份。
