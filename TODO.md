# TODO / 开发路线图

> 最近一次路线图同步：2026-07-08（PR #6 合并后）  
> 当前状态：**Alpha / 基础设施已稳定且 CI 通过，测试护栏已补强**  
> 范围：`nonebot-plugin-yijing` 仓库、包可复现性、服务器验收、资料库、用户体验与解读质量。

本文档不再重复保留已经关闭的每一个基础设施勾选项，而是将已完成的基础设施工作汇总记录。详细历史可查看已合并的 PR 与 `CHANGELOG.md`。

---

## 0. 当前总体评估

`nonebot_plugin_yijing` 目前是一个**群内可用的 Alpha 版本，并且已经具备可复现的包工程基础设施**。

核心运行链路已经实现：

```text
群消息命令
→ nonebot-plugin-alconna 解析
→ access-control 服务检查
→ ORM 群配置 / 限额 / 冷却 / 历史记录
→ 本地 / LLM 预处理
→ 起卦
→ 本卦 / 变卦 / 动爻
→ 记录持久化
→ htmlrender 长图渲染
→ OneBot V11 图片回复
```

仓库基础设施基线已经在 CI 中通过：

```text
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

主要剩余缺口是：**包安装后的服务器验收、资料内容完整性、LLM 强约束、解读质量、手动起卦体验、重复问题复用策略和视觉打磨**。

---

## 1. 已完成的基础设施基线

已通过 v0.1.1 稳定化工作完成：

- [x] 包元数据更新到 `0.1.1`。
- [x] 占位仓库地址替换为 `newcovid/nonebot-plugin-yijing`。
- [x] 添加项目 Issues 地址。
- [x] 更新 `PluginMetadata.homepage`。
- [x] 提升 `nonebot2`、`nonebot-plugin-htmlrender` 和 Playwright 的依赖基线。
- [x] 当前 OneBot V11 Alpha 阶段有意保留 `nonebot-adapter-onebot` 为硬依赖。
- [x] 保留 `nonebot-plugin-access-control` 与 `nonebot-plugin-access-control-api` 为硬依赖。
- [x] 包数据匹配规则改为递归匹配，支持 data、templates、CSS 和 migrations 的后续分层。
- [x] 选择 MIT License，并补齐完整许可证文本。
- [x] README 与 `.env.example` 已补充 ORM、htmlrender 0.7.1、Playwright、Docker `/ms-playwright`、LLM 隐私说明。
- [x] 推荐默认配置中不再关闭 `ALEMBIC_STARTUP_CHECK`。
- [x] 为当前运行时数据表添加初始 ORM migration。
- [x] 添加 migration 打包与元数据测试。
- [x] CI 在 Python 3.10、3.11、3.12 上执行阻断式 ruff、compile、pytest、build、twine check。
- [x] PyPI 发布 workflow 在上传前执行 `twine check`。
- [x] 添加 `CHANGELOG.md`。
- [x] 添加 `docs/server-smoke-test.md`。
- [x] 添加 `docs/data-collation.md`。
- [x] 添加 `docs/release.md`。

后续已合并 PR 继续完成：

- [x] 群级重复问题窗口和 LLM 历史窗口已进入模型、迁移、命令和设置页。
- [x] 设置命令的非法数值输入已使用图片化错误提示处理，避免直接 traceback。
- [x] `tests/test_payload.py` 已覆盖记录卡片、历史记录和查卦 payload。
- [x] `tests/test_models.py` 已覆盖 `record_to_dict()` 的基础序列化。
- [x] `tests/test_llm_schema.py` 已覆盖 LLM 异常 fallback 和缺字段默认值保留。
- [x] `tests/test_data_integrity.py` 已覆盖卦关系目标存在性。

---

## 2. 当前进度矩阵

| 领域 | 当前状态 | 完成度 |
|---|---|---:|
| 仓库结构 | 元数据、包数据、文档、CI、发布 workflow 均已具备 | 95% |
| 服务器集成 | 已在现有 NoneBot Docker 栈中运行；仍需完成包安装验收 | 90% |
| ORM + SQLite | 模型、仓储层、迁移和测试均已具备 | 95% |
| 命令解析 | 已接入 `nonebot-plugin-alconna` | 90% |
| 图片输出 | 已接入 htmlrender；视觉设计仍较基础 | 85% |
| 权限管理 | 已集成 access-control 服务 | 80% |
| 硬币术语 | 正/反输入已可配置并受约束 | 95% |
| 起卦方式 | 铜钱、大衍、手动、随机基础流程已实现 | 75% |
| 短期重复问题 | 已有本地相似度与时间窗口机制；仍缺旧记录直接复用 | 65% |
| LLM 预处理 | 已有 OpenAI 兼容接口、本地 fallback 和基础测试；仍缺 Pydantic 强约束 | 55% |
| LLM 解读 | 已有 JSON prompt、本地 fallback 和基础测试；仍缺 Pydantic 强约束 | 55% |
| 数据结构 | 已有 16 类主要数据表、预留扩展和关系完整性测试 | 88% |
| 数据内容 | 大部分经典文本仍是种子内容或占位内容 | 30% |
| 设置界面 | 基础设置、重复窗口、历史窗口和数值校验已具备；仍缺 LLM 首次启用隐私提示 | 70% |
| 测试 | 已有核心基础设施、数据、起卦、模型、payload、LLM fallback 测试 | 70% |
| 发布质量 | CI 已通过；仍待服务器包安装验收与 PyPI 策略决定 | 70% |

---

## 3. 近期下一步

这些事项应在首次公开 PyPI 发布前完成。

### P0 — 服务器 / 包安装验收

- [ ] 在测试服务器上改用 GitHub commit 或 wheel 安装，而不是本地 `plugin_dirs`。
- [ ] 在干净测试 SQLite 数据库上运行 `nb orm upgrade`。
- [ ] 运行 `nb orm check`，确认没有 schema drift。
- [ ] 按 `docs/server-smoke-test.md` 执行真实群聊验收清单。
- [ ] 确认共享 htmlrender 栈的其他插件仍然正常。
- [ ] 按 `docs/release.md` 流程手动检查一次 wheel 内容。
- [ ] 决定发布通道：先 TestPyPI，还是直接发布 PyPI Alpha。

### P1 — 剩余最小测试

- [x] `tests/test_payload.py`
  - [x] 记录卡片 payload 包含模板需要的所有部分。
  - [x] 历史记录 payload 支持空记录和非空记录。
  - [x] 查卦 payload 支持找到和未找到两种情况。

- [ ] 扩展 `tests/test_models.py`
  - [x] `record_to_dict()` 可用于未过期记录。
  - [ ] 如可行，增加一个针对旧 `MissingGreenlet` 模式的回归用例。

- [x] 扩展 `tests/test_llm_schema.py`
  - [x] LLM 返回畸形 JSON 时可以安全 fallback。
  - [x] 缺失字段可被确定性地默认填充或拒绝。

### P1 — 文档与发布卫生

- [ ] 将 wheel 内容检查加入 CI，或新增专用 workflow artifact 检查。
- [ ] 如果后续频繁发布，添加 release checklist issue template。
- [ ] 首次包安装服务器冒烟测试后，记录服务器包安装结果。

---

## 4. v0.2.0 — 群内可用功能版本

目标：提升群内用户体验和管理员控制能力。

### 设置命令

当前已实现的基础项：

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
- [x] 对非法数值设置输入进行校验，避免 traceback。

剩余设置工作：

- [ ] 群级 LLM 首次启用时展示隐私提示。

### 手动起卦体验

- [ ] 用户可在手动会话中查看示例。
- [ ] 手动会话支持超时和取消。
- [ ] 非法手动输入可重试，而不是直接退出。
- [ ] 手动铜钱输入在最终渲染前展示逐爻解析结果。
- [ ] 手动大衍从“直接输入六个最终爻值”演进为引导式流程。

### 随机一卦

当前已实现的基础项：

- [x] 随机模式会跳过问题预处理。
- [x] 随机模式会选择起卦方式并渲染标准卡片。

剩余随机模式工作：

- [ ] 支持随机静卦查询。
- [ ] 支持随机观察主题。
- [ ] 决定随机记录是否保存，或允许配置为不保存。

### 重复问题处理

- [ ] 增加 `--force` 或等价的管理员覆盖机制。
- [ ] 检测到短期重复问题时，直接返回旧记录图片。
- [ ] 改进同人 / 同群 / 同主题问题的归一化。
- [ ] 使重复问题阈值可配置。

### 隐私与安全

当前已实现的基础项：

- [x] 群级 LLM 开关会在设置图片中显示。
- [x] 已文档化 `YIJING_STORE_QUESTION=false` 模式。
- [x] 敏感话题会追加专业建议提示。

剩余隐私 / 安全工作：

- [ ] 首次启用 LLM 时说明第三方模型数据流。
- [ ] 为 `YIJING_STORE_QUESTION=false` 模式添加测试。

---

## 5. v0.3.0 — 资料库增强

目标：让数据层真正成为有价值的结构化《周易》资料库。

### 数据 Schema 与校验

- [ ] 为每个数据文件定义 JSON Schema。
- [ ] 为每一条经典文本添加 `source_id`。
- [ ] 添加 `version` / `edition` / `collation_status` 元数据。
- [ ] 将数据校验测试加入 CI。
- [ ] 增加数据完整度报告命令或脚本。

### 经典文本优先补全

- [ ] 补全 384 条爻辞。
- [ ] 补全 64 卦彖传。
- [ ] 补全 64 卦象传。
- [ ] 补全乾坤文言传。
- [ ] 补全系辞上传。
- [ ] 补全系辞下传。
- [ ] 补全说卦传。
- [ ] 补全序卦传。
- [ ] 补全杂卦传。

### 数据完整性检查

当前已实现的基础项：

- [x] `hexagrams.json` 中不存在缺失的 1-64 卦序。
- [x] 每一卦都有六条结构化爻位记录。
- [x] 核心 JSON 文件存在，并且可从包资源加载。
- [x] 每一个卦关系目标都存在。

剩余数据完整性工作：

- [ ] 每一条文本都有有效来源。
- [ ] v0.3.0 之后禁止核心文本继续使用占位内容。

### 现代解释数据

- [ ] 为每一卦添加现代白话解释。
- [ ] 为每一爻添加现代白话解释。
- [ ] 添加场景模板：学习、实习、工作、出行、项目、关系、健康敏感、法律敏感、财务敏感。
- [ ] 添加风险提示模板。

---

## 6. v0.4.0 — LLM 与解读质量

目标：让 LLM 输出结构化、可审计、可控制。

### LLM Schema

- [ ] 使用 Pydantic 模型约束 LLM 预处理输出。
- [ ] 使用 Pydantic 模型约束 LLM 解读输出。
- [ ] 缺失字段可被安全默认填充。
- [ ] 非法字段会被拒绝或降级处理。
- [ ] LLM 不得改写经典原文。

### 历史记录参数化

- [x] 起卦预处理：读取最近 30-120 分钟历史。
- [x] 历史命令：不调用 LLM。
- [ ] 查卦命令：只传递查询文本和目标卦象。
- [ ] 高级复盘模式：仅在用户明确请求时汇总全部历史。
- [ ] 敏感问题：只发送必要最小字段。

### 三不占细化

- [ ] 不诚：明显玩梗、空问题、恶意刷屏。
- [ ] 不义：作弊、伤害他人、违法或规避政策意图。
- [ ] 不疑：没有具体疑问、纯确定性预测请求。
- [ ] 使本地规则与 LLM 规则保持一致。

### 解读输出标准

- [ ] 经典文本。
- [ ] 卦象结构。
- [ ] 动爻重点。
- [ ] 变卦趋势。
- [ ] 对用户问题的回答。
- [ ] 可执行建议。
- [ ] 风险与不确定性。
- [ ] 免责声明。

### 多规则策略预留

- [ ] 周易经传默认解读。
- [ ] 仅经典文本模式。
- [ ] 梅花易数预留模式。
- [ ] 六爻纳甲预留模式。
- [ ] 文王卦预留模式。

---

## 7. v0.5.0+ — 高阶术数系统

在 v0.3.0 数据完整性和 v0.4.0 解读 schema 稳定之前，不要开始这些内容。

- [ ] 梅花易数规则。
- [ ] 六爻纳甲规则。
- [ ] 干支历法。
- [ ] 五行旺衰。
- [ ] 六亲六神。
- [ ] 世应。
- [ ] 用神。
- [ ] 神煞。
- [ ] 日月建。
- [ ] 旬空。
- [ ] 高级场景化解读模板。

---

## 8. 视觉渲染路线图

当前渲染已经可用，但仍然较基础；公开 v1.0 前应达到产品级视觉质量。

- [ ] 所有卡片采用统一视觉设计。
- [ ] 用更好的铜钱图形替代纯文本 / 列表展示。
- [ ] 六爻可视化更清晰地区分动静、阴阳状态。
- [ ] 本卦 / 变卦对比更清楚。
- [ ] 通知 / 错误 / 拒绝 / 设置 / 历史图片风格一致。
- [ ] 长文本排版优化间距和章节层级。
- [ ] 如可行，添加基于截图的视觉回归测试。

---

## 9. 已知技术债

### 本仓库

- [ ] 避免在包代码中隐含服务器专属假设。
- [ ] 只有当公开插件易用性成为优先目标时，才考虑让 access-control 变成可选依赖。
- [ ] 在明确支持非 OneBot 适配器后，重新评估 `nonebot-adapter-onebot` 是否仍应为硬依赖。

### 外部 / 服务器栈技术债

- [ ] `nonebot_plugin_loladmin` 的表名可能需要重构。
  - 当前短前缀示例：
    - `loladmin_admin_auth`
    - `loladmin_banned_word`
    - `loladmin_group_settings`
    - `loladmin_ban_violation`
  - 未来推荐名称：
    - `nonebot_plugin_loladmin_admin_auth`
    - `nonebot_plugin_loladmin_banned_word`
    - `nonebot_plugin_loladmin_group_settings`
    - `nonebot_plugin_loladmin_ban_violation`
  - **不要直接在生产环境重命名。**
  - 必要流程：
    1. 备份 SQLite。
    2. 添加包含 rename 操作的 Alembic migration。
    3. 如有需要，重命名索引 / 约束。
    4. 校验迁移前后的数据数量。
    5. 执行服务器验收测试。
    6. 更新服务器项目文档。

---

## 10. 发布检查清单

### `v0.1.1` 前

- [x] P0 基础设施完成。
- [x] wheel 可在 CI 中成功构建。
- [x] CI 中 `twine check` 通过。
- [x] README 准确说明当前限制。
- [x] 明确披露资料不完整状态。
- [ ] 服务器包安装冒烟测试通过。
- [ ] 真实服务器手动验收清单通过。

### PyPI 发布前

- [ ] 决定发布通道：先 TestPyPI，还是直接发布 PyPI。
- [ ] 创建 GitHub release tag。
- [ ] 确认 PyPI 项目名 `nonebot-plugin-yijing` 可用。
- [ ] 确认 sdist / wheel 不包含秘密文件。
- [ ] 确认安装命令可用：
  ```bash
  pip install nonebot-plugin-yijing==0.1.1
  ```

### NoneBot 插件商店提交前

- [ ] 公开 README 已打磨。
- [x] 当前 Alpha 范围内的 `PluginMetadata` 已完整。
- [x] import / load 不需要必填秘密配置。
- [x] 可选 LLM 配置已文档化。
- [x] CI 通过。
- [ ] 包已发布到 PyPI。
- [x] 数据限制已明确披露。
- [x] 没有明显不安全或确定性预测宣称。
- [x] 隐私说明和免责声明已明确。

---

## 11. 建议下一步

按以下顺序推进：

1. 在测试服务器上从 GitHub commit 或本地 wheel 安装。
2. 在干净测试 SQLite 数据库上运行 `nb orm upgrade` 和 `nb orm check`。
3. 在真实群内执行 `docs/server-smoke-test.md`，并记录服务器包安装结果。
4. 决定 TestPyPI 还是直接发布 PyPI Alpha。
5. 实现“检测到短期重复问题时，直接返回旧记录图片”。
6. 添加群级 LLM 首次启用隐私提示。
7. 使用 Pydantic 模型约束 LLM 预处理和解读输出。
8. 改进手动起卦会话的示例、超时和非法输入重试。
9. 开始数据 JSON Schema、`source_id`、版本 / 底本 / 校勘状态设计。
10. 打 tag 并发布 `v0.1.1`。

在服务器包安装验收、数据完整性和 LLM schema 更稳定前，避免启动高阶术数系统开发。
