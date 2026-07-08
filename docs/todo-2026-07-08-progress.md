# 2026-07-08 TODO 接手进展

本次从 `TODO.md` 中选择了一组低风险、可验证、适合在 Alpha 阶段优先补齐的事项，重点不是新增大型功能，而是把现有运行链路的测试护栏补齐。

## 本次完成范围

### 1. Payload 生成测试

对应 `TODO.md` 中 `tests/test_payload.py` 的剩余项：

- 记录卡片 payload 包含模板需要的核心字段。
- 历史记录 payload 支持空记录。
- 历史记录 payload 支持非空记录。
- 查卦 payload 支持找到卦象和未找到卦象两种情况。

新增文件：

```text
tests/test_payload.py
```

覆盖目标：

- `build_record_card_payload()`
- `build_history_payload()`
- `build_hexagram_query_payload()`

### 2. 模型序列化测试

对应 `TODO.md` 中 `record_to_dict()` 可用于未过期记录的测试项。

扩展文件：

```text
tests/test_models.py
```

覆盖目标：

- 手动构造已加载的 `CastRecord`。
- 校验 `record_to_dict()` 能稳定解析 JSON 字段。
- 校验时间字段格式化结果。
- 校验问题、卦序、动爻、预处理和解读字段均可读取。

### 3. LLM fallback 与缺字段默认值测试

对应 `TODO.md` 中 LLM schema 的两个剩余测试项：

- LLM 返回畸形 JSON 或解析异常时可以安全 fallback。
- LLM 返回缺失字段时，本地默认字段仍可确定性保留。

扩展文件：

```text
tests/test_llm_schema.py
```

覆盖目标：

- `preprocess_question()` 在 LLM 异常时回退到 `local_preprocess()`。
- `preprocess_question()` 在 LLM 缺字段时保留本地默认字段。
- `interpret_with_llm()` 在 LLM 异常时回退到 `build_local_interpretation()`。
- `interpret_with_llm()` 在 LLM 缺字段时保留本地默认解释字段。

### 4. 卦关系完整性测试

对应 `TODO.md` 中数据完整性检查的“每一个卦关系目标都存在”。

新增文件：

```text
tests/test_data_integrity.py
```

覆盖目标：

- `relations.json` 中每一条 `hexagram_seq` 必须存在于六十四卦表。
- `relations.json` 中每一条 `target_seq` 必须存在于六十四卦表。
- 关系类型限定为当前已使用的 `opposite`、`inverse`、`nuclear`。

## 验证命令

建议在本地或 CI 中执行：

```bash
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
```

如需在发布前继续验证包内容，再执行：

```bash
python -m build --sdist --wheel .
twine check dist/*
```

## 未纳入本次 PR 的事项

以下事项仍建议后续独立处理：

- 真实服务器包安装冒烟测试。
- 手动起卦的完整会话超时与引导式大衍流程。
- LLM 输出改为 Pydantic 模型强约束。
- 经典文本补录、来源字段和完整 JSON Schema。

这些事项会涉及运行环境、交互状态机或资料校勘，适合单独拆 PR，避免与本次测试护栏混在一起。
