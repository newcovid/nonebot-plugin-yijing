# Release Guide

This document describes the release process for `nonebot-plugin-yijing`.

The project is still alpha. Treat every release as reproducibility work first and feature delivery second.

## 1. Release channels

Recommended progression:

1. GitHub commit install for server alpha validation.
2. Local wheel install for package validation.
3. TestPyPI for first public package rehearsal, if needed.
4. PyPI for tagged alpha release.
5. NoneBot Plugin Store submission only after CI, docs, privacy notes, and package metadata are stable.

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
- No private `.env`, SQLite database, logs, cache, or server-only path is included.
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

## 5. Server validation from GitHub commit

Before PyPI, validate a specific commit on the real test server:

```text
nonebot-plugin-yijing @ git+ssh://git@github.com/newcovid/nonebot-plugin-yijing.git@<commit-sha>
```

Then run:

```bash
nb orm upgrade
nb orm check
```

Follow `docs/server-smoke-test.md` for group command testing.

## 6. Tagging

Use a `v` prefix for release tags:

```bash
git tag v0.1.1
git push origin v0.1.1
```

The publish workflow is configured to run on tags matching `v*` and can also be dispatched manually.

## 7. PyPI publishing

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

## 8. Post-release checks

After publishing:

```bash
python -m venv .venv-release-test
. .venv-release-test/bin/activate
python -m pip install --upgrade pip
python -m pip install nonebot-plugin-yijing==0.1.1
python - <<'PY'
import importlib.resources as resources
root = resources.files('nonebot_plugin_yijing')
print((root / 'data' / 'hexagrams.json').is_file())
PY
deactivate
```

Then update the server to the exact version and repeat the server smoke test.

## 9. Do not release when

Do not publish a release if any of the following is true:

- CI is red.
- `nb orm check` reports schema drift.
- The wheel lacks data, templates, or migrations.
- README promises features not implemented in the package.
- LLM privacy behavior is unclear.
- Known deterministic-prediction or professional-advice claims appear in user-facing text.
