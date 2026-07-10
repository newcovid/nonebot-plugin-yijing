# Data Collation Guide

This document defines how the built-in Zhouyi/Yijing corpus should be expanded without breaking the long-term data model.

The goal is not to make every release text-complete. The goal is to make every later text-completion change traceable, reviewable, and testable.

## 1. Principles

1. Keep the data layer stable before adding advanced divination systems.
2. Prefer structured JSON over free-form notes.
3. Preserve placeholders explicitly instead of silently omitting records.
4. Every classical text item should eventually have a `source_id`.
5. Text completion and interpretation-rule changes should be reviewed separately.
6. Do not mix unverifiable modern interpretation with classical source text.
7. Keep canonical classical text, historical commentary, modern explanation, and LLM output in separate layers.

## 2. Core files

The current corpus is stored under `nonebot_plugin_yijing/data/`.

| File | Purpose | Current expectation |
|---|---|---|
| `trigrams.json` | Eight trigram metadata | Complete seed data |
| `hexagrams.json` | 64 hexagram metadata and binary structure | Complete seed data |
| `lines.json` | 384 structural line slots | Complete structural skeleton |
| `guaci.json` | Hexagram judgments | Script-fetched from public source, ready for later multi-source proofreading |
| `yaoci.json` | 384 ordinary line texts | Script-fetched from public source, ready for later multi-source proofreading |
| `special_texts.json` | Special texts outside ordinary six-line slots, such as 用九 / 用六 | Small canonical seed file |
| `tuan.json` | Tuan Zhuan | Script-fetched from public source, 64 records |
| `xiang.json` | Xiang Zhuan; `daxiang` plus structured `xiaoxiang` line records | Script-fetched from public source, with six structured `xiaoxiang` records per hexagram |
| `wenyan.json` | Canonical Wenyan Zhuan | Script-fetched and limited to Qian and Kun |
| `xici_shang.json` | Xici Zhuan, upper | Script-fetched and split by chapter |
| `xici_xia.json` | Xici Zhuan, lower | Script-fetched and split by chapter |
| `shuogua.json` | Shuogua Zhuan | Script-fetched and split by chapter |
| `xugua.json` | Xugua Zhuan | Script-fetched and split by section |
| `zagua.json` | Zagua Zhuan | Script-fetched as one section |
| `relations.json` | Hexagram relations | Must reference valid hexagram sequences |
| `sources.json` | Source registry | Required for traceability |
| `casting_rules.json` | Casting method metadata | Stable seed data |
| `interpret_rules.json` | Interpretation strategy metadata | Stable seed data |
| `reserved_tables.json` | Reserved future schema topics | Planning only |

Schema files live under `nonebot_plugin_yijing/data/schemas/`. `schemas/manifest.json` maps each data file to its schema. The manifest is the source of truth for corpus coverage checks.

## 3. Canonical text layer boundaries

The corpus must keep these layers separate:

| Layer | Examples | Storage |
|---|---|---|
| Canonical Zhouyi text | 卦辞、爻辞、用九、用六 | `guaci.json`, `yaoci.json`, `special_texts.json` |
| Ten Wings / received commentarial canon | 彖传、象传、文言、系辞、说卦、序卦、杂卦 | Dedicated JSON files |
| Historical commentary | 王弼、孔颖达、程颐、朱熹等 | Future `dynasty_commentaries` schema |
| Modern explanation | 白话解释、场景建议、风险提示 | Future `modern_explanations` / `scenario_templates` |
| Runtime interpretation | LLM or local generated answer | ORM record JSON, not corpus files |

Do not put modern advice or LLM-generated interpretation into classical text fields.

## 4. Record states

Use a small lifecycle vocabulary when adding or revising text records.

```text
placeholder -> draft -> checked -> verified
```

Legacy data also contains `seeded` for early seed records. New data should prefer:

- `placeholder`: structure exists, text is not collated.
- `draft`: text has been entered from a source but not reviewed.
- `checked`: text has been checked once against the cited source.
- `verified`: text has been checked against at least one authoritative source and is ready for release notes.

Until the v0.3.0 corpus milestone, placeholders are allowed. After that milestone, core placeholders should become CI failures for the files declared complete.

## 5. Source policy

Each source should be registered in `sources.json` with enough information to audit where text came from.

Recommended source fields:

```json
{
  "id": "wikisource_zhouyi",
  "name": "维基文库《周易》",
  "title": "周易",
  "type": "classical_text",
  "url": "...",
  "edition": "...",
  "license": "...",
  "usage": "...",
  "notes": "..."
}
```

For classical text records, prefer adding or preserving:

```json
{
  "source_id": "wikisource_zhouyi",
  "status": "checked",
  "edition": "...",
  "source_locator": "乾卦/九二",
  "collation_notes": "..."
}
```

## 6. File-specific rules

### `xiang.json`

`daxiang` remains a hexagram-level text field. `xiaoxiang` must be a list of per-line objects, not a dictionary and not a free-form string list:

```json
{
  "position": 1,
  "line_label": "初九",
  "text": "...",
  "source_id": "wikisource_zhouyi",
  "status": "checked"
}
```

### `wenyan.json`

The canonical `wenyan.json` layer is limited to Qian and Kun. Do not add 64 generic Wenyan placeholders. Later dynasty or school-specific explanations for other hexagrams should go into a commentary layer.

### `special_texts.json`

Use this file for texts that are canonical but not one of the six ordinary line positions. Current examples:

- 乾：用九
- 坤：用六

### Chapter text files

`xici_shang.json`, `xici_xia.json`, `shuogua.json`, `xugua.json`, and `zagua.json` should eventually be split by chapter or section. One giant text block should be avoided because it is hard to cite, render, and feed into LLM prompts safely.

## 7. Editing workflow

A safe text-completion PR should follow this order:

1. Choose one narrow file or one narrow hexagram range.
2. Add or correct source metadata first if needed.
3. Prefer updating and rerunning `scripts/fetch_wikisource_corpus.py` for canonical text changes.
4. Edit the target JSON records only for reviewed metadata or fields that are not public-source text.
5. Preserve sequence numbers and positions exactly.
6. Run data tests.
7. Update the changelog or a corpus progress note if the completion is substantial.

Recommended local checks:

```bash
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

## 8. Validation checks

Current and future validation should cover:

- JSON syntax for every data and schema file.
- Schema manifest coverage for every core data file.
- `source_id` existence checks for every classical text record.
- Relation target checks for every relation type.
- Placeholder count reports.
- Release-gate rules that disallow placeholders for files marked complete.

## 9. Corpus completion priority

Recommended order:

1. Complete 384 `yaoci.json` line texts.
2. Complete 64 `tuan.json` records.
3. Complete 64 `xiang.json` records, including structured `xiaoxiang`.
4. Complete Qian/Kun `wenyan.json` records.
5. Complete `xici_shang.json` and `xici_xia.json` by section.
6. Complete `shuogua.json`, `xugua.json`, and `zagua.json`.
7. Add modern plain-language explanation files only after classical text has stable source tracking.

## 10. What not to do yet

Do not start these before v0.3.0 data integrity and v0.4.0 interpretation schema are stable:

- Mei Hua Yi Shu rules.
- Liuyao Najia rules.
- Ganzhi calendar.
- Wuxing strength calculation.
- Six relatives / six spirits.
- Scene-specific LLM-heavy interpretation templates.
