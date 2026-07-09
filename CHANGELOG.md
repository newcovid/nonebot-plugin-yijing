# Changelog

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
