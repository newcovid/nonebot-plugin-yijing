# I Ching Data Corpus Structure

[简体中文](README.md) | [Back to project README](../../README.en.md)

This directory follows the principle of modeling the underlying corpus first, then gradually proofreading and filling in content. Data files are mainly JSON. JSON Schemas live in `schemas/` and define the structure and boundaries for future corpus work.

## Current Status

The current seed data is runnable:

- Hexagram names, upper/lower trigrams, sequence numbers, hexagram statements, and hexagram relations are provided as complete seed data.
- Trigrams, line skeletons, sources, casting rules, and interpretation rules are modeled.
- Among the 384 line texts, Qian, Kun, and Xu have been entered; the other line positions use placeholder text so they can be replaced after manual proofreading.
- Tuan, Xiang, Wenyan, Xici, Shuogua, Xugua, Zagua, and related classical-text layers have reserved structures and will be filled according to proofreading progress.

## Core Data Files

| File | Content |
| --- | --- |
| `trigrams.json` | Eight trigram data |
| `hexagrams.json` | Sixty-four hexagram data |
| `lines.json` | Six-line structure skeleton |
| `guaci.json` | Hexagram statements |
| `yaoci.json` | Line statements |
| `tuan.json` | Tuan commentary |
| `xiang.json` | Xiang commentary |
| `wenyan.json` | Wenyan commentary |
| `xici_shang.json` | Xici, Part I |
| `xici_xia.json` | Xici, Part II |
| `shuogua.json` | Shuogua commentary |
| `xugua.json` | Xugua commentary |
| `zagua.json` | Zagua commentary |
| `relations.json` | Hexagram relations |
| `sources.json` | Source and edition metadata |
| `casting_rules.json` | Casting rules |
| `interpret_rules.json` | Interpretation rules |
| `reserved_tables.json` | Registry for future extension tables |

## JSON Schema

Schemas in `schemas/` constrain the structure of the data files. When adding or editing corpus data, keep fields stable and avoid adding vague source-specific fields for one-off cases.

Key principles:

- Use stable, reusable `snake_case` field names.
- Store canonical text, commentaries, annotations, modern explanations, and traditional-method extensions in separate layers.
- Source information should be traceable through `sources.json`.
- Placeholder text is only for structural completeness. When replacing it, update source and proofreading status at the same time.

## Reserved Extension Areas

The corpus has reserved space for these future areas:

- Historical annotations.
- Meihua Yishu.
- Six-line Najia.
- Ganzhi calendar data.
- Five-phase strength and weakness.
- Six kinships and six spirits.
- Modern plain-language explanations.
- Scenario-based interpretation templates.

## Maintenance Notes

Recommended workflow for adding data:

1. Confirm the target JSON file and corresponding schema.
2. Add or revise the corpus text.
3. Register the source in `sources.json`, or confirm that an existing source can be reused.
4. Update related proofreading status.
5. Run data-structure, import, and rendering-related tests.

See [`../../docs/data-collation.md`](../../docs/data-collation.md) for the broader collation workflow.
