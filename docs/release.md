# Release Guide

This document describes the release process for `nonebot-plugin-yijing`.

## 1. Release channels

Public installation channels:

1. PyPI for tagged releases.
2. NoneBot Plugin Store after the listing is accepted.

Local wheels and TestPyPI may still be used internally to validate release artifacts, but
they are not public installation channels.

## 2. Pre-release checks

Before tagging a release, confirm:

```bash
ruff check .
python -m compileall nonebot_plugin_yijing
pytest -q
python -m build --sdist --wheel .
twine check dist/*
```

Also confirm:

- `pyproject.toml` version matches the intended release.
- `CHANGELOG.md` has a release entry.
- `README.md` describes current limitations accurately.
- `LICENSE` and `pyproject.toml` license metadata match.
- No private `.env`, local database, logs, cache, or machine-specific path is included.
- `nonebot_plugin_yijing/data/`, `templates/`, and `migrations/` are included in the wheel.

## 3. Wheel content inspection

After building, inspect the wheel:

```bash
python -m build --sdist --wheel .
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile

wheel = next(Path('dist').glob('*.whl'))
with ZipFile(wheel) as zf:
    names = sorted(zf.namelist())

required_prefixes = [
    'nonebot_plugin_yijing/data/',
    'nonebot_plugin_yijing/templates/',
    'nonebot_plugin_yijing/migrations/',
]
for prefix in required_prefixes:
    assert any(name.startswith(prefix) for name in names), prefix

for forbidden in ['.env', '.sqlite', '.sqlite3', '.db', '__pycache__']:
    assert not any(forbidden in name for name in names), forbidden

print(f'OK: {wheel}')
PY
```

## 4. Fresh environment smoke test

Use a fresh environment instead of the development venv.

PowerShell example:

```powershell
python -m venv .venv-test
.\.venv-test\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install dist\*.whl
python - <<'PY'
import importlib.resources as resources

root = resources.files('nonebot_plugin_yijing')
assert (root / 'data' / 'hexagrams.json').is_file()
assert (root / 'templates' / 'card.html').is_file()
assert (root / 'migrations' / '20260708_01_initial_yijing_tables.py').is_file()
print('package resources OK')
PY
deactivate
```

Avoid using a full plugin import as the only smoke test because plugin import can require a properly initialized NoneBot driver and adapter context.

## 5. Tagging

Use a `v` prefix for release tags:

```bash
git tag v0.2.0
git push origin v0.2.0
```

The publish workflow is configured to run on tags matching `v*` and can also be dispatched manually.

## 6. PyPI publishing

The release workflow uses PyPI Trusted Publishing.

Requirements:

- PyPI must have a trusted publisher or pending publisher configured for:
  - project: `nonebot-plugin-yijing`
  - owner: `newcovid`
  - repository: `nonebot-plugin-yijing`
  - workflow: `publish.yml`
  - environment: empty, unless the workflow starts using a GitHub environment
- The workflow must keep `id-token: write`.
- `twine check dist/*` must pass before upload.
- The GitHub Actions publish job should not run from unreviewed branches.

Do not add a long-lived `PYPI_API_TOKEN` unless trusted publishing is unavailable.

## 7. Post-release checks

After publishing:

```bash
python -m venv .venv-release-test
. .venv-release-test/bin/activate
python -m pip install --upgrade pip
python -m pip install nonebot-plugin-yijing==0.2.0
python - <<'PY'
import importlib.resources as resources
root = resources.files('nonebot_plugin_yijing')
print((root / 'data' / 'hexagrams.json').is_file())
PY
deactivate
```

Then install the exact version in a regular NoneBot project and verify plugin loading, ORM
migrations, image replies, and the documented chat commands.

## 8. Do not release when

Do not publish a release if any of the following is true:

- CI is red.
- `nb orm check` reports schema drift.
- The wheel lacks data, templates, or migrations.
- README promises features not implemented in the package.
- LLM privacy behavior is unclear.
- Known deterministic-prediction or professional-advice claims appear in user-facing text.
