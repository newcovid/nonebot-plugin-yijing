# nonebot-plugin-yijing

[简体中文](README.md)

A NoneBot2 plugin for I Ching group-chat divination, lookup, interpretation, history, and image-rendered replies.

## Introduction

`nonebot-plugin-yijing` supports multi-adapter NoneBot2 chat environments. It lets users cast hexagrams, query hexagram text, view history, and receive rendered image replies directly in chat.

The plugin works with local rule-based interpretation by default. An optional OpenAI-compatible LLM can be enabled for question preprocessing, "three don'ts" checks, recent-history comparison, and synthesized interpretation. If the LLM request fails, the plugin falls back to local logic and does not block the core casting flow.

## Features

- Command parsing with `nonebot-plugin-alconna`.
- History, settings, quota, and cooldown persistence with `nonebot-plugin-orm`; the host project chooses the database backend.
- Image output for help, casting, lookup, and history views through `nonebot-plugin-htmlrender`.
- Plugin-level and feature-level permission control through `nonebot-plugin-access-control` and `nonebot-plugin-access-control-api`.
- Three-coin casting, probabilistic yarrow-stalk simulation, manual input, and random hexagram generation.
- Timestamped casting records for cooldowns, daily limits, and short-term similar-question checks.
- Data model prepared for the classical corpus, relations, sources, casting rules, interpretation rules, and later traditional-method extensions.

## Preview

### Cast record with synthesized LLM interpretation

![Cast record with synthesized LLM interpretation](https://raw.githubusercontent.com/newcovid/nonebot-plugin-yijing/main/docs/images/feature-cast.png)

| Command help | History |
| --- | --- |
| ![Command help](https://raw.githubusercontent.com/newcovid/nonebot-plugin-yijing/main/docs/images/feature-help.png) | ![History](https://raw.githubusercontent.com/newcovid/nonebot-plugin-yijing/main/docs/images/feature-history.png) |
| Manual casting | Group settings |
| ![Manual casting](https://raw.githubusercontent.com/newcovid/nonebot-plugin-yijing/main/docs/images/feature-manual.png) | ![Group settings](https://raw.githubusercontent.com/newcovid/nonebot-plugin-yijing/main/docs/images/feature-settings.png) |

## Installation

### NoneBot Plugin Store

After the plugin is listed in the NoneBot Plugin Store, install it with nb-cli:

```bash
nb plugin install nonebot-plugin-yijing
```

### With pip

```bash
pip install nonebot-plugin-yijing
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

Runtime dependencies are installed automatically. The plugin does not require a specific adapter; install and configure the adapter for the platform used by the host NoneBot project.

The plugin depends only on the `nonebot-plugin-orm` core package and does not force a database
backend. The host project manages its database driver and connection configuration.

## ORM Setup

Run after first install or upgrade:

```bash
nb orm upgrade
nb orm check
```

## Configuration

Put configuration in the NoneBot project's `.env` file or its active environment file.
See [`.env.example`](.env.example) for the complete sample.

### ENV sample

```env
# Rendering backend used by nonebot-plugin-htmlrender.
RENDER_BACKEND=playwright

# access-control
# Automatically apply access-control permission and rate-limit rules to plugin matchers.
ACCESS_CONTROL_AUTO_PATCH_ENABLED=true
# Reply to the user when access-control denies permission.
ACCESS_CONTROL_REPLY_ON_PERMISSION_DENIED_ENABLED=true
# Reply to the user when access-control rate-limits a command.
ACCESS_CONTROL_REPLY_ON_RATE_LIMITED_ENABLED=true

# Yijing global defaults
# Default casting method for newly initialized groups: coin or yarrow.
YIJING_DEFAULT_METHOD=coin
# Text accepted as the positive coin face during manual casting.
YIJING_POSITIVE_FACE=正
# Text accepted as the negative coin face during manual casting.
YIJING_NEGATIVE_FACE=反
# Numeric value assigned to the positive coin face.
YIJING_POSITIVE_VALUE=3
# Numeric value assigned to the negative coin face.
YIJING_NEGATIVE_VALUE=2
# Enable the plugin by default when a group is initialized for the first time.
YIJING_GROUP_DEFAULT_ENABLED=true
# Group-wide cooldown after a cast, in seconds; set 0 to disable it.
YIJING_COOLDOWN_SECONDS=60
# Maximum casts per user in each group during a rolling 24-hour period.
YIJING_DAILY_LIMIT_PER_USER=10
# Similar-question detection window, in minutes.
YIJING_DUPLICATE_WINDOW_MINUTES=30
# Recent-history window sent to LLM preprocessing, in minutes.
YIJING_HISTORY_MINUTES_FOR_LLM=120
# Guided manual-casting session timeout, in seconds.
YIJING_MANUAL_SESSION_TIMEOUT_SECONDS=900
# Store original question text in history records when true.
YIJING_STORE_QUESTION=true
# Salt used to hash user IDs; replace this with a private random value in production.
YIJING_USER_HASH_SALT=change-me
# Device scale factor for rendered images; valid range is 1.0 to 4.0.
YIJING_RENDER_SCALE=2.0
# Viewport width for rendered long images; valid range is 640 to 1600 pixels.
YIJING_RENDER_WIDTH=900

# Enable the OpenAI-compatible LLM integration globally.
YIJING_LLM_ENABLED=false
# Base URL of the optional OpenAI-compatible API.
# YIJING_LLM_BASE_URL=https://api.openai.com/v1
# API key for the optional LLM provider; never commit a real key.
# YIJING_LLM_API_KEY=sk-xxx
# Model name exposed by the optional LLM provider.
# YIJING_LLM_MODEL=gpt-4o-mini
# Total timeout for one LLM request, in seconds; valid range is 3 to 120.
# YIJING_LLM_TIMEOUT_SECONDS=30
```

### Configuration Reference

| Key | Default | Description |
| --- | --- | --- |
| `RENDER_BACKEND` | htmlrender default | Image renderer backend; this plugin recommends and validates `playwright`. |
| `ACCESS_CONTROL_AUTO_PATCH_ENABLED` | access-control default | Whether access-control automatically patches matchers; keeping `true` is recommended. |
| `ACCESS_CONTROL_REPLY_ON_PERMISSION_DENIED_ENABLED` | access-control default | Whether access-control replies when permission is denied. |
| `ACCESS_CONTROL_REPLY_ON_RATE_LIMITED_ENABLED` | access-control default | Whether access-control replies when a request is rate-limited. |
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

## Usage

### Commands

| Command | Description |
| --- | --- |
| `易经帮助` | Show the help image |
| `起卦 问题` | Cast and interpret with the group's default method |
| `起卦 问题 铜钱` | Use the three-coin method explicitly |
| `起卦 问题 大衍` | Use probabilistic yarrow-stalk simulation |
| `起卦 问题 手动` | Start guided manual casting |
| `起卦 问题 [method] --force` | Bypass repeat reuse only; three-don'ts, quota, and cooldown still apply |
| `解卦 卦象` | Query or interpret a specified hexagram |
| `易经历史` | View your own history |
| `易经记录 ID` | View a specific record |
| `易经清理 ID` | Delete one of your own casting records in the current group |
| `易经清理 全部` | Delete all of your casting history in the current group without resetting quota or cooldown |
| `随机一卦` | Generate a random observation topic, save it, but do not consume quota or cooldown |
| `易经设置` | View or modify group settings |

`易经设置` subcommands:

| Subcommand | Description |
| --- | --- |
| `开启` / `关闭` | Enable or disable the plugin in the current group |
| `冷却 秒数` | Set the group casting cooldown; `0` disables it |
| `日限额 次数` | Set the per-user rolling 24-hour casting limit |
| `重复窗口 分钟` | Set the recent similar-question detection window |
| `历史窗口 分钟` | Set the recent-history window used by LLM preprocessing |
| `默认 铜钱/大衍` | Set the group's default casting method |
| `LLM 开启/关闭` | Enable or disable LLM interpretation for the group |

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

After an allowed question is cast, the plugin makes a second LLM request with the question
and the minimum required primary, changing-line, changed-hexagram, and classical context.
The result card identifies LLM interpretation, local interpretation, or safe fallback and
separates the direct answer, structure, changing-line focus, trend, actions, and risks.

The LLM endpoint is OpenAI-compatible `/chat/completions`. Failures fall back to local rules and do not block casting.

When a similar question is found in the short-term window, the previous full record card is
returned without an LLM request, a new record, or quota usage. Append `--force` only when a
fresh cast is genuinely required.

Privacy notes:

- When `YIJING_LLM_ENABLED=false`, no LLM request is sent.
- When LLM is enabled, the user question, hexagram data, preprocessing fields, and selected recent history may be sent to the configured third-party model provider.
- Normal history context contains question text only; sensitive questions send no history. Group, user, bot, and record identifiers are never sent to the LLM.
- The first `易经设置 LLM 开启` in a group enables LLM immediately and shows a one-time privacy notice.
- `YIJING_STORE_QUESTION=true` stores the original question text in the database for history review and similar-question checks.
- Set `YIJING_STORE_QUESTION=false` to reduce sensitive text storage. History keeps hexagram and structured result data, but not the original question text.
- The plugin only provides local fallback logic. It does not proxy or change the model provider's data-handling policy. Add group notices or privacy text according to the provider you use.

## Development

```bash
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

## More Documentation

- [`docs/data-collation.md`](docs/data-collation.md): corpus collation, sources, status, and proofreading workflow.
- [`docs/release.md`](docs/release.md): build, package check, release validation, and PyPI publishing workflow.

## License

MIT License. See [`LICENSE`](LICENSE).

## Disclaimer

This plugin is for traditional-culture study, text interpretation, and group-chat entertainment. It does not provide deterministic prediction and is not medical, legal, investment, safety, or other professional advice.
