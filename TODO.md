# TODO / Roadmap

> Last roadmap update: 2026-07-10
>
> Current status: Beta. PyPI installation, multi-adapter message export, NoneBot loading,
> ORM migrations, image rendering, and chat commands are covered by the release baseline.

This roadmap tracks public project work only. Do not record private infrastructure
details, real bot IDs, group IDs, hostnames, database paths, access tokens, or
operator-specific deployment notes here.

## Current Baseline

The package currently provides:

- Command parsing with `nonebot-plugin-alconna`.
- Runtime storage through `nonebot-plugin-orm[sqlite]`.
- HTML image rendering through `nonebot-plugin-htmlrender`.
- Permission registration through `nonebot-plugin-access-control-api`.
- Three-coin casting, yarrow-stalk probability simulation, manual input, and random casting.
- Group settings for cooldown, daily quota, duplicate-question window, LLM history window, and LLM enablement.
- PyPI Trusted Publishing for tagged releases.
- CI coverage for linting, compilation, tests, build, and package metadata checks.

Validated release chain:

- [x] Build sdist and wheel.
- [x] Check distribution metadata with `twine check`.
- [x] Publish to PyPI from a GitHub tag.
- [x] Install the published package with `pip`.
- [x] Load `nonebot_plugin_yijing` from a package install.
- [x] Run `nb orm upgrade` and `nb orm check`.
- [x] Verify packaged data, templates, and migrations are available at runtime.
- [x] Run basic chat-command smoke tests.

Remaining major gaps:

- Classical corpus completion and source tracking.
- Stronger LLM output validation.
- Better manual-casting interaction.
- Reuse of recent matching records for repeated questions.
- Product-level visual polish.
- NoneBot Plugin Store listing and adapter-specific compatibility feedback.

## Near-Term Priorities

### P0 - Release Hygiene

- [ ] Keep `CHANGELOG.md` updated for every released version.
- [ ] Confirm each release wheel contains data, templates, and migrations.
- [ ] Submit and maintain the NoneBot Plugin Store listing.
- [ ] Add a release checklist issue template if releases become frequent.
- [ ] Keep public docs free of private deployment details.

### P1 - Tests

- [x] Cover record-card payload construction.
- [x] Cover empty and non-empty history payloads.
- [x] Cover hexagram query payloads for found and not-found cases.
- [x] Cover `record_to_dict()` serialization for loaded records.
- [x] Cover LLM malformed JSON fallback.
- [x] Cover LLM missing-field fallback.
- [x] Cover hexagram relation target integrity.
- [x] Validate the Alembic revision graph for the packaged yijing migrations.
- [ ] Add a regression test for the old lazy-load / `MissingGreenlet` pattern if practical.
- [ ] Add tests for `YIJING_STORE_QUESTION=false`.
- [ ] Add package-content checks to CI or as a dedicated release workflow artifact check.

### P1 - Runtime UX

- [ ] Show a privacy notice the first time a group enables LLM support.
- [ ] Add `--force` or an equivalent override for repeated-question handling.
- [ ] Return the previous record image when a short-term repeated question is detected.
- [ ] Improve question normalization for same-user / same-group / same-topic repeats.
- [ ] Make repeated-question thresholds configurable where useful.

## v0.2.0 - Group-Usable Beta

Goal: improve day-to-day group usage and administrator control.

Implemented settings:

- [x] `易经设置`
- [x] `易经设置 开启`
- [x] `易经设置 关闭`
- [x] `易经设置 冷却 60`
- [x] `易经设置 日限额 10`
- [x] `易经设置 默认 铜钱`
- [x] `易经设置 默认 大衍`
- [x] `易经设置 重复窗口 30`
- [x] `易经设置 历史窗口 120`
- [x] `易经设置 LLM 开启`
- [x] `易经设置 LLM 关闭`
- [x] Validate invalid numeric setting input and render an error image instead of raising.

Remaining interaction work:

- [ ] Show examples during manual-casting sessions.
- [ ] Support timeout and cancel during manual-casting sessions.
- [ ] Let users retry invalid manual input instead of ending immediately.
- [ ] Show per-line parsing before final manual coin rendering.
- [ ] Replace direct six-value yarrow input with a guided flow.
- [ ] Support random static hexagram lookup.
- [ ] Support random observation topics.
- [ ] Decide whether random casts should be stored by default.

## v0.3.0 - Corpus Quality

Goal: make the built-in data layer useful as a structured Zhouyi/Yijing corpus.

Schema and traceability:

- [ ] Define JSON Schema for every data file.
- [ ] Require `source_id` for each classical text item.
- [ ] Add `version`, `edition`, and `collation_status` metadata where appropriate.
- [ ] Add a corpus completeness report.
- [ ] Make data validation part of release gates.

Classical text completion:

- [ ] Complete all 384 line texts.
- [ ] Complete all 64 Tuan Zhuan records.
- [ ] Complete all 64 Xiang Zhuan records.
- [ ] Complete Qian/Kun Wenyan Zhuan records.
- [ ] Complete Xici Shang.
- [ ] Complete Xici Xia.
- [ ] Complete Shuogua Zhuan.
- [ ] Complete Xugua Zhuan.
- [ ] Complete Zagua Zhuan.

Data integrity:

- [x] Ensure `hexagrams.json` has sequences 1-64.
- [x] Ensure every hexagram has six structured line records.
- [x] Ensure core JSON files can be loaded from package resources.
- [x] Ensure every relation target references an existing hexagram.
- [ ] Ensure every classical text record has a valid source.
- [ ] Disallow placeholder text for corpus files marked complete.

Modern explanation data:

- [ ] Add modern plain-language explanations for each hexagram.
- [ ] Add modern plain-language explanations for each line.
- [ ] Add scenario templates for learning, work, travel, projects, relationships, health-sensitive, legal-sensitive, and finance-sensitive questions.
- [ ] Add risk-notice templates.

## v0.4.0 - LLM Quality And Safety

Goal: make LLM behavior structured, auditable, and predictable.

- [ ] Use Pydantic models for LLM preprocessing output.
- [ ] Use Pydantic models for LLM interpretation output.
- [ ] Fill safe defaults for missing optional fields.
- [ ] Reject or downgrade invalid fields.
- [ ] Prevent LLM output from rewriting classical source text.
- [ ] Pass only necessary fields for sensitive questions.
- [ ] Keep local and LLM "three don'ts" behavior consistent.
- [ ] Add a documented advanced review mode that summarizes more history only when explicitly requested.

Expected interpretation sections:

- [ ] Classical text.
- [ ] Hexagram structure.
- [ ] Changing-line focus.
- [ ] Changed-hexagram trend.
- [ ] Answer to the user's question.
- [ ] Actionable suggestions.
- [ ] Risk and uncertainty.
- [ ] Disclaimer.

## v0.5.0+ - Advanced Traditional Systems

Do not start these before v0.3.0 corpus integrity and v0.4.0 LLM schema are stable.

- [ ] Mei Hua Yi Shu rules.
- [ ] Liuyao Najia rules.
- [ ] Ganzhi calendar.
- [ ] Wuxing strength calculation.
- [ ] Six relatives and six spirits.
- [ ] Shi/Ying.
- [ ] Yongshen.
- [ ] Shen Sha.
- [ ] Day/month strength rules.
- [ ] Xunkong.
- [ ] Advanced scenario-specific interpretation templates.

## Visual Polish

- [ ] Use a unified visual system across all rendered cards.
- [ ] Replace text-only coin output with clearer visual coin marks.
- [ ] Make changing/stable and yin/yang lines easier to scan.
- [ ] Improve original/changed hexagram comparison.
- [ ] Align notice, error, refusal, settings, history, and record-card styles.
- [ ] Improve long-text spacing and hierarchy.
- [ ] Add screenshot-based visual regression tests if the rendering setup becomes stable enough.

## Public Repository Standards

- [ ] Keep examples generic and reproducible.
- [ ] Keep secrets, databases, logs, caches, local bot config, and deployment-only paths out of Git.
- [ ] Avoid documenting operator-specific infrastructure in this repository.
- [ ] Keep package instructions usable for a fresh NoneBot project.
- [ ] Keep privacy and disclaimer text aligned with actual runtime behavior.
