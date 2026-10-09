# 配对执行 DEV v2：事前兼容解码、真实依赖条件、继续旧DEV

日期2026-10-09。原pair v1为1/2；后验精确解码另1/1，原结果不改。新版本不重跑原两题，不抽canary或Fresh30。

## 输入与确定性选择

零调用`prepare`只检查frozen DEV12的本机已缓存公开issue、exact-base生产源码、不可变镜像与已存在双准入摘要。仅读取公开issue blob ID与base/Gold阶段通过布尔值，不读取断言/补丁/官方日志作定位。缺source/issue记INFRA_BLOCKED，不下载、不复制容器源码或变更Docker。固定12行，不将缺材料记模型失败。

相同任务无关方法处理所有可用来源：balanced lexical/structural各最多4窗口→public backtick限定名补证→有界loaded globals→排除benchmark/examples→canonical输入重算。逐window核验host摘要、LF/base blob与原切片cap（lexical2200、连续AST5000、signature/body2500）。边界/32k字符预算保持。静态globals不是runtime值证书。

新两题pilot选择规则：按原DEV12顺序，排除**上一pair v1所有已尝试task**（不看成功/失败），从每个剩余repo取第一条已双准入、ready来源，选最先两个repo。不排序官方结果、不人工挑文件、不读新独立任务。所有source/input、公开元数据、准入摘要与前次两题身份绑定SHA；不是未见独立canary。

## 统一方法

沿用fresh pair的生成→重复离线执行→conditional gate→模型patch→原probe自验证→全生成seal→独立official。复用纯函数/显式row/root，不改变原模块OUT/preflight、不改旧frozen源。

1. repair调用返回raw/usage先保存，**在编译前**使用已有精确canonical_response：只有恰为type+edits且type=json_object才删元字段；否则必须只有edits。canonical与removed标记单独保存；path/old/new字符串不变，unknown字段继续拒绝。这不是事后按得分决定解码。
2. probe严格三keys，不新增任意JSON修复。新增通用静态门槛：拒绝重绑导入名、直接或简单Name别名写导入namespace（含setattr/delattr）；允许构造后对象参数改变。prompt明确不改library可用性guard。optional条件由已有公开issue/import推断的真实容器blocker提供。
3. normal×2通过、target×2稳定rc1且无setup异常仅为operational pair。公开语义义务/环境忠实性仍未完全自动认证；full_issue_trusted保持false，不能直接开canary。
4. strict暴露old/base唯一/AST/生产路径/补丁预算保持；不改probe/断言，不回流official答案。新模型与产物全部封存、核验SHA及方法freeze后才显式调用既有独立评分器。

静态namespace检查只覆盖限定结构，不称通用程序语义或恶意代码证明；既有无网络容器/host只读/cap-drop/pull-never仍是执行边界。正常fixture的对象属性调整不等于改写生产模块。

## 单批预算与命令

只授权新两题pilot，不暗中展开全部九准入：Flash enabled/high/no-tools，最多4calls/100,000 provider tokens含推理；每题2calls/50k，输出预注册16k–20k按实际余量；HTTP300、probe90、official900、retry0。第一题全局cap50k保留后一题50k。余量不够16k不请求，SDK/使用量不明或容器infra中断整批，不自动扩大额度或重试。

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_pair_dev_v2 prepare
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_pair_dev_v2 preflight
```

上述为零调用；prepare一旦创建不能改写或重跑。新付费命令必须按仓库AGENTS精确授权：

```powershell
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_pair_dev_v2 run
```

paid启动前检查freeze/实际首消息SHA/engine+immutable images；started/ledger存在拒绝重跑。`--offline`是uv依赖约束，模型请求仍需网络；验证容器network none。

本批同版固定2分母，DEV12的12行仅是输入/准入准备，不叫12题生成/修复完成。之后扩九准入必须另冻结整体cohort与**总**预算，不能隐瞒多个100k子批，不能拼跨版最好分数。公开行为缺证验收→新独立canary≥2/3→repair/DEV对照→另授权Fresh30/E2，未过门槛不打开。本轮不改Docker/IPC/VHD/proxy/tunnel/key，不下载删除重要材料，不保证30/30或一周完美。
