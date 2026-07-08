# nonebot-plugin-yijing

群内自助进行基于《周易》的起卦、查卦、解卦、历史记录与图片化输出的 NoneBot2 插件。

> 当前版本是可运行工程骨架 + 种子资料库。结构、数据表、命令、ORM、权限、HTML 长图渲染链路已经搭好；经传全文需要在后续版本继续校勘补录。

## 特性

- `nonebot-plugin-alconna` 命令解析。
- `nonebot-plugin-orm[sqlite]` + SQLite 存储历史、配置、限额、冷却。
- `nonebot-plugin-htmlrender` 渲染所有交互输出为图片。
- `nonebot-plugin-access-control` + `nonebot-plugin-access-control-api` 做插件级/功能级权限管理。
- 支持三枚铜钱法、大衍筮法概率模拟、手动输入、随机一卦。
- 所有铜钱/硬币均统一使用“正/反”，可通过环境变量调整正反字符和数值。
- 起卦记录包含时间信息，用于冷却、日限额、短期相似问题判断。
- 可选 OpenAI 兼容 LLM：用于问题预处理、三不占判断、短期历史对照、综合解读。
- 资料库结构预留完整经传与后续术数扩展字段。

## 安装

```bash
pip install nonebot-plugin-yijing
```

开发目录安装：

```bash
pip install -e .
```

从 GitHub 指定提交安装，适合 Alpha 服务器验证：

```bash
pip install "nonebot-plugin-yijing @ git+ssh://git@github.com/newcovid/nonebot-plugin-yijing.git@<commit-sha>"
```

在 NoneBot 项目中加载：

```python
nonebot.load_plugin("nonebot_plugin_yijing")
```

或在 `pyproject.toml` 中：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_yijing"]
```

## 依赖插件

```bash
pip install "nonebot-plugin-orm[sqlite]" nonebot-plugin-alconna nonebot-plugin-htmlrender
pip install nonebot-plugin-access-control nonebot-plugin-access-control-api
```

本插件当前保留 `nonebot-adapter-onebot` 作为硬依赖，因为当前发布目标主要是 OneBot V11 群聊环境。

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

## 基础配置

```env
SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///./data/yijing.sqlite3

ACCESS_CONTROL_AUTO_PATCH_ENABLED=true
ACCESS_CONTROL_REPLY_ON_PERMISSION_DENIED_ENABLED=true
ACCESS_CONTROL_REPLY_ON_RATE_LIMITED_ENABLED=true

YIJING_DEFAULT_METHOD=coin
YIJING_POSITIVE_FACE=正
YIJING_NEGATIVE_FACE=反
YIJING_POSITIVE_VALUE=3
YIJING_NEGATIVE_VALUE=2
YIJING_GROUP_DEFAULT_ENABLED=true
YIJING_COOLDOWN_SECONDS=60
YIJING_DAILY_LIMIT_PER_USER=10
YIJING_DUPLICATE_WINDOW_MINUTES=30
YIJING_STORE_QUESTION=true

YIJING_LLM_ENABLED=false
# YIJING_LLM_BASE_URL=https://api.openai.com/v1
# YIJING_LLM_API_KEY=sk-xxx
# YIJING_LLM_MODEL=gpt-4o-mini
```

## htmlrender / Playwright 配置

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

## 命令

| 命令 | 说明 |
|---|---|
| `易经帮助` | 查看帮助长图 |
| `起卦 问题` | 默认三枚铜钱法起卦并解卦 |
| `起卦 问题 铜钱` | 精确指定铜钱法 |
| `起卦 问题 大衍` | 使用大衍筮法概率模拟 |
| `起卦 问题 手动` | 进入手动起卦引导 |
| `解卦 卦象` | 查询/解释指定卦象 |
| `易经历史` | 查看自己的历史记录 |
| `易经记录 ID` | 查看指定记录 |
| `随机一卦` | 随机生成一个观察主题 |
| `易经设置` | 查看或修改本群配置 |

### 手动铜钱输入

铜钱法必须自下而上输入 6 组，每组 3 个正/反：

```text
正反正 反反正 正正反 正反反 反正正 反反反
```

### 手动大衍输入

大衍法可以自下而上输入 6 个爻值：

```text
7 8 9 6 7 8
```

其中：

- `6` 老阴，动爻，阴变阳。
- `7` 少阳，静爻。
- `8` 少阴，静爻。
- `9` 老阳，动爻，阳变阴。

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

## 资料库结构

`nonebot_plugin_yijing/data/` 已预留：

1. 八卦表：`trigrams.json`
2. 六十四卦表：`hexagrams.json`
3. 六爻表：`lines.json`
4. 卦辞表：`guaci.json`
5. 爻辞表：`yaoci.json`
6. 彖传表：`tuan.json`
7. 象传表：`xiang.json`
8. 文言传表：`wenyan.json`
9. 系辞上下表：`xici_shang.json`、`xici_xia.json`
10. 说卦表：`shuogua.json`
11. 序卦表：`xugua.json`
12. 杂卦表：`zagua.json`
13. 卦关系表：`relations.json`
14. 来源表：`sources.json`
15. 起卦规则表：`casting_rules.json`
16. 解读规则表：`interpret_rules.json`
17. 预留扩展表：`reserved_tables.json`

当前内置完整项：八卦、六十四卦、六爻骨架、卦辞、卦关系、起卦规则、解读规则。

当前种子经文：乾、坤、需的爻辞/象传较完整；其余卦的爻辞、彖传、文言、系辞等字段先以结构化占位保留，等待后续校勘补录。

## LLM 预处理、解读与隐私

启用 LLM 后，`起卦 问题` 会在真正起卦前执行预处理：

- 判断问题是否明确。
- 判断是否违反“不诚不占、不义不占、不疑不占”。
- 对照参数化历史记录，识别短期重复/相似问题。
- 标注医疗、法律、投资、人身安全等敏感领域。

LLM 接口为 OpenAI 兼容 `/chat/completions`，失败会自动降级到本地规则，不阻塞起卦核心流程。

隐私注意事项：

- `YIJING_LLM_ENABLED=false` 时，LLM 不会被调用。
- 开启 LLM 后，用户问题、卦象资料、预处理字段，以及按配置选取的近期历史记录，可能会发送给你配置的第三方模型服务商。
- `YIJING_STORE_QUESTION=true` 会在数据库中保存原始问题文本，便于历史回看和相似问题判断。
- 若希望降低存储敏感内容的风险，可设置 `YIJING_STORE_QUESTION=false`。此时历史记录会保留卦象和结构化结果，但原始问题文本不会保存。
- 本插件只提供本地降级逻辑，不代理或改变第三方模型服务商的数据处理规则。请按实际接入的模型服务商补充群公告或隐私说明。

## 开发质量检查

```bash
python -m pip install -e ".[dev]"
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

## 服务器冒烟测试

服务器升级、换镜像、换 htmlrender/Playwright 基线后，建议按照 `docs/server-smoke-test.md` 执行真实群聊冒烟测试。

## 更多文档

- `docs/server-smoke-test.md`：服务器升级、包安装、真实群聊命令验收清单。
- `docs/data-collation.md`：经传资料库补录、来源、状态与校勘流程。
- `docs/release.md`：构建、验包、发布、服务器验证与 PyPI 发布流程。

## 许可证

本项目使用 MIT License。详见 `LICENSE`。

## 免责声明

本插件用于传统文化学习、文本解释与群聊娱乐，不提供确定性预测，不构成医疗、法律、投资、安全或其他专业建议。
