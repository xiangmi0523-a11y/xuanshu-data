# xuanshu-data · 玄枢契约与基准数据正本

这个仓库是玄枢**契约文本、B4 回归基准数据和它们的生成脚本**的唯一正本。
这里不放排盘引擎代码（引擎另起仓库，且不得引用本仓库的生成脚本【B4-11】）。

## 三条规则

1. **只认仓库里的版本。** 云端硬盘、聊天附件、各个 AI 环境里的副本都只是副本；哪份是正式的，看 `manifest.toml`。
2. **结论写成断言。** 契约里的常量和已定结论只在 `constants.toml` 写一次；`checks/verify.py` 每次提交都把它们跑一遍，数据和结论对不上，CI 就变红。
3. **一个执笔，其余审阅。** 同一时间只有一个 AI 提交改动；其他 AI 读仓库、在 Issue / PR 里提意见；用户只拍板。不再在聊天之间转贴原文。

## 目录

| 路径 | 内容 |
|---|---|
| `manifest.toml` | 正本清单：每个文件的 sha256、行数、状态（formal / recheck / source / pending） |
| `constants.toml` | 常量与已定结论：子时窗口、叠加用例年份、金值、年历舍入跨日等 |
| `checks/verify.py` | 核对脚本（唯一判据） |
| `ephemeris/` | JPL DE440s 星历 |
| `jieqi/` | 节气基准表（Skyfield 版，B4 正式）与生成脚本 |
| `b4-data/` | 日柱序列：正式文件（待放入）与 `recheck/` 独立复算件 |
| `almanac/` | 紫金山日历比对材料 |
| `contract/` | 契约 md 正文（待放入） |

## 怎么看对不对

- 手机上：打开仓库 → **Actions** → 最新一次"核对数据"，绿色 = 全部通过；点进去看汇总，⏳ 是待补项，❌ 是失败项。
- 本地：`python3 checks/verify.py`（几秒）；加 `--regen` 会用生成脚本重跑并比对哈希（需 `pip install skyfield==1.55`）。

## 改数据的流程

1. 改文件（或放入新文件）。
2. 同一次提交里更新 `manifest.toml` 的 sha256 / 行数；如果改的是已定结论，同时改 `constants.toml`。
3. 提交说明写裁决号，例如 `B4-15: 1923 雨水、1979 大寒以基准表为准`。
4. 等 CI 变绿。红了就是哪里没对上，不合入。

## 当前待补（CI 里显示为 ⏳）

- `b4-data/day_pillars_1900_2100.csv`（契约登记 sha256 `374922ef…`）及其生成脚本 `b4-data/gen_day_pillars.py`
- `almanac/zjs_terms_1900_2025_extracted.csv`（契约登记 sha256 `ee87a53d…`），放入后补比对器
- `contract/` 下的契约 md 正文

B4 仍未解除。
