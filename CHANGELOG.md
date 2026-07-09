# Changelog

## 0.1.3 - 2026-07-09

### Added

- Add reserved corpus tables and schemas for dynasty commentaries, Meihua rules,
  Najia rules, Ganzhi calendar, Wuxing strength, Liuqin/Liushen, modern explanations,
  and scenario templates.
- Persist raw cast traces for automatic, manual, and random casting records.
- Add interactive manual casting flows for coin and full yarrow-stalk input.

### Changed

- Resolve default, explicit coin, explicit yarrow, manual, query, random, history,
  record, help, and settings command flows against the shared corpus and runtime settings.
- Treat changed hexagrams as dynamic results computed from moving lines instead of a
  static 64x64 relation table.
- Reorder rendered card payloads to show raw state, hexagrams, line movement, corpus
  excerpts, interpretation, risk notices, disclaimer, and source notes.

### Fixed

- Normalize Yi terminology so `乾之策` is preserved while unrelated `干` usage remains
  untouched.
- Scope record viewing to the owner in the same group unless the requester is an admin.

## 0.1.2 - 2026-07-09

### Fixed

- Remove a legacy Alembic migration that reused the `nonebot_plugin_yijing` branch label
  and prevented `nonebot-plugin-orm` startup checks from completing.

## 0.1.1 - 2026-07-08

### Changed

- Bump package version to `0.1.1`.
- Update project metadata, repository URLs, issue URL, and plugin homepage.
- Raise dependency baselines for `nonebot2`, `nonebot-plugin-htmlrender`, and Playwright.
- Keep `nonebot-adapter-onebot` as a hard dependency for the current OneBot V11 oriented alpha.
- Switch the project license to MIT for easier public plugin reuse.
- Make package-data patterns recursive for future nested data, templates, CSS, and migrations.
- Add `nonebot2[fastapi]` to development extras so tests can initialize NoneBot's default FastAPI driver.

### Documentation

- Document ORM setup without defaulting to `ALEMBIC_STARTUP_CHECK=false`.
- Document htmlrender 0.7.1 / Playwright local and Docker production baselines.
- Add LLM privacy notes for third-party model data flow and `YIJING_STORE_QUESTION`.
- Add deployment smoke-test checklist.

### CI / Tests

- Add ruff, compile, pytest, build, and twine-check steps to CI.
- Add PyPI publish workflow with a distribution check before upload.
- Add minimum regression tests for packaged data, hexagrams, six-line slots, casting parsers, resolving, ORM model names, and local LLM fallback schema.
- Add an initial ORM migration for yijing runtime tables and migration packaging checks.
- Make ruff blocking again after removing the known lint debt.

## 0.1.0 - 2026-07-08

### Added

- Initial runnable NoneBot2 plugin scaffold.
- Alconna command parsing.
- ORM + SQLite persistence for records, group config, quotas, and cooldowns.
- htmlrender image output.
- access-control service registration.
- Coin, yarrow, manual, and random casting flows.
- Seed structured Zhouyi data corpus.
