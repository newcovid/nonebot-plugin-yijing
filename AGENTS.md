# Repository Guidelines

## Project Structure & Module Organization

This is a Python 3.10+ NoneBot2 plugin package. Main source lives in
`nonebot_plugin_yijing/`: command handlers are in `commands/`, domain logic in `core/`,
rendering helpers in `render/`, integrations and persistence helpers in `services/`,
ORM models in `models.py`, and configuration in `config.py`. Packaged data is under
`nonebot_plugin_yijing/data/`, with JSON schemas in `data/schemas/`. HTML templates used
for image rendering are in `nonebot_plugin_yijing/templates/`. Migrations are in
`nonebot_plugin_yijing/migrations/`. Tests live in `tests/`, and longer design or data
notes belong in `docs/` or `nonebot_plugin_yijing/data/README.md`.

## Build, Test, and Development Commands

- `python -m pip install -e ".[dev]"`: install the plugin in editable mode with test,
  lint, build, and publish tooling.
- `ruff check .`: run the configured linter.
- `python -m compileall nonebot_plugin_yijing`: verify package modules compile.
- `pytest -q`: run the test suite with `pytest-asyncio` in auto mode.
- `python -m build --sdist --wheel .`: build release distributions.
- `twine check dist/*`: validate built package metadata before publishing.

CI runs these checks on Python 3.10, 3.11, and 3.12.

## Coding Style & Naming Conventions

Use four-space indentation, type hints where practical, and `from __future__ import
annotations` in new Python modules. Keep lines at or below 100
characters; Ruff is configured with `line-length = 100` and `target-version = "py310"`.
Use `snake_case` for functions, variables, modules, and JSON data keys. Keep plugin-facing
service identifiers under the `nonebot_plugin_yijing` namespace.

## Testing Guidelines

Add focused tests under `tests/test_*.py`. Prefer deterministic tests for core casting,
schema validation, payload construction, migrations, and data loading. `tests/conftest.py`
initializes a minimal NoneBot driver with the test database URL and LLM disabled. Database
integration tests require the configured test service. Run `pytest -q` before submitting changes;
run Ruff and compile checks when touching shared code or packaging.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style subjects, for example `feat(data): add source
schema`, `test(data): cover corpus schema structure`, and `docs(data): codify corpus schema
boundaries`. Keep subjects imperative and scoped when useful. Pull requests should describe
the behavior or data changed, list the checks run, link related issues, and include rendered
output screenshots when HTML templates or image rendering change.

## Security & Configuration Tips

Use `.env.example` as the configuration reference. Do not commit real bot tokens, database
URLs, API keys, or private group IDs. Keep database backend selection outside runtime plugin
dependencies.
