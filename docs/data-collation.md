# Data Collation Guide

This document defines how the built-in Zhouyi/Yijing corpus should be expanded without breaking the long-term data model.

The goal is not to make the first alpha release text-complete. The goal is to make every later text-completion change traceable, reviewable, and testable.

## 1. Principles

1. Keep the data layer stable before adding advanced divination systems.
2. Prefer structured JSON over free-form notes.
3. Preserve placeholders explicitly instead of silently omitting records.
4. Every classical text item should eventually have a `source_id`.
5. Text completion and interpretation-rule changes should be reviewed separately.
6. Do not mix unverifiable modern interpretation with classical source text.

## 2. Core files

The current corpus is stored under `nonebot_plugin_yijing/data/`.

| File | Purpose | Current expectation |
|---|---|---|
| `trigrams.json` | Eight trigram metadata | Complete seed data |
| `hexagrams.json` | 64 hexagram metadata and binary structure | Complete seed data |
| `lines.json` | 384 structural line slots | Complete structural skeleton |
| `guaci.json` | Hexagram judgments | Seed text, gradually verified |
| `yaoci.json` | 384 line texts | Placeholder allowed during alpha |
| `tuan.json` | Tuan Zhuan | Placeholder allowed during alpha |
| `xiang.json` | Xiang Zhuan | Seed text, gradually verified |
| `wenyan.json` | Wenyan Zhuan | Placeholder allowed during alpha |
| `xici_shang.json` | Xici Zhuan, upper | Placeholder allowed during alpha |
| `xici_xia.json` | Xici Zhuan, lower | Placeholder allowed during alpha |
| `shuogua.json` | Shuogua Zhuan | Placeholder allowed during alpha |
| `xugua.json` | Xugua Zhuan | Placeholder allowed during alpha |
| `zagua.json` | Zagua Zhuan | Placeholder allowed during alpha |
| `relations.json` | Hexagram relations | Must reference valid hexagram sequences |
| `sources.json` | Source registry | Required for traceability |
| `casting_rules.json` | Casting method metadata | Stable seed data |
| `interpret_rules.json` | Interpretation strategy metadata | Stable seed data |
| `reserved_tables.json` | Reserved future schema topics | Planning only |

## 3. Suggested record states

Use a small lifecycle vocabulary when adding or revising text records.

```text
placeholder -> draft -> checked -> verified
```

Recommended meanings:

- `placeholder`: structure exists, text is not collated.
- `draft`: text has been entered from a source but not reviewed.
- `checked`: text has been checked once against the cited source.
- `verified`: text has been checked against at least one authoritative source and is ready for release notes.

During alpha, placeholders are allowed. After the v0.3.0 corpus milestone, core placeholders should become CI failures for the files declared complete.

## 4. Source policy

Each source should be registered in `sources.json` with enough information to audit where text came from.

Suggested fields for future source records:

```json
{
  "id": "wikisource_zhouyi",
  "title": "周易",
  "type": "classical_text",
  "url": "...",
  "edition": "...",
  "license": "...",
  "notes": "..."
}
```

For classical text records, prefer adding or preserving:

```json
{
  "source_id": "wikisource_zhouyi",
  "status": "checked"
}
```

Do not put modern explanations, divination advice, or LLM-generated prose into classical text fields.

## 5. Editing workflow

A safe text-completion PR should follow this order:

1. Choose one narrow file or one narrow hexagram range.
2. Add or correct source metadata first if needed.
3. Edit the target JSON records.
4. Preserve sequence numbers and positions exactly.
5. Run data tests.
6. Update the changelog or a corpus progress note if the completion is substantial.

Recommended local checks:

```bash
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

## 6. Future validation checks

The current alpha tests verify the basic skeleton. Later validation should add:

- JSON schema validation for every data file.
- `source_id` existence checks for every classical text record.
- Relation target checks for every relation type.
- Placeholder count reports.
- Release-gate rules that disallow placeholders for files marked complete.

## 7. Corpus completion priority

Recommended order:

1. Complete 384 `yaoci.json` line texts.
2. Complete 64 `tuan.json` records.
3. Complete 64 `xiang.json` records.
4. Complete Qian/Kun `wenyan.json` records.
5. Complete `xici_shang.json` and `xici_xia.json`.
6. Complete `shuogua.json`, `xugua.json`, and `zagua.json`.
7. Add modern plain-language explanation files only after classical text has stable source tracking.

## 8. What not to do yet

Do not start these before v0.3.0 data integrity and v0.4.0 interpretation schema are stable:

- Mei Hua Yi Shu rules.
- Liuyao Najia rules.
- Ganzhi calendar.
- Wuxing strength calculation.
- Six relatives / six spirits.
- Scene-specific LLM-heavy interpretation templates.
