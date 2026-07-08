# TODO / Development Roadmap

> Last consolidated review: 2026-07-08  
> Current state: **Alpha / server-tested internal build**  
> Scope: `nonebot-plugin-yijing` repository, PyPI readiness, server deployment readiness, and longer-term feature/data roadmap.

This file consolidates two review tracks:

1. **Functional gap review**: original design goals vs current implementation.
2. **Repository infrastructure review**: packaging, CI, metadata, PyPI publishing, README, license, and deployment reproducibility.

The plugin already runs on the production NoneBot server and the main command pipeline has been proven in a real OneBot V11 group environment. The next objective is not to add advanced divination features immediately, but to turn the current server-tested code into a reproducible, testable, packageable, and maintainable project.

---

## 0. Current Overall Assessment

`nonebot_plugin_yijing` is currently a **group-usable Alpha / internal test build**.

The core runtime chain is already closed:

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

Major server-side issues already fixed and should be treated as part of the v0.1.1 stabilization baseline:

- Missing `nonebot_plugin_access_control` dependency.
- ORM migration/model index-name mismatch.
- htmlrender 0.7.0 / system Chromium runtime instability.
- htmlrender 0.7.1 `RENDER_STORAGE_PATH=/ms-playwright` browser path alignment.
- `render_template()` missing `pages.base_url`, causing Chromium directory-page JS warnings such as `start/addRow is not defined`.
- SQLAlchemy `MissingGreenlet` after async ORM commit/expiration.
- Practical Docker / localstore / SQLite / OneBot deployment chain.

The main remaining gaps are **data completeness, LLM robustness, interpretation quality, visual polish, tests, and release readiness**.

---

## 1. Progress Matrix

| Area | Original Goal | Current State | Completion |
|---|---|---:|---:|
| Repository structure | gold-price-style repo with `pyproject.toml`, README, workflows, plugin package | Basic structure exists | 80% |
| Server integration | Runs in existing NoneBot Docker stack | Real server loaded and tested | 90% |
| ORM + SQLite | `nonebot-plugin-orm` for records/config/quota/cooldown | Implemented; key runtime bugs fixed | 85% |
| Command parsing | Use `nonebot-plugin-alconna` | Implemented | 90% |
| Image output | All interactions rendered by htmlrender | Implemented; 0.7.1 baseline rebuilt | 85% |
| Permission management | Use a quality NoneBot permission plugin | access-control API integrated | 75% |
| Coin terminology | All coin inputs use 正/反 and are configurable | Implemented | 95% |
| Casting methods | Coin, yarrow, manual, random | Basic versions implemented | 75% |
| Short-term repeated questions | Time-aware similar-question handling | Local similarity + time window exists | 65% |
| LLM preprocessing | 三不占, similar questions, sensitive topics, parameterized history | Basic OpenAI-compatible interface; rough strategy | 45% |
| LLM interpretation | Question + hexagram + classic text analysis | Basic JSON prompt + local fallback | 50% |
| Data structure | 16 major data tables + reserved expansion | Structure mostly present | 80% |
| Data content | Long-term expandable, rich 周易 corpus | Architecture exists; most texts still seed/placeholders | 30% |
| Settings UI | Image-based group settings commands | Basic image/settings view; few commands | 55% |
| Tests | Sustainable regression tests | Minimal or insufficient coverage | 35% |
| Release quality | Public plugin quality | Metadata, license, tests, docs still need work | 45% |

---

## 2. Immediate Repository Infrastructure Tasks

These tasks should be completed before any PyPI release or server switch from local `plugin_dirs` to pip installation.

### P0-Infra: Must Fix Before v0.1.1

- [ ] **Update `pyproject.toml` metadata**
  - [ ] Change version from `0.1.0` to `0.1.1`.
  - [ ] Replace placeholder author email `example@example.com`.
  - [ ] Replace all `your-name/nonebot-plugin-yijing` URLs with `newcovid/nonebot-plugin-yijing`.
  - [ ] Add `Issues = "https://github.com/newcovid/nonebot-plugin-yijing/issues"`.
  - [ ] Ensure project name remains `nonebot-plugin-yijing`.
  - [ ] Ensure import package remains `nonebot_plugin_yijing`.

- [ ] **Update `PluginMetadata`**
  - [ ] Change `homepage` to `https://github.com/newcovid/nonebot-plugin-yijing`.
  - [ ] Keep `config=YijingConfig`.
  - [ ] Confirm `supported_adapters={"~onebot.v11"}` is intentional.

- [ ] **Fix dependency baselines**
  - [ ] Raise `nonebot2` to `>=2.5.0` because htmlrender 0.7.1 depends on it.
  - [ ] Raise `nonebot-plugin-htmlrender` to `>=0.7.1`.
  - [ ] Explicitly include `playwright>=1.60.0` or rely on htmlrender but document it. Prefer explicit while server baseline is sensitive.
  - [ ] Review whether `nonebot-adapter-onebot` should remain a hard dependency or move to docs-only.
  - [ ] Keep `nonebot-plugin-access-control` and `nonebot-plugin-access-control-api` as hard deps for now because the design requires fine-grained permission management.

- [ ] **Fix package data to support future nested data/templates**
  - Current one-level matching is fragile:
    ```toml
    "data/*.json"
    "templates/*.html"
    "migrations/*.py"
    ```
  - Replace with recursive patterns:
    ```toml
    [tool.setuptools.package-data]
    nonebot_plugin_yijing = [
        "data/**/*.json",
        "data/**/*.md",
        "templates/**/*.html",
        "templates/**/*.css",
        "migrations/**/*.py",
    ]
    ```

- [ ] **Verify ORM migration files exist and are packaged**
  - [ ] Run locally:
    ```powershell
    Get-ChildItem -Recurse nonebot_plugin_yijing\migrations
    ```
  - [ ] Confirm at least one migration file exists for:
    - `nonebot_plugin_yijing_cast_record`
    - `nonebot_plugin_yijing_group_config`
    - `nonebot_plugin_yijing_runtime_quota`
    - `nonebot_plugin_yijing_group_cooldown`
  - [ ] If migrations are missing, generate or write Alembic migrations before PyPI testing.
  - [ ] Ensure migration table names and model table names match exactly.
  - [ ] Do not hide migration problems by recommending `ALEMBIC_STARTUP_CHECK=false` as default.

- [ ] **Fix LICENSE consistency**
  - [ ] Choose license intentionally: `GPL-3.0-or-later`, `GPL-3.0-only`, MIT, etc.
  - [ ] Make `pyproject.toml` license match `LICENSE`.
  - [ ] Replace current short placeholder `LICENSE` with the full license text.
  - [ ] If staying GPL, use complete GPL text and update README if needed.

- [ ] **Update README and `.env.example` for htmlrender 0.7.1**
  - [ ] Add general local/development config:
    ```env
    RENDER_BACKEND=playwright
    RENDER_STARTUP_MODE=probe
    RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":false,"close_on_exit":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}
    ```
  - [ ] Add production Docker config used on the real server:
    ```env
    RENDER_BACKEND=playwright
    RENDER_STARTUP_MODE=probe
    RENDER_STORAGE_PATH=/ms-playwright
    RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":true,"close_on_exit":true,"cleanup_legacy_cache":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}
    ```
  - [ ] Document that the server Dockerfile installs Playwright Chromium into `/ms-playwright`.
  - [ ] Document that `RENDER_STORAGE_PATH=/ms-playwright` is required in that deployment style.

- [ ] **Do not default to disabling ORM checks**
  - [ ] Remove `ALEMBIC_STARTUP_CHECK=false` from the basic recommended config.
  - [ ] Keep it only under a section named “temporary development workaround”.
  - [ ] Recommend:
    ```bash
    nb orm upgrade
    nb orm check
    ```

- [ ] **Add LLM privacy notice to README**
  - [ ] State clearly: when LLM is enabled, user questions and selected recent history may be sent to the configured third-party model provider.
  - [ ] Document `YIJING_STORE_QUESTION` and privacy tradeoffs.
  - [ ] Document that LLM is optional and local fallback exists.

- [ ] **Improve CI**
  - [ ] Add `ruff check`.
  - [ ] Add `python -m build`.
  - [ ] Add `twine check dist/*`.
  - [ ] Keep `python -m compileall nonebot_plugin_yijing`.
  - [ ] Keep tests on Python 3.10, 3.11, 3.12 unless dependency matrix becomes too heavy.

- [ ] **Improve PyPI publish workflow**
  - [ ] Add `twine check dist/*` before publish.
  - [ ] Prefer PyPI Trusted Publishing later instead of long-lived `PYPI_API_TOKEN`.
  - [ ] If using token initially, make sure `PYPI_API_TOKEN` is a project-scoped token.

---

## 3. Current Runtime Stabilization Tasks

### P0-Runtime: Server-Tested v0.1.1 Baseline

- [x] `nonebot_plugin_access_control` dependency installed on server.
- [x] ORM index-name mismatch fixed.
- [x] htmlrender 0.7.1 baseline rebuilt.
- [x] `RENDER_STORAGE_PATH=/ms-playwright` aligned with Docker-installed Playwright browser.
- [x] `render_template()` `about:blank` base_url fix applied.
- [x] SQLAlchemy `MissingGreenlet` fixed by avoiding expired attribute lazy-load after async commits.
- [ ] Confirm the same fixes are present in the GitHub source, not only server hotfix files.
- [ ] Add a server-maintenance section in README or `docs/server-smoke-test.md`.
- [ ] Record the real server deployment baseline:
  - [ ] `nonebot-plugin-htmlrender==0.7.1`
  - [ ] `playwright==1.60.0`
  - [ ] Playwright Chromium installed to `/ms-playwright`
  - [ ] `RENDER_STORAGE_PATH=/ms-playwright`

### Manual Server Acceptance Checklist

Run these in a real group after every server upgrade:

- [ ] `易经帮助` returns image without htmlrender page errors.
- [ ] `易经设置` returns image.
- [ ] `随机一卦` returns image.
- [ ] `起卦 此行去山西实习一程怎么样`
- [ ] `起卦 此行去山西实习一程怎么样 铜钱`
- [ ] `起卦 此行去山西实习一程怎么样 大衍`
- [ ] `起卦 此行去山西实习一程怎么样 手动`
- [ ] `解卦 需`
- [ ] `易经历史`
- [ ] `易经记录 <ID>`
- [ ] `运行状态` still works, proving shared htmlrender stack did not break picstatus-ng.
- [ ] `tps` still works, proving shared htmlrender stack did not break terralink.

Acceptance standard:

```text
All commands return an image or an expected notice image.
No traceback appears in nonebot logs.
No ORM autogenerate mismatch appears.
No MissingGreenlet appears.
No htmlrender runtime startup failure appears.
```

---

## 4. PyPI / Packaging Readiness

### P0-Package: Before First PyPI Release

- [ ] `python -m compileall nonebot_plugin_yijing`
- [ ] `python -m pip install --upgrade build twine`
- [ ] `python -m build --sdist --wheel .`
- [ ] `twine check dist/*`
- [ ] Verify wheel contents:
  - [ ] `nonebot_plugin_yijing/data/*.json`
  - [ ] `nonebot_plugin_yijing/templates/*.html`
  - [ ] `nonebot_plugin_yijing/migrations/*.py`
  - [ ] `nonebot_plugin_yijing/__init__.py`
  - [ ] No `__pycache__`
  - [ ] No `.env`
  - [ ] No server private paths

### Wheel Installation Smoke Test

Use a fresh environment:

```powershell
python -m venv .venv-test
.\.venv-test\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install dist\*.whl
python - <<'PY'
import nonebot_plugin_yijing
print(nonebot_plugin_yijing.__name__)
PY
deactivate
```

Notes:

- If import fails due to required NoneBot plugin context, add a lightweight test that uses `importlib.resources` to check packaged data instead of importing the full plugin directly.
- If full import requires NoneBot driver initialization, document a correct test harness.

### Server Testing Without Copying Local Plugin Directory

Preferred development sequence:

1. **Frequent iteration**: install from GitHub commit.
   ```txt
   nonebot-plugin-yijing @ git+ssh://git@github.com/newcovid/nonebot-plugin-yijing.git@<commit-sha>
   ```
2. **Stabilized alpha**: publish PyPI and install exact version.
   ```txt
   nonebot-plugin-yijing==0.1.1
   ```
3. Remove local copy from:
   ```text
   /srv/stack/nonebot/lolbot/plugins/nonebot_plugin_yijing
   ```
4. Add `nonebot_plugin_yijing` to the server `pyproject.toml` plugin list.
5. Rebuild:
   ```bash
   cd /srv/stack/nonebot
   docker compose build --no-cache nonebot
   docker compose up -d --force-recreate nonebot
   docker logs -f --tail=200 nonebot
   ```

Do not keep both local plugin directory and pip-installed package active at the same time. It will make import precedence and debugging unreliable.

---

## 5. Tests To Add

### P1-Test: Minimum Regression Coverage

- [ ] `tests/test_data_load.py`
  - [ ] All required JSON files exist.
  - [ ] Data loader can load them from package resources.
  - [ ] No core JSON file is empty.

- [ ] `tests/test_hexagrams.py`
  - [ ] 64 hexagrams exist.
  - [ ] Sequence numbers 1-64 are complete and unique.
  - [ ] Names are unique where expected.
  - [ ] Lookup by `需` works.
  - [ ] Lookup by `5` works.

- [ ] `tests/test_lines.py`
  - [ ] 384 line slots exist structurally.
  - [ ] Each hexagram has six lines.
  - [ ] Positions are valid: 1-6.
  - [ ] Placeholder text is allowed for Alpha but flagged in completeness report.

- [ ] `tests/test_casting.py`
  - [ ] Coin cast returns exactly six values.
  - [ ] Coin values are only 6, 7, 8, 9.
  - [ ] Yarrow cast returns exactly six values.
  - [ ] Yarrow values are only 6, 7, 8, 9.
  - [ ] Manual coin parser accepts 正/反 only.
  - [ ] Manual coin parser rejects malformed input.

- [ ] `tests/test_resolve.py`
  - [ ] Fixed line values resolve to expected primary hexagram.
  - [ ] Moving lines generate correct changed hexagram.
  - [ ] No moving line returns no changed hexagram or expected same/none behavior.

- [ ] `tests/test_payload.py`
  - [ ] Record card payload contains all sections required by templates.
  - [ ] History payload supports empty and non-empty records.
  - [ ] Notice payload is renderable.

- [ ] `tests/test_models.py`
  - [ ] Table names use `nonebot_plugin_yijing_` prefix.
  - [ ] Model index names match migrations.
  - [ ] `record_to_dict()` works on non-expired records.
  - [ ] Add a regression case for the previous `MissingGreenlet` pattern if feasible.

- [ ] `tests/test_llm_schema.py`
  - [ ] Local fallback preprocessing schema is stable.
  - [ ] LLM malformed JSON falls back safely.
  - [ ] Missing fields are filled or rejected deterministically.

### P1-CI Improvements

- [ ] CI runs `ruff check .`.
- [ ] CI runs `python -m build`.
- [ ] CI runs `twine check dist/*`.
- [ ] CI uploads built artifacts on workflow dispatch or release builds if useful.

---

## 6. Feature Roadmap

## v0.1.1 — Server-Stabilized Alpha

Goal: current feature set is reproducible, rebuildable, and testable.

- [ ] Bump version to `0.1.1`.
- [ ] Fix metadata and repository URLs.
- [ ] Fix license consistency.
- [ ] Raise dependency baselines.
- [ ] Confirm package-data includes all data/templates/migrations.
- [ ] Confirm migration files exist.
- [ ] Add htmlrender 0.7.1 config docs.
- [ ] Add LLM privacy note.
- [ ] Add basic tests.
- [ ] Add `CHANGELOG.md`.
- [ ] Run wheel build and install smoke test.
- [ ] Run server manual acceptance checklist.

## v0.2.0 — Group-Usable Feature Version

Goal: improve group UX and administrator controls.

### Settings Commands

- [ ] `易经设置`
- [ ] `易经设置 开启`
- [ ] `易经设置 关闭`
- [ ] `易经设置 冷却 60`
- [ ] `易经设置 日限额 10`
- [ ] `易经设置 默认 铜钱`
- [ ] `易经设置 默认 大衍`
- [ ] `易经设置 LLM 开启`
- [ ] `易经设置 LLM 关闭`
- [ ] `易经设置 重复窗口 30`
- [ ] `易经设置 历史窗口 120`

### Manual Casting UX

- [ ] User can view examples during manual session.
- [ ] Manual session timeout and cancellation.
- [ ] Invalid manual input retries without exiting.
- [ ] Manual coin input shows parsed line-by-line result before final render.
- [ ] Manual yarrow evolves from “enter six final values” to a guided process.

### Random Hexagram

- [ ] Support random static hexagram lookup.
- [ ] Support random observation theme.
- [ ] Support random casting method selection.
- [ ] Decide whether random records are saved or optionally not saved.
- [ ] Explicitly avoid LLM question preprocessing for random mode.

### Repeated Question Handling

- [ ] Add `--force` or equivalent administrator override.
- [ ] Return old record image when short-term duplicate is detected.
- [ ] Improve normalization for same-person/same-group/same-topic questions.
- [ ] Make duplicate threshold configurable.

### Privacy and Safety

- [ ] First LLM enablement message explains third-party model data flow.
- [ ] Group-level LLM switch is visible in settings image.
- [ ] `YIJING_STORE_QUESTION=false` mode is documented and tested.
- [ ] Sensitive topics add professional-advice notices.

## v0.3.0 — Data Corpus Enhancement

Goal: make the data layer genuinely valuable as a structured 周易 corpus.

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

- [ ] No missing sequence numbers 1-64.
- [ ] Every hexagram has six line records.
- [ ] Every relation target exists.
- [ ] Every text has a source.
- [ ] Core text placeholders are disallowed after v0.3.0.

### Modern Explanation Data

- [ ] Add modern plain-language explanation per hexagram.
- [ ] Add modern plain-language explanation per line.
- [ ] Add scene templates: study, internship, job, travel, project, relationship, health-sensitive, legal-sensitive, finance-sensitive.
- [ ] Add risk warning templates.

## v0.4.0 — LLM and Interpretation Quality

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

## v0.5.0+ — Advanced Divination Systems

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

## 7. Visual Rendering Roadmap

Current rendering is usable but basic. It should become product-grade before a public v1.0.

- [ ] Unified visual design for all cards.
- [ ] Better coin graphics instead of plain text/list representation.
- [ ] Clearer six-line visualization with moving/static and yin/yang state.
- [ ] Better primary/changed hexagram comparison.
- [ ] Consistent notice/error/rejection/settings/history image style.
- [ ] Long-text layout with better spacing and section hierarchy.
- [ ] Add screenshot-based visual regression tests if feasible.

---

## 8. Documentation Roadmap

- [ ] README: quick start.
- [ ] README: installation via PyPI.
- [ ] README: installation via GitHub commit for alpha testing.
- [ ] README: NoneBot plugin loading.
- [ ] README: ORM setup.
- [ ] README: htmlrender 0.7.1 setup.
- [ ] README: Docker production notes.
- [ ] README: command reference.
- [ ] README: data corpus status.
- [ ] README: LLM privacy notice.
- [ ] README: disclaimer.
- [ ] Add `CHANGELOG.md`.
- [ ] Add `docs/server-smoke-test.md`.
- [ ] Add `docs/data-collation.md`.
- [ ] Add `docs/release.md`.

---

## 9. Known Technical Debt

### This Repository

- [ ] Verify ORM migrations are present and match models.
- [ ] Avoid server-only assumptions in package code.
- [ ] Make access-control optional only if public plugin usability becomes a priority.
- [ ] Revisit whether `nonebot-adapter-onebot` should be a hard dependency.
- [ ] Ensure no placeholder author, URL, or license metadata remains.
- [ ] Ensure all data/templates/migrations are included in wheel.

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

- [ ] P0-Infra complete.
- [ ] P0-Runtime complete.
- [ ] Wheel builds successfully.
- [ ] `twine check` passes.
- [ ] Fresh environment import/install smoke passes.
- [ ] Real server test via GitHub commit or local wheel passes.
- [ ] README accurately reflects current limitations.
- [ ] Data incompleteness is clearly disclosed.

### Before PyPI Release

- [ ] Decide release channel: TestPyPI first or real PyPI.
- [ ] Create GitHub release tag.
- [ ] Confirm PyPI project name is available: `nonebot-plugin-yijing`.
- [ ] Confirm no secret files are included in sdist/wheel.
- [ ] Confirm LICENSE is valid and complete.
- [ ] Confirm package data is included.
- [ ] Confirm install command works:
  ```bash
  pip install nonebot-plugin-yijing==0.1.1
  ```

### Before NoneBot Plugin Store Submission

- [ ] Public README is polished.
- [ ] `PluginMetadata` is complete.
- [ ] No required secret config for import/load.
- [ ] Optional LLM config is documented.
- [ ] CI is green.
- [ ] Package is on PyPI.
- [ ] Data limitations are clearly disclosed.
- [ ] No obvious unsafe or deterministic-prediction claims.
- [ ] Privacy and disclaimer are explicit.

---

## 11. Recommended Next Steps

Do these in order:

1. Fix repository metadata and dependency baselines.
2. Verify and fix migrations.
3. Add htmlrender 0.7.1 docs to README and `.env.example`.
4. Fix LICENSE.
5. Improve CI and publish workflow.
6. Add minimum regression tests.
7. Build wheel and verify contents.
8. Install from wheel in a fresh environment.
9. Server-test via GitHub commit or wheel/PyPI package.
10. Tag and release v0.1.1.

Avoid starting advanced divination systems before the above is complete.
