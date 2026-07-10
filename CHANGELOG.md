# Changelog

## Unreleased

## 0.2.0 - 2026-07-10

### Added

- Support adapter-independent image replies through Alconna `UniMessage` export.
- Group every `易经设置` subcommand under the parent command in the rendered help image.

### Changed

- Declare support for all NoneBot adapters and remove the OneBot V11 runtime dependency.
- Recommend PyPI and the pending NoneBot Plugin Store listing as the public installation channels.
- Simplify public configuration guidance to settings owned by this plugin and its required
  database URL.
- Migrate package licensing metadata to the PEP 639 SPDX format and require a compatible
  setuptools build backend.
- Add a field-specific comment before every setting in the README ENV samples and
  `.env.example` so copied configurations remain self-explanatory.

### Removed

- Remove the redundant direct Playwright dependency and operator-specific rendering examples.
- Remove local-directory and GitHub-commit installation recommendations.

## 0.1.4 - 2026-07-10

### Added

- Add `易经清理 ID` and `易经清理 全部` for user-scoped history cleanup in the
  current group without resetting quota or cooldown state.

### Changed

- Render yin and yang lines with fixed-width geometric segments so their left and right
  edges align consistently.
- Keep the six-line result heading concise and remove the redundant orientation note.
- Honor the configured render width and scale, and document the complete runtime ENV
  reference in the Chinese and English guides.

### Fixed

- Use canonical line labels such as `九五` and `六五` throughout runtime payloads and
  structured line-slot data.
- Avoid repeating line labels in the classical six-line section when the source text
  already includes its own label.
- Confirm and regression-test that similar-question detection uses the configured
  minute-based window, with a 30-minute default.

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
- Raise dependency baselines for `nonebot2` and `nonebot-plugin-htmlrender`.
- Switch the project license to MIT for easier public plugin reuse.
- Make package-data patterns recursive for future nested data, templates, CSS, and migrations.
- Add `nonebot2[fastapi]` to development extras so tests can initialize NoneBot's default FastAPI driver.

### Documentation

- Document ORM setup and runtime configuration.
- Add LLM privacy notes for third-party model data flow and `YIJING_STORE_QUESTION`.
- Add deployment validation coverage.

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
