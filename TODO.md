# TODO / Development Roadmap

> Last roadmap cleanup: 2026-07-08  
> Current state: **Alpha / CI-green infrastructure baseline**  
> Scope: `nonebot-plugin-yijing` repository, package reproducibility, server validation, data corpus, UX, and interpretation quality.

This roadmap now keeps completed infrastructure work summarized instead of repeating every closed checkbox. Detailed history is available in merged PRs and `CHANGELOG.md`.

---

## 0. Current Overall Assessment

`nonebot_plugin_yijing` is now a **group-usable Alpha with reproducible package infrastructure**.

The core runtime chain is implemented:

```text
Group message command
→ nonebot-plugin-alconna parsing
→ access-control service check
→ ORM group config / quota / cooldown / history
→ local / LLM preprocessing
→ casting
→ primary hexagram / changed hexagram / moving lines
→ record persistence
→ htmlrender long-image rendering
→ OneBot V11 image reply
```

The repository infrastructure baseline is now CI-green:

```text
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

The main remaining gaps are **server acceptance after package install, data completeness, LLM robustness, interpretation quality, settings UX, manual-casting UX, and visual polish**.

---

## 1. Completed Infrastructure Baseline

Completed through the merged v0.1.1 stabilization work:

- [x] Package metadata updated to `0.1.1`.
- [x] Placeholder repository URLs replaced with `newcovid/nonebot-plugin-yijing`.
- [x] Project Issues URL added.
- [x] `PluginMetadata.homepage` updated.
- [x] Dependency baselines raised for `nonebot2`, `nonebot-plugin-htmlrender`, and Playwright.
- [x] `nonebot-adapter-onebot` intentionally retained as a hard dependency for the current OneBot V11 alpha.
- [x] `nonebot-plugin-access-control` and `nonebot-plugin-access-control-api` retained as hard dependencies.
- [x] Package-data patterns made recursive for data, templates, CSS, and migrations.
- [x] MIT license selected and full license text added.
- [x] README and `.env.example` updated for ORM, htmlrender 0.7.1, Playwright, Docker `/ms-playwright`, and LLM privacy.
- [x] `ALEMBIC_STARTUP_CHECK=false` removed from recommended default config.
- [x] Initial ORM migration added for current runtime tables.
- [x] Migration packaging and metadata tests added.
- [x] CI runs blocking ruff, compile, pytest, build, and twine check on Python 3.10, 3.11, and 3.12.
- [x] PyPI publish workflow includes `twine check` before upload.
- [x] `CHANGELOG.md` added.
- [x] `docs/server-smoke-test.md` added.
- [x] `docs/data-collation.md` added.
- [x] `docs/release.md` added.

---

## 2. Current Progress Matrix

| Area | Current State | Completion |
|---|---|---:|
| Repository structure | Metadata, package data, docs, CI, release workflow present | 95% |
| Server integration | Runs in existing NoneBot Docker stack; package-install acceptance still needed | 90% |
| ORM + SQLite | Models, repository layer, migration, and tests present | 95% |
| Command parsing | `nonebot-plugin-alconna` implemented | 90% |
| Image output | htmlrender implemented; visual design still basic | 85% |
| Permission management | access-control service integrated | 80% |
| Coin terminology | 正/反 input configurable and enforced | 95% |
| Casting methods | Coin, yarrow, manual, random basic flows implemented | 75% |
| Short-term repeated questions | Local similarity + time window exists | 65% |
| LLM preprocessing | OpenAI-compatible interface and local fallback exist | 45% |
| LLM interpretation | JSON prompt and local fallback exist | 50% |
| Data structure | 16 major data tables + reserved expansion present | 85% |
| Data content | Most classical text still seed/placeholders | 30% |
| Settings UI | Basic image/settings view; missing several commands | 55% |
| Tests | Core infrastructure/data/casting/model tests present | 55% |
| Release quality | CI green; server package-install acceptance and PyPI decision pending | 70% |

---

## 3. Immediate Next Steps

Do these before the first public PyPI release.

### P0 — Server/package acceptance

- [ ] Install from GitHub commit or wheel on the test server instead of local `plugin_dirs`.
- [ ] Run `nb orm upgrade` against a clean test SQLite database.
- [ ] Run `nb orm check` and confirm no schema drift.
- [ ] Run `docs/server-smoke-test.md` real group checklist.
- [ ] Confirm shared htmlrender stack still works for other plugins.
- [ ] Verify wheel contents manually once with the process in `docs/release.md`.
- [ ] Decide release channel: TestPyPI first or direct PyPI alpha.

### P1 — Remaining minimum tests

- [ ] `tests/test_payload.py`
  - [ ] Record card payload contains all sections required by templates.
  - [ ] History payload supports empty and non-empty records.
  - [ ] Query payload handles found and not-found cases.

- [ ] Extend `tests/test_models.py`
  - [ ] `record_to_dict()` works on non-expired records.
  - [ ] Add a regression case for the previous `MissingGreenlet` pattern if feasible.

- [ ] Extend `tests/test_llm_schema.py`
  - [ ] LLM malformed JSON falls back safely.
  - [ ] Missing fields are defaulted or rejected deterministically.

### P1 — Documentation and release hygiene

- [ ] Add wheel-content inspection to CI or a dedicated workflow artifact check.
- [ ] Add a release checklist issue template if releases become frequent.
- [ ] Document server package-install results after the first package-based server smoke test.

---

## 4. v0.2.0 — Group-Usable Feature Version

Goal: improve group UX and administrator controls.

### Settings Commands

Current implemented basics:

- [x] `易经设置`
- [x] `易经设置 开启`
- [x] `易经设置 关闭`
- [x] `易经设置 冷却 60`
- [x] `易经设置 日限额 10`
- [x] `易经设置 默认 铜钱`
- [x] `易经设置 默认 大衍`
- [x] `易经设置 LLM 开启`
- [x] `易经设置 LLM 关闭`

Remaining settings work:

- [ ] `易经设置 重复窗口 30`
- [ ] `易经设置 历史窗口 120`
- [ ] Validate invalid numeric setting input without traceback.
- [ ] Show privacy warning when enabling group-level LLM.

### Manual Casting UX

- [ ] User can view examples during manual session.
- [ ] Manual session timeout and cancellation.
- [ ] Invalid manual input retries without exiting.
- [ ] Manual coin input shows parsed line-by-line result before final render.
- [ ] Manual yarrow evolves from “enter six final values” to a guided process.

### Random Hexagram

Current implemented basics:

- [x] Random mode avoids question preprocessing.
- [x] Random mode selects a casting method and renders the standard card.

Remaining random-mode work:

- [ ] Support random static hexagram lookup.
- [ ] Support random observation theme.
- [ ] Decide whether random records are saved or optionally not saved.

### Repeated Question Handling

- [ ] Add `--force` or equivalent administrator override.
- [ ] Return old record image when short-term duplicate is detected.
- [ ] Improve normalization for same-person/same-group/same-topic questions.
- [ ] Make duplicate threshold configurable.

### Privacy and Safety

Current implemented basics:

- [x] Group-level LLM switch is visible in settings image.
- [x] `YIJING_STORE_QUESTION=false` mode is documented.
- [x] Sensitive topics add professional-advice notices.

Remaining privacy/safety work:

- [ ] First LLM enablement message explains third-party model data flow.
- [ ] Add tests for `YIJING_STORE_QUESTION=false` mode.

---

## 5. v0.3.0 — Data Corpus Enhancement

Goal: make the data layer genuinely valuable as a structured Zhouyi corpus.

### Data Schema and Validation

- [ ] Define JSON schema for every data file.
- [ ] Add `source_id` to every classical text item.
- [ ] Add `version` / `edition` / `collation_status` metadata.
- [ ] Add data validation tests to CI.
- [ ] Add a data completeness report command or script.

### Priority Classical Text Completion

- [ ] Complete 384 爻辞.
- [ ] Complete 64 卦 彖传.
- [ ] Complete 64 卦 象传.
- [ ] Complete 乾坤 文言传.
- [ ] Complete 系辞上传.
- [ ] Complete 系辞下传.
- [ ] Complete 说卦传.
- [ ] Complete 序卦传.
- [ ] Complete 杂卦传.

### Data Integrity Checks

Current implemented basics:

- [x] No missing sequence numbers 1-64 in `hexagrams.json`.
- [x] Every hexagram has six structural line records.
- [x] Required core JSON files exist and load from package resources.

Remaining data integrity work:

- [ ] Every relation target exists.
- [ ] Every text has a valid source.
- [ ] Core text placeholders are disallowed after v0.3.0.

### Modern Explanation Data

- [ ] Add modern plain-language explanation per hexagram.
- [ ] Add modern plain-language explanation per line.
- [ ] Add scene templates: study, internship, job, travel, project, relationship, health-sensitive, legal-sensitive, finance-sensitive.
- [ ] Add risk warning templates.

---

## 6. v0.4.0 — LLM and Interpretation Quality

Goal: make LLM output structured, auditable, and controllable.

### LLM Schema

- [ ] Use Pydantic models for LLM preprocessing output.
- [ ] Use Pydantic models for LLM interpretation output.
- [ ] Missing fields are defaulted safely.
- [ ] Invalid fields are rejected or downgraded.
- [ ] LLM must never rewrite classical text.

### History Parameterization

- [ ] Casting preprocessing: recent 30-120 minutes.
- [ ] History command: no LLM call.
- [ ] Hexagram query: only query text and target hexagram.
- [ ] Advanced review mode: summarized full history if explicitly requested.
- [ ] Sensitive questions: send minimal necessary fields only.

### 三不占 Refinement

- [ ] 不诚: obvious trolling, empty questions, malicious spam.
- [ ] 不义: cheating, harming others, illegal or policy-evading intent.
- [ ] 不疑: no concrete uncertainty, pure deterministic prediction requests.
- [ ] Make local rules and LLM rules consistent.

### Interpretation Output Standard

- [ ] Classical text.
- [ ] Hexagram structure.
- [ ] Moving-line emphasis.
- [ ] Changed-hexagram trend.
- [ ] Answer to user question.
- [ ] Actionable suggestions.
- [ ] Risks and uncertainty.
- [ ] Disclaimer.

### Multi-Rule Strategy Reservation

- [ ] 周易经传 default interpretation.
- [ ] Classical-text-only mode.
- [ ] 梅花易数 reserved mode.
- [ ] 六爻纳甲 reserved mode.
- [ ] 文王卦 reserved mode.

---

## 7. v0.5.0+ — Advanced Divination Systems

Do not start these before v0.3.0 data integrity and v0.4.0 interpretation schema are stable.

- [ ] 梅花易数 rules.
- [ ] 六爻纳甲 rules.
- [ ] 干支历法.
- [ ] 五行旺衰.
- [ ] 六亲六神.
- [ ] 世应.
- [ ] 用神.
- [ ] 神煞.
- [ ] 日月建.
- [ ] 旬空.
- [ ] Advanced scene-specific reading templates.

---

## 8. Visual Rendering Roadmap

Current rendering is usable but basic. It should become product-grade before a public v1.0.

- [ ] Unified visual design for all cards.
- [ ] Better coin graphics instead of plain text/list representation.
- [ ] Clearer six-line visualization with moving/static and yin/yang state.
- [ ] Better primary/changed hexagram comparison.
- [ ] Consistent notice/error/rejection/settings/history image style.
- [ ] Long-text layout with better spacing and section hierarchy.
- [ ] Add screenshot-based visual regression tests if feasible.

---

## 9. Known Technical Debt

### This Repository

- [ ] Avoid server-only assumptions in package code.
- [ ] Make access-control optional only if public plugin usability becomes a priority.
- [ ] Revisit whether `nonebot-adapter-onebot` should remain a hard dependency after non-OneBot adapters are explicitly supported.

### External / Server Stack Debt

- [ ] `nonebot_plugin_loladmin` table names likely need refactor.
  - Current short-prefix examples:
    - `loladmin_admin_auth`
    - `loladmin_banned_word`
    - `loladmin_group_settings`
    - `loladmin_ban_violation`
  - Future recommended names:
    - `nonebot_plugin_loladmin_admin_auth`
    - `nonebot_plugin_loladmin_banned_word`
    - `nonebot_plugin_loladmin_group_settings`
    - `nonebot_plugin_loladmin_ban_violation`
  - Do **not** rename directly in production.
  - Required process:
    1. Backup SQLite.
    2. Add Alembic migration with rename operations.
    3. Rename indexes/constraints if needed.
    4. Verify data counts before/after.
    5. Run server acceptance tests.
    6. Update server project documentation.

---

## 10. Release Checklist

### Before `v0.1.1`

- [x] P0-Infra complete.
- [x] Wheel builds successfully in CI.
- [x] `twine check` passes in CI.
- [x] README accurately reflects current limitations.
- [x] Data incompleteness is clearly disclosed.
- [ ] Server package-install smoke passes.
- [ ] Real server manual acceptance checklist passes.

### Before PyPI Release

- [ ] Decide release channel: TestPyPI first or real PyPI.
- [ ] Create GitHub release tag.
- [ ] Confirm PyPI project name is available: `nonebot-plugin-yijing`.
- [ ] Confirm no secret files are included in sdist/wheel.
- [ ] Confirm install command works:
  ```bash
  pip install nonebot-plugin-yijing==0.1.1
  ```

### Before NoneBot Plugin Store Submission

- [ ] Public README is polished.
- [x] `PluginMetadata` is complete for current alpha scope.
- [x] No required secret config for import/load.
- [x] Optional LLM config is documented.
- [x] CI is green.
- [ ] Package is on PyPI.
- [x] Data limitations are clearly disclosed.
- [x] No obvious unsafe or deterministic-prediction claims.
- [x] Privacy and disclaimer are explicit.

---

## 11. Recommended Next Steps

Do these in order:

1. Install from GitHub commit or local wheel on the test server.
2. Run `nb orm upgrade` and `nb orm check` against a clean test SQLite database.
3. Execute `docs/server-smoke-test.md` in a real group.
4. Add payload tests and model serialization regression tests.
5. Add settings commands for duplicate/history windows.
6. Add data relation-target validation.
7. Decide TestPyPI vs PyPI direct alpha release.
8. Tag and release `v0.1.1`.

Avoid starting advanced divination systems before server package-install acceptance, data integrity, and LLM schema are more stable.
