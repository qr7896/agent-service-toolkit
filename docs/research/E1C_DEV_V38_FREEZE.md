# E1-C DEV v3.8：AlterField 完整窗口单题验证

2026-09-24，付费调用前冻结。v3.5 的 `django__django-11740` 三次 `old text must occur exactly once`，审计显示其首轮补丁把原 base 的 `field=field` 写作 `field=new_field`；v3.5 的原窗口在该调用前被3,800字符限制截断。v3.8 是实质性的证据修正，不是原提示再抽样。

- 身份 `e1c-dev-v38-alterfield-window1-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_v38 run`，launcher SHA-256 `7fa3f57dcd0b5b614e907de60a1460c173e309ef14049a024e84a47a39f39c01`，复用未修改 v3.3 engine；manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。
- 只处理该1条公开历史未解 DEV 任务。公开题面、base-fail 断言和原 base `autodetector.py` 的三个局部窗口入模；第一个窗口显式包含 `AlterField(field=field)` 完整调用，第二个包含 FK 依赖 helper，第三个包含 `add_operation`。不读取 gold patch/sealed TEST。研究者人工校正定位，不能宣称自动定位收益。
- DeepSeek `deepseek-flash` non-thinking、non-streaming、直连、SDK retries=0；最多2次请求、输出≤1,800、单题≤22,000 provider tokens；候选 exact edits、旧 patch 去重、官方 Docker grade。首轮预算预留6,426/22,000，零调用预检 ready，Ruff clean，run目录不存在。没有净新 resolved 则不对该提示再抽样。
