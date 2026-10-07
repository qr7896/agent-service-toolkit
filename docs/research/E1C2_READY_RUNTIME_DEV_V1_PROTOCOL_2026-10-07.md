# Readiness 四参考 DEV：执行前协议

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent；ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: UNVERIFIED（质量结果另存，不回填协议）
- Version Label: ready-runtime-reference-dev-v1

本轮止损：不再直接扩九题/抽canary。仅原DEV四条已用于调参的固定参考，顺序SK13496、SK26289、MM1252、MM1359。原固定分母12、九准入、screen4必须分开报告，绝不叫独立4题或完整DEV12。历史3/12与1/12及所有原响应/账本/冻结/seal保留。

方法身份`evals.e1c_evaluation_2_ready_runtime_dev`，单文件适配原已冻执行器，不改其source：统一probe的五string＋两integer ref格式，兼容精确旧string引用；仅已知单层json_object/content dict包装解码，extra/string/递归/未知拒。原文按已有catalogue的同ID原text无损显示为紧凑pairs，保留所有字符与生产窗/公开fixture事实。一次实际Assistant/observation；只删除与实际上一probe/observation完全相同的重复字段，不删不同的previous_probe，源/预期不丢。语法/来源合法不能证明期待忠实。

前版compiler/control/target执行/安全边界不改；新readiness在root选择前绑定probe/execution源SHA，Assert比较求值TypeError等只记不可信诊断并反馈，不作为predicate false终止选定；construction/API位置异常留unknown，不一刀切否认功能缺陷。oracle仍锁定，修fixture消费只能据生产源码，不改expected/assertion。完整程序和人工未选择源码路径边界不变。两次相同canonical行动且均rejected/control_failed/oracle求值错误/target不复现，第三调用前停止；不因新source/read或不同fixture提前停，provider/infra失败仍原fail closed不retry。

生成器禁止原tests/Gold/assertion答案/网络/shell/写文件/native pytest harness。当前native组件仍仅历史合成，不伪造证书接现评分。正常control必须base支持，不能与target同故障配置；公共示例输入类型/数值要保真，未知弃答。没有新增自动“补到过”的数值、返回属性、constructor keyword或task规则编译器。

先所有已有两批响应零调用codec审计（不按Gold挑），candidate自身readiness审计（不读Gold）、专项/Ruff/完整回归/规定V3 plumbing，再真实两仓库smoke。通过后method/input/source/protocol/预算freeze并提交代码，再列唯一精确付费命令。全batch50000 provider tokens、每题20000、输出2000、至多16/题4、Flash only/thinking off/温度0、reserve1.4与未跑题首reserve保护、retry0。不借旧预算或在已有namespace再run。

```powershell
# 工作目录 D:\codex\working\project20260827，各阶段仅一次
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_ready_runtime_dev smoke
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_ready_runtime_dev preflight
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_ready_runtime_dev run
uv run --frozen --offline python -u -X utf8 -m evals.e1c_evaluation_2_ready_runtime_dev gold
```

`.codex/e1c/evaluation_2/ready-runtime-reference-dev-v1/`独立原件，smoke另目录。`uv --offline`仅禁止取包；paid run仍DeepSeek HTTPS，验证容器network none/read-only/pull never。原样producer seal先于Gold判别，评分不反馈生成，机器trusted仍false。合成smoke不是task score。四参考未全部保留或忠实性/跨仓库无收益，停止paid扩批继续DEV零调用；有收益才另外冻结完整旧DEV/预算，完整gate后才不重叠canary≥2/3、Agent patch/official评分/同版对照/新任务。

不动Docker/VHD/IPC/镜像/registry/proxy/tunnel/key/所有备份，不新下载/删除。sealed TEST/C5/Fresh30/private Test500/E2不打开。旧bridge白名单不扩大，Cloud缺local artifacts/source/image/runtime报告INFRA_BLOCKED，不伪造现场成功或索取key。故障分类是当前通用原型，不承诺一周完美/30题全过。
