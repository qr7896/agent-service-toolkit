# 零调用合同恢复与生成式 runtime 定位：已完成结果

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent; implementation: ponytail
- Origin Mode: run
- Origin Date: 2026-10-07
- Verification Status: VERIFIED（仅本页列明的离线运行/缓存区分/组件验证；不代表研究达标）
- Version Label: contract-recovery-results-20261007

## 实际成果

本轮新增模型调用0、tokens0。原付费v1/v3/v4与所有旧实验封板原件不改，费用仍旧29请求70977tokens；本轮不把新结果回填旧成绩，也不补收费角色。

同三个旧DEV各第一份probe：v1表达式语法解释＋已有生产构造前沿得到1个重复失败候选/独立Gold区分1；v2增加生产格式正常对照后得到**2个候选/Gold区分2（screen3、原DEV分母12）**，分别SK13496与MM1252，两次control均通过后target重复失败。pytest原合同的自然语言CLI仍是invalid Python，本轮没有把它强行改写成可执行代码。新变化是task无关的源码/合同编译器，未按task ID指定文件/修数值或日期，target/预期不由Gold生成。

这是**缓存开发恢复，不是新生成、独立canary或Agent修复率**。自动trusted仍0；Gold区分不自动证明issue全语义。SK主要验证请求的constructor option，不能凭它说全部增量树行为已验证。MM目标保留原Z字符串，但新control时区/表示可不同，source-format receiver证据不等于实际target绑定证明。2/3缓存不能开启独立门槛。

机器收据：[数据与所有SHA](../../data/e1c_evaluation_2_contract_recovery_result.json)。本机完整原件分别`contract-recovery-zero-dev-v1`、`contract-recovery-zero-dev-v2`、`generated-skip-component-zero-v1`、`generated-runtime-location-zero-v1`，都在`.codex/e1c/evaluation_2/`下。producer先freeze/完成并seal，再独立Gold；已有zero/gold入口不再执行。原响应/评分类材料不上Git。

## 验证的机制与边界

1. **比较语法：** 原`n2 == 20`是predicate，不是Assert语句。新协议把单Compare包成Assert，predicate AST/变量/数字/运算符/quote不变。明确不宣称原无Assert程序与新程序执行等价；旧invalid记录保持原样，不弱化旧验证器。
2. **构造前沿：** 复用已有production signature规则识别unsupported constructor kwarg；setup＋完整target_action AST在移动前后恒等，oracle/control不改。SK已在实际容器证明控制成功、原target故障发生在constructor、Gold后通过。没有人工定目标文件或重写target。
3. **对照格式：** MM首次失败在control_action，不在setup；trace→生成AST定位已反驳“盲目移动setup”的猜测。算法从已选SHA验证生产文件中收集stdlib strptime静态时间格式，按固定path/line顺序生成一个正常control，原Z target不变；实际两次正常、target失败、独立Gold通过。v2 proof中的`issue_quotes_or_control_changed=false`只描述构造前沿子阶段，**整个v2确实替换control**，由`source_format_control.original_control_replaced=true`记录；不回填原JSON掩盖范围差别。
4. **受限native组件：** 可信controller driver只写自己/tmp临时case，固定一个显式文件、空config、noconftest、confcutdir、插件autoload禁用、No network/pull/只读sandbox；模型不能给shell/path/plugin/config。当前只支持单一unconditional skip/Pass，非通用pytest fixture、尚未接Agent工具，也未解除旧native guard。没有冒充model safe_static_check证书；只复用底层Docker command builder并独立登记controller driver身份。
5. **自动runtime定位：** 两次CLI输出中，正常flags定位generated_case.py:3，runxfail定位生产skipping.py:239；只解析自有driver receipt，绑定log/module/image/base SHA，将位置规范化并拒绝原test/docs/hidden/conftest/越界/伪造tmp根。自动取到src/_pytest/skipping.py:233开始的窗口，**没有人工选择生产文件**。输入fixture是开发者写的synthetic，不能当第3条模型解题成功或3/3成绩。
6. **预算negative：** 无损重叠窗口编码往返JSON完全一致、未加源内容或丢provenance。实际原budget stop点10700→10694，只省6预留tokens，仍高于余额10087，不解决budget瓶颈，不接live，也不降低reserve去凑通过。保存原型/negative；模型能否正确理解wire引用格式尚未验证。

## 下一步唯一顺序

1. 把comparison/frontier/source-format compiler接入**另立**统一DEV runner，完整保留原控制与raw→canonical→execute的provenance，unknown明确停止。旧frozen模块不改，不能把cache成绩称新生成。
2. 新native动作必须用machine-readable case_source/flags与来自公开issue的有效quote/预期绑定，不把旧自然语言CLI自动翻译。先补受限fixture规范、权限/身份验证和与独立评分的接口；现组件仅skip profile，不能宣称支持所有pytest。原native guard继续保留，未知/注入fixture拒绝。
3. 零调用验收/完整回归/跨仓库机制过关后另冻方法和预算，先列精确Flash命令；四参考/完整旧DEV同版验证未完成，不直接选新canary。source-format/control与原baseline分别记录，不best-of。
4. 只有真实新生成开发证据通过才预注册不重叠独立canary，一次≥2/3且行为一致后另冻Agent patch与official repair grade，最后同版对照及全新任务。现TEST/C5/Fresh30/private Test500/Agent repair/E2仍关闭，不能承诺一周30/30。

Cloud可接编译器/单测/文档；缺本机exact source/cache/image/runtime即INFRA_BLOCKED，不索取key或开裸daemon；当前tunnel旧strict-v5白名单未扩大。Docker/VHD/registry/代理/tunnel/key与所有旧IPC备份保留，本轮无重启、删除、下载或新付费。

最终工程：15项grammar/source-frontier、23项含source-format、4项lossless、11项generated-only harness、13项runtime定位边界专项分别通过；规定预算/V3重点18passed、Ruff与原V3 preflight ready=true。完整单次1292passed/4skipped/33warnings/0failed（61.87秒；XML1296tests/0errors/61.815秒），不弱化旧断言/skip/timeout、不是修复率。三个first-probe的issue_quote/expected_quote均核验在投影公开issue中；pytest被拒绝原因是English动作非Python，不是quote不存在。所有已经开始的zero/gold/component/audit命令保留原件并禁止重跑。
