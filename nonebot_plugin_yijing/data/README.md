# 易经资料库结构

[English](README.en.md) | [返回项目 README](../../README.md)

本目录按“底层资料库先完整建模、内容逐步校勘补录”的原则组织。数据文件以 JSON 为主，配套 JSON Schema 位于 `schemas/`，用于约束资料结构和后续补录边界。

## 当前状态

当前种子数据可运行：

- 六十四卦名、上下卦、卦序、卦辞和卦关系已经作为完整种子提供。
- 八卦、六爻骨架、来源、起卦规则、解读规则已经建模。
- 384 条爻辞中，乾、坤、需三卦已录入；其余爻位使用占位文本，便于后续人工校勘后逐步替换。
- 彖传、象传、文言、系辞、说卦、序卦、杂卦等经传层级已预留结构，内容随校勘进度补录。

## 核心数据表

| 文件 | 内容 |
| --- | --- |
| `trigrams.json` | 八卦基础资料 |
| `hexagrams.json` | 六十四卦基础资料 |
| `lines.json` | 六爻结构骨架 |
| `guaci.json` | 卦辞 |
| `yaoci.json` | 爻辞 |
| `tuan.json` | 彖传 |
| `xiang.json` | 象传 |
| `wenyan.json` | 文言传 |
| `xici_shang.json` | 系辞上传 |
| `xici_xia.json` | 系辞下传 |
| `shuogua.json` | 说卦传 |
| `xugua.json` | 序卦传 |
| `zagua.json` | 杂卦传 |
| `relations.json` | 卦关系 |
| `sources.json` | 来源与版本信息 |
| `casting_rules.json` | 起卦规则 |
| `interpret_rules.json` | 解读规则 |
| `reserved_tables.json` | 后续扩展表登记 |

## JSON Schema

`schemas/` 中的 schema 用于约束数据文件结构。新增或修改资料时，应优先保持字段稳定，避免为单一资料来源临时添加含义模糊的字段。

重点原则：

- 使用稳定、可复用的 `snake_case` 字段名。
- 经文、传文、注释、现代解释和术数扩展分层存放。
- 来源信息应能够追溯到 `sources.json`。
- 占位文本只用于保持结构完整，替换时应同步更新来源和校勘状态。

## 预留扩展方向

资料库已预留以下方向，具体内容以后续版本逐步补齐：

- 历代注释。
- 梅花易数。
- 六爻纳甲。
- 干支历法。
- 五行旺衰。
- 六亲六神。
- 现代白话解释。
- 场景化解读模板。

## 维护建议

新增资料时建议按以下顺序处理：

1. 确认目标 JSON 文件和对应 schema。
2. 补录或修订资料正文。
3. 在 `sources.json` 中登记来源或确认已有来源可复用。
4. 更新相关校勘状态。
5. 运行数据结构、导入和渲染相关测试。

更多补录流程见 [`../../docs/data-collation.md`](../../docs/data-collation.md)。
