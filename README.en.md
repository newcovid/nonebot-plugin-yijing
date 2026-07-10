# nonebot-plugin-yijing

[简体中文](README.md)

A NoneBot2 plugin for I Ching group-chat divination, lookup, interpretation, history, and image-rendered replies.

> The current release is a runnable Alpha project. Commands, ORM, permissions, HTML image rendering, data schemas, and seed data are wired up; the full classical corpus is still being collated and proofread.

## Introduction

`nonebot-plugin-yijing` targets OneBot V11 group-chat usage. It lets users cast hexagrams, query hexagram text, view history, and receive rendered image replies directly in chat.

The plugin works with local rule-based interpretation by default. An optional OpenAI-compatible LLM can be enabled for question preprocessing, "three don'ts" checks, recent-history comparison, and synthesized interpretation. If the LLM request fails, the plugin falls back to local logic and does not block the core casting flow.

## Features

- Command parsing with `nonebot-plugin-alconna`.
- History, settings, quota, and cooldown persistence with `nonebot-plugin-orm[sqlite]` and SQLite.
- Image output for help, casting, lookup, and history views through `nonebot-plugin-htmlrender`.
- Plugin-level and feature-level permission control through `nonebot-plugin-access-control` and `nonebot-plugin-access-control-api`.
- Three-coin casting, probabilistic yarrow-stalk simulation, manual input, and random hexagram generation.
- Timestamped casting records for cooldowns, daily limits, and short-term similar-question checks.
- Data model prepared for the classical corpus, relations, sources, casting rules, interpretation rules, and later traditional-method extensions.

## Installation

### With nb-cli

```bash
nb plugin install nonebot-plugin-yijing
```

### With pip

```bash
pip install nonebot-plugin-yijing
```

Editable development install:

```bash
pip install -e .
```

Install a specific GitHub commit for Alpha deployment validation:

```bash
pip install "nonebot-plugin-yijing @ git+ssh://git@github.com/newcovid/nonebot-plugin-yijing.git@<commit-sha>"
```

### Load in a NoneBot project

```python
nonebot.load_plugin("nonebot_plugin_yijing")
```

Or configure `pyproject.toml`:

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_yijing"]
```

## Dependencies

Runtime dependencies are installed with the plugin. To explicitly install the main integration plugins in an existing project:

```bash
pip install "nonebot-plugin-orm[sqlite]" nonebot-plugin-alconna nonebot-plugin-htmlrender
pip install nonebot-plugin-access-control nonebot-plugin-access-control-api
```

The plugin currently keeps `nonebot-adapter-onebot` as a required dependency because its primary release target is OneBot V11 group chat.

## ORM Setup

Run after first install or upgrade:

```bash
nb orm upgrade
nb orm check
```

Do not disable the ORM startup check in normal configuration. Only use the following temporarily while diagnosing local migration issues:

```env
ALEMBIC_STARTUP_CHECK=false
```

Remove it after troubleshooting, then run `nb orm upgrade` and `nb orm check` again.

## Configuration

Put configuration in the NoneBot project's `.env` file or the environment file used by
your deployment. See [`.env.example`](.env.example) for the complete sample.

### ENV sample

```env
# NoneBot / ORM
SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///./data/yijing.sqlite3

# Temporary local-only workaround when diagnosing ORM migration issues.
# Do not disable this in normal deployments.
# ALEMBIC_STARTUP_CHECK=false

# access-control
ACCESS_CONTROL_AUTO_PATCH_ENABLED=true
ACCESS_CONTROL_REPLY_ON_PERMISSION_DENIED_ENABLED=true
ACCESS_CONTROL_REPLY_ON_RATE_LIMITED_ENABLED=true

# htmlrender / Playwright: local development baseline
RENDER_BACKEND=playwright
RENDER_STARTUP_MODE=probe
RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":false,"close_on_exit":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}

# Yijing global defaults; group settings are initialized from these values and can be changed by command.
YIJING_DEFAULT_METHOD=coin
YIJING_POSITIVE_FACE=正
YIJING_NEGATIVE_FACE=反
YIJING_POSITIVE_VALUE=3
YIJING_NEGATIVE_VALUE=2
YIJING_GROUP_DEFAULT_ENABLED=true
YIJING_COOLDOWN_SECONDS=60
YIJING_DAILY_LIMIT_PER_USER=10
YIJING_DUPLICATE_WINDOW_MINUTES=30
YIJING_HISTORY_MINUTES_FOR_LLM=120
YIJING_MANUAL_SESSION_TIMEOUT_SECONDS=900
YIJING_STORE_QUESTION=true
YIJING_USER_HASH_SALT=change-me
YIJING_RENDER_SCALE=2.0
YIJING_RENDER_WIDTH=900

YIJING_LLM_ENABLED=false
# YIJING_LLM_BASE_URL=https://api.openai.com/v1
# YIJING_LLM_API_KEY=sk-xxx
# YIJING_LLM_MODEL=gpt-4o-mini
# YIJING_LLM_TIMEOUT_SECONDS=30
```

### Configuration Reference

| Key | Default | Description |
| --- | --- | --- |
| `SQLALCHEMY_DATABASE_URL` | Set by the host project | Database URL for `nonebot-plugin-orm`; the sample value is suitable for SQLite deployments. |
| `ALEMBIC_STARTUP_CHECK` | `true` | ORM startup migration check; set to `false` only temporarily while diagnosing local migration issues. |
| `ACCESS_CONTROL_AUTO_PATCH_ENABLED` | access-control default | Whether access-control automatically patches matchers; keeping `true` is recommended. |
| `ACCESS_CONTROL_REPLY_ON_PERMISSION_DENIED_ENABLED` | access-control default | Whether access-control replies when permission is denied. |
| `ACCESS_CONTROL_REPLY_ON_RATE_LIMITED_ENABLED` | access-control default | Whether access-control replies when a request is rate-limited. |
| `RENDER_BACKEND` | htmlrender default | htmlrender backend; this plugin recommends `playwright`. |
| `RENDER_STARTUP_MODE` | htmlrender default | Browser startup probing mode; the sample uses `probe`. |
| `RENDER_STORAGE_PATH` | htmlrender default | Playwright browser storage/install path; Docker images with preinstalled browsers can use `/ms-playwright`. |
| `RENDER_PLAYWRIGHT` | htmlrender default | JSON configuration for Playwright, including engine, install behavior, and launch arguments. |
| `YIJING_DEFAULT_METHOD` | `coin` | Default casting method for new groups: `coin` for three-coin casting or `yarrow` for simulated yarrow-stalk casting. |
| `YIJING_POSITIVE_FACE` | `正` | Text used for the positive face in manual coin input. |
| `YIJING_NEGATIVE_FACE` | `反` | Text used for the negative face in manual coin input. |
| `YIJING_POSITIVE_VALUE` | `3` | Numeric value assigned to the positive face. |
| `YIJING_NEGATIVE_VALUE` | `2` | Numeric value assigned to the negative face. |
| `YIJING_GROUP_DEFAULT_ENABLED` | `true` | Whether newly initialized group settings enable the plugin by default. |
| `YIJING_COOLDOWN_SECONDS` | `60` | Default group-level casting cooldown in seconds for new groups; `0` disables cooldown. |
| `YIJING_DAILY_LIMIT_PER_USER` | `10` | Default 24-hour casting limit per user in each group; minimum is `1`. |
| `YIJING_DUPLICATE_WINDOW_MINUTES` | `30` | Default short-term similar-question detection window for new groups, in minutes. |
| `YIJING_HISTORY_MINUTES_FOR_LLM` | `120` | Default recent-history window sent to LLM preprocessing for new groups, in minutes. |
| `YIJING_MANUAL_SESSION_TIMEOUT_SECONDS` | `900` | Manual casting session timeout in seconds; minimum is `60`. |
| `YIJING_STORE_QUESTION` | `true` | Whether to store original question text; when `false`, hexagram data, hashes, and structured results are still stored. |
| `YIJING_USER_HASH_SALT` | `change-me` | Salt for hashing user IDs; use a private random value in production. Changing it prevents old records from matching the same user hash. |
| `YIJING_RENDER_SCALE` | `2.0` | Screenshot scale for rendered images, from `1.0` to `4.0`; higher values are sharper and cost more resources. |
| `YIJING_RENDER_WIDTH` | `900` | Rendered image viewport width, from `640` to `1600`; affects layout width. |
| `YIJING_LLM_ENABLED` | `false` | Global OpenAI-compatible LLM switch; group-level LLM settings must also be enabled before a group uses LLM. |
| `YIJING_LLM_BASE_URL` | Empty | OpenAI-compatible base URL, for example `https://api.openai.com/v1`. |
| `YIJING_LLM_API_KEY` | Empty | LLM API key; do not commit it to the repository. |
| `YIJING_LLM_MODEL` | Empty | Model name, such as `gpt-4o-mini` or the name used by your compatible provider. |
| `YIJING_LLM_TIMEOUT_SECONDS` | `30` | Total LLM request timeout in seconds, from `3` to `120`. |

Group settings are initialized from these global `YIJING_*` defaults on first use. Enabled
state, default casting method, cooldown, daily limit, duplicate window, LLM history window,
and group-level LLM switch can later be changed with `易经设置`.

### htmlrender / Playwright

This plugin uses `nonebot-plugin-htmlrender>=0.7.1` as its baseline. Recommended local development configuration:

```env
RENDER_BACKEND=playwright
RENDER_STARTUP_MODE=probe
RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":false,"close_on_exit":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}
```

For production Docker images that install Playwright Chromium into `/ms-playwright` during image build:

```env
RENDER_BACKEND=playwright
RENDER_STARTUP_MODE=probe
RENDER_STORAGE_PATH=/ms-playwright
RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":true,"close_on_exit":true,"cleanup_legacy_cache":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}
```

Only set `skip_browser_install=true` if the image really includes the browser at `/ms-playwright`.

## Usage

### Commands

| Command | Description |
| --- | --- |
| `易经帮助` | Show the help image |
| `起卦 问题` | Cast and interpret with the group's default method |
| `起卦 问题 铜钱` | Use the three-coin method explicitly |
| `起卦 问题 大衍` | Use probabilistic yarrow-stalk simulation |
| `起卦 问题 手动` | Start guided manual casting |
| `解卦 卦象` | Query or interpret a specified hexagram |
| `易经历史` | View your own history |
| `易经记录 ID` | View a specific record |
| `易经清理 ID` | Delete one of your own casting records in the current group |
| `易经清理 全部` | Delete all of your casting history in the current group without resetting quota or cooldown |
| `随机一卦` | Generate a random observation topic, save it, but do not consume quota or cooldown |
| `易经设置` | View or modify group settings |

### Manual coin input

After `起卦 问题 手动`, choose `铜钱`, then enter one line at a time from bottom to top. Each line has 3 faces:

```text
正反正
```

### Manual yarrow-stalk input

After `起卦 问题 手动`, choose `大衍`. The plugin guides all 18 changes of the yarrow-stalk method. For each change, split the current stalks into left and right piles and enter both counts:

```text
24 25
```

The plugin validates the held stalk, counting by fours, remainders, and remaining stalk count, then computes the `6/7/8/9` line value.

## Permission Control

The plugin registers these services through `nonebot-plugin-access-control-api`:

```text
nonebot_plugin_yijing
nonebot_plugin_yijing.cast
nonebot_plugin_yijing.query
nonebot_plugin_yijing.history
nonebot_plugin_yijing.settings
nonebot_plugin_yijing.random
nonebot_plugin_yijing.manual
```

Example: disable casting in one group while keeping lookup enabled:

```text
/ac permission deny --sbj qq:g123456789 --srv nonebot_plugin_yijing.cast
/ac permission allow --sbj qq:g123456789 --srv nonebot_plugin_yijing.query
```

## Data Corpus

The data corpus lives in `nonebot_plugin_yijing/data/`. See [`nonebot_plugin_yijing/data/README.en.md`](nonebot_plugin_yijing/data/README.en.md) for its structure.

The core classical layer is filled: trigrams, 64 hexagrams, 384 line slots, hexagram statements, 384 line statements, Tuan, Xiang, canonical Qian/Kun Wenyan, Xici, Shuogua, Xugua, Zagua, relations, sources, casting rules, and interpretation rules.

Future extension layers now have empty JSON files and schemas: historical commentary, Meihua rules, Najia rules, Ganzhi calendar data, wuxing strength, liuqin/liushen, modern explanations, and scenario templates. Extension text must come from scripted fetching or human collation, not AI generation.

## LLM Preprocessing, Interpretation, and Privacy

When LLM support is enabled, `起卦 问题` runs preprocessing before casting:

- Checks whether the question is clear.
- Checks whether it violates the "do not divine without sincerity, righteousness, or doubt" rules.
- Compares parameterized recent history to find short-term repeated or similar questions.
- Marks sensitive areas such as medical, legal, investment, and personal-safety topics.

The LLM endpoint is OpenAI-compatible `/chat/completions`. Failures fall back to local rules and do not block casting.

Privacy notes:

- When `YIJING_LLM_ENABLED=false`, no LLM request is sent.
- When LLM is enabled, the user question, hexagram data, preprocessing fields, and selected recent history may be sent to the configured third-party model provider.
- `YIJING_STORE_QUESTION=true` stores the original question text in the database for history review and similar-question checks.
- Set `YIJING_STORE_QUESTION=false` to reduce sensitive text storage. History keeps hexagram and structured result data, but not the original question text.
- The plugin only provides local fallback logic. It does not proxy or change the model provider's data-handling policy. Add group notices or privacy text according to the provider you use.

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

## More Documentation

- [`docs/deployment-smoke-test.md`](docs/deployment-smoke-test.md): package install, ORM, rendering, and chat-command acceptance checklist.
- [`docs/data-collation.md`](docs/data-collation.md): corpus collation, sources, status, and proofreading workflow.
- [`docs/release.md`](docs/release.md): build, package check, release, deployment validation, and PyPI publishing workflow.

## License

MIT License. See [`LICENSE`](LICENSE).

## Disclaimer

This plugin is for traditional-culture study, text interpretation, and group-chat entertainment. It does not provide deterministic prediction and is not medical, legal, investment, safety, or other professional advice.
