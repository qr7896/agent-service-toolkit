# E1-C DEV 已有模型补丁合并：12 对零模型筛选

2026-09-24，Docker grade 前冻结。v4.2 首次验证两个分别未过目标但回归全保持的模型候选，可在非重叠 hunk 处机械组合并通过官方检查。此批在现有所有公开 DEV 的已评分模型 patch 中，排除已有 resolved 任务、无效 SHA/source identity/test path，选择同题非重叠 patch 对；若两候选目标 F2P 都为0，则必须都维持全部 P2P。按原 manifest 次序、评分和路径排序，每题最多2对、全批最多12对，并按 diff SHA 去重。运行中 `git apply --check` 再实际合并，冲突仅记录不修。

- 身份 `e1c-dev-patch-union-batch1-20260924`，入口 `uv run --frozen python -X utf8 -m evals.e1c_dev_patch_union run`，runner SHA-256 `afc7a5ad692d662116637311930d823a3130841ee9ead68cbf5020a61c58342`，manifest SHA-256 `7d8e6569054195d8d68b406b1e51b9d43778b3b9699df4bc8c3672aa049a4435`。零模型预检 ready，固定12对覆盖8个未解任务；每对完整原 patch 路径与 SHA 由 `identity.json` 在任何 grade 前落盘。
- 最多12次 Docker grade，provider calls=0/tokens=0；一题某对 resolved 后跳过其后对。全部候选来自此前模型，绝不看 gold patch 或 E1-B sealed TEST。不将最佳组合当作单次模型修复，更不作为独立泛化结果。
