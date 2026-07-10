# nonebot-plugin-yijing

[English](README.en.md)

基于《周易》的 NoneBot2 群聊起卦、查卦、解卦与图片化输出插件。

> 当前版本是可运行的 Alpha 工程：命令、ORM、权限、HTML 长图渲染、核心经传资料库与后续扩展资料层已经接通；历代注释和术数扩展仍在持续校勘补录。

## 介绍

`nonebot-plugin-yijing` 面向 OneBot V11 群聊场景，提供群内自助起卦、查询、历史记录与解读输出。插件将交互结果统一渲染为图片，便于在 QQ 群等聊天环境中展示。

插件支持本地规则解读，并可选接入 OpenAI 兼容 LLM，用于问题预处理、三不占判断、近期历史对照与综合解读。LLM 失败时会自动降级到本地逻辑，不阻塞核心起卦流程。

## 功能

- 使用 `nonebot-plugin-alconna` 解析命令。
- 使用 `nonebot-plugin-orm[sqlite]` + SQLite 存储历史、配置、限额与冷却。
- 使用 `nonebot-plugin-htmlrender` 将帮助、起卦、查卦、历史等输出渲染为图片。
- 使用 `nonebot-plugin-access-control` 与 `nonebot-plugin-access-control-api` 管理插件级和功能级权限。
- 支持三枚铜钱法、大衍筮法概率模拟、手动输入与随机一卦。
- 起卦记录包含时间信息，可用于冷却、日限额与短期相似问题判断。
- 资料库预留完整经传、关系、来源、起卦规则、解读规则与后续术数扩展字段。

## 安装

### 使用 nb-cli

```bash
nb plugin install nonebot-plugin-yijing
```

### 使用包管理器

```bash
pip install nonebot-plugin-yijing
```

开发目录安装：

```bash
pip install -e .
```

从 GitHub 指定提交安装，适合 Alpha 部署验证：

```bash
pip install "nonebot-plugin-yijing @ git+ssh://git@github.com/newcovid/nonebot-plugin-yijing.git@<commit-sha>"
```

### 在 NoneBot 项目中加载

```python
nonebot.load_plugin("nonebot_plugin_yijing")
```

或在 `pyproject.toml` 中配置：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_yijing"]
```

## 依赖

基础依赖会随插件安装。若需要在现有项目中显式补齐依赖，可执行：

```bash
pip install "nonebot-plugin-orm[sqlite]" nonebot-plugin-alconna nonebot-plugin-htmlrender
pip install nonebot-plugin-access-control nonebot-plugin-access-control-api
```

本插件当前保留 `nonebot-adapter-onebot` 作为硬依赖，因为发布目标主要是 OneBot V11 群聊环境。

## ORM 初始化

首次使用或升级后执行：

```bash
nb orm upgrade
nb orm check
```

不建议在常规配置中默认关闭 ORM 启动检查。只有在本地临时排查迁移问题时，才可短暂加入：

```env
ALEMBIC_STARTUP_CHECK=false
```

排查结束后应移除该配置，并重新执行 `nb orm upgrade` 与 `nb orm check`。

## 配置

配置写入 NoneBot 项目的 `.env` 或对应环境配置文件。完整示例见 [`.env.example`](.env.example)。

### ENV 示例

```env
# NoneBot / ORM
SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///./data/yijing.sqlite3

# 仅在本地排查 ORM 迁移问题时临时使用；常规部署不要关闭。
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

### 配置项说明

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `SQLALCHEMY_DATABASE_URL` | 由宿主项目决定 | `nonebot-plugin-orm` 数据库连接串；SQLite 部署可使用示例值。 |
| `ALEMBIC_STARTUP_CHECK` | `true` | ORM 启动迁移检查；只建议在本地临时排查迁移问题时设为 `false`。 |
| `ACCESS_CONTROL_AUTO_PATCH_ENABLED` | access-control 默认值 | 是否自动接入 access-control 权限补丁；推荐保持 `true`。 |
| `ACCESS_CONTROL_REPLY_ON_PERMISSION_DENIED_ENABLED` | access-control 默认值 | 权限拒绝时是否由 access-control 回复提示。 |
| `ACCESS_CONTROL_REPLY_ON_RATE_LIMITED_ENABLED` | access-control 默认值 | 被 access-control 限流时是否回复提示。 |
| `RENDER_BACKEND` | htmlrender 默认值 | htmlrender 后端；本插件推荐 `playwright`。 |
| `RENDER_STARTUP_MODE` | htmlrender 默认值 | htmlrender 启动时浏览器探测策略；示例使用 `probe`。 |
| `RENDER_STORAGE_PATH` | htmlrender 默认值 | Playwright 浏览器缓存/安装目录；Docker 预装浏览器时可设为 `/ms-playwright`。 |
| `RENDER_PLAYWRIGHT` | htmlrender 默认值 | Playwright JSON 配置，包括浏览器引擎、是否跳过安装和启动参数。 |
| `YIJING_DEFAULT_METHOD` | `coin` | 新群默认起卦方式；可选 `coin` 三枚铜钱法，或 `yarrow` 大衍筮法模拟。 |
| `YIJING_POSITIVE_FACE` | `正` | 手动铜钱输入中代表正面的文本。 |
| `YIJING_NEGATIVE_FACE` | `反` | 手动铜钱输入中代表反面的文本。 |
| `YIJING_POSITIVE_VALUE` | `3` | 正面计数值；默认与传统铜钱法的正面数值一致。 |
| `YIJING_NEGATIVE_VALUE` | `2` | 反面计数值；默认与传统铜钱法的反面数值一致。 |
| `YIJING_GROUP_DEFAULT_ENABLED` | `true` | 新群首次写入群配置时是否默认启用插件。 |
| `YIJING_COOLDOWN_SECONDS` | `60` | 新群默认群级起卦冷却秒数；`0` 表示不启用冷却。 |
| `YIJING_DAILY_LIMIT_PER_USER` | `10` | 新群默认单用户 24 小时起卦次数上限，最小值为 `1`。 |
| `YIJING_DUPLICATE_WINDOW_MINUTES` | `30` | 新群默认短期相似问题检测窗口，单位分钟。 |
| `YIJING_HISTORY_MINUTES_FOR_LLM` | `120` | 新群默认传给 LLM 预处理的近期历史窗口，单位分钟。 |
| `YIJING_MANUAL_SESSION_TIMEOUT_SECONDS` | `900` | 手动起卦会话超时时间，单位秒，最小值为 `60`。 |
| `YIJING_STORE_QUESTION` | `true` | 是否保存原始问题文本；设为 `false` 时仍保存卦象、哈希和结构化结果。 |
| `YIJING_USER_HASH_SALT` | `change-me` | 用户 ID 哈希盐；生产环境应改成私有随机字符串，修改后旧记录无法再按同一用户哈希匹配。 |
| `YIJING_RENDER_SCALE` | `2.0` | 长图截图倍率，范围 `1.0` 到 `4.0`；越高图片越清晰也越耗资源。 |
| `YIJING_RENDER_WIDTH` | `900` | 长图视口宽度，范围 `640` 到 `1600`，影响图片排版宽度。 |
| `YIJING_LLM_ENABLED` | `false` | 全局是否启用 OpenAI 兼容 LLM；还需要群配置开启 LLM 才会在群内使用。 |
| `YIJING_LLM_BASE_URL` | 空 | OpenAI 兼容接口 base URL，例如 `https://api.openai.com/v1`。 |
| `YIJING_LLM_API_KEY` | 空 | LLM API Key；不要提交到仓库。 |
| `YIJING_LLM_MODEL` | 空 | 调用的模型名，例如 `gpt-4o-mini` 或你的兼容服务模型名。 |
| `YIJING_LLM_TIMEOUT_SECONDS` | `30` | LLM 请求总超时秒数，范围 `3` 到 `120`。 |

群配置表会在群首次使用时从这些 `YIJING_*` 全局默认值初始化。其中启用状态、默认起卦方式、冷却、日限额、重复窗口、LLM 历史窗口和本群 LLM 开关，可通过 `易经设置` 在群内继续调整。

### htmlrender / Playwright

本插件以 `nonebot-plugin-htmlrender>=0.7.1` 为基线。推荐本地开发配置：

```env
RENDER_BACKEND=playwright
RENDER_STARTUP_MODE=probe
RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":false,"close_on_exit":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}
```

生产 Docker 环境如果在镜像构建阶段把 Playwright Chromium 安装到 `/ms-playwright`，推荐：

```env
RENDER_BACKEND=playwright
RENDER_STARTUP_MODE=probe
RENDER_STORAGE_PATH=/ms-playwright
RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":true,"close_on_exit":true,"cleanup_legacy_cache":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}
```

这种部署方式要求 Dockerfile 或镜像构建脚本确实把 Chromium 安装到了 `/ms-playwright`。如果没有预装浏览器，不要设置 `skip_browser_install=true`。

## 使用

### 命令

| 命令 | 说明 |
| --- | --- |
| `易经帮助` | 查看帮助长图 |
| `起卦 问题` | 使用本群默认方式起卦并解卦 |
| `起卦 问题 铜钱` | 精确指定铜钱法 |
| `起卦 问题 大衍` | 使用大衍筮法概率模拟 |
| `起卦 问题 手动` | 进入手动起卦引导 |
| `解卦 卦象` | 查询/解释指定卦象 |
| `易经历史` | 查看自己的历史记录 |
| `易经记录 ID` | 查看指定记录 |
| `易经清理 ID` | 清理自己在当前群的指定起卦记录 |
| `易经清理 全部` | 清理自己在当前群的全部起卦历史，不重置日限额和群冷却 |
| `随机一卦` | 随机生成一个观察主题，保存历史但不占日限额、不触发冷却 |
| `易经设置` | 查看或修改本群配置 |

### 手动铜钱输入

进入 `起卦 问题 手动` 后选择 `铜钱`，再按提示自下而上逐爻输入。每爻输入 3 个正/反：

```text
正反正
```

### 手动大衍输入

进入 `起卦 问题 手动` 后选择 `大衍`。插件会按大衍筮法引导六爻十八变；每一变请将当前蓍草分成左右两堆，并输入左右数量：

```text
24 25
```

插件会校验挂一、揲四、归奇后的策数，并自动计算 `6/7/8/9` 爻值。

## 权限控制

本插件通过 `nonebot-plugin-access-control-api` 注册以下服务：

```text
nonebot_plugin_yijing
nonebot_plugin_yijing.cast
nonebot_plugin_yijing.query
nonebot_plugin_yijing.history
nonebot_plugin_yijing.settings
nonebot_plugin_yijing.random
nonebot_plugin_yijing.manual
```

示例：禁用某群的起卦功能，但保留查卦：

```text
/ac permission deny --sbj qq:g123456789 --srv nonebot_plugin_yijing.cast
/ac permission allow --sbj qq:g123456789 --srv nonebot_plugin_yijing.query
```

## 资料库

资料库位于 `nonebot_plugin_yijing/data/`，结构说明见 [`nonebot_plugin_yijing/data/README.md`](nonebot_plugin_yijing/data/README.md)。

当前核心经传层已填充：八卦、六十四卦、六爻骨架、卦辞、384 条爻辞、彖传、象传、乾坤文言、系辞上下、说卦、序卦、杂卦、卦关系、来源、起卦规则、解读规则。

后续扩展层已建立空表和 schema：历代注释、梅花易数、六爻纳甲、干支历法、五行旺衰、六亲六神、现代白话解释、场景化解读模板。扩展正文必须来自脚本抓取或人工校勘来源，禁止 AI 生成资料库正文。

## LLM 预处理、解读与隐私

启用 LLM 后，`起卦 问题` 会在真正起卦前执行预处理：

- 判断问题是否明确。
- 判断是否违反“不诚不占、不义不占、不疑不占”。
- 对照参数化历史记录，识别短期重复或相似问题。
- 标注医疗、法律、投资、人身安全等敏感领域。

LLM 接口为 OpenAI 兼容 `/chat/completions`，失败会自动降级到本地规则，不阻塞起卦核心流程。

隐私注意事项：

- `YIJING_LLM_ENABLED=false` 时，LLM 不会被调用。
- 开启 LLM 后，用户问题、卦象资料、预处理字段，以及按配置选取的近期历史记录，可能会发送给你配置的第三方模型服务商。
- `YIJING_STORE_QUESTION=true` 会在数据库中保存原始问题文本，便于历史回看和相似问题判断。
- 若希望降低存储敏感内容的风险，可设置 `YIJING_STORE_QUESTION=false`。此时历史记录会保留卦象和结构化结果，但原始问题文本不会保存。
- 本插件只提供本地降级逻辑，不代理或改变第三方模型服务商的数据处理规则。请按实际接入的模型服务商补充群公告或隐私说明。

## 开发

```bash
python -m pip install -e ".[dev]"
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

## 更多文档

- [`docs/deployment-smoke-test.md`](docs/deployment-smoke-test.md)：包安装、ORM、渲染与聊天命令验收清单。
- [`docs/data-collation.md`](docs/data-collation.md)：经传资料库补录、来源、状态与校勘流程。
- [`docs/release.md`](docs/release.md)：构建、验包、发布、部署验证与 PyPI 发布流程。

## 许可证

本项目使用 MIT License。详见 [`LICENSE`](LICENSE)。

## 免责声明

本插件用于传统文化学习、文本解释与群聊娱乐，不提供确定性预测，不构成医疗、法律、投资、安全或其他专业建议。
