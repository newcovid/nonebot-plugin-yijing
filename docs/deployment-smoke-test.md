# Deployment Smoke Test

This checklist validates that `nonebot-plugin-yijing` can be installed from a
package source, loaded by a NoneBot project, migrate its ORM schema, render
images, and respond to chat commands.

The steps are intentionally generic. Replace placeholder paths, container names,
and process commands with the values used by your deployment.

## 1. Environment Baseline

Record the package versions before testing:

```bash
python -V
python -m pip show nonebot2 nonebot-plugin-htmlrender playwright nonebot-plugin-orm nonebot-plugin-yijing
```

Recommended runtime baselines:

```text
nonebot2>=2.5.0
nonebot-plugin-htmlrender>=0.7.1
playwright>=1.60.0
```

If your image preinstalls Playwright Chromium into `/ms-playwright`, use a
configuration similar to:

```env
RENDER_BACKEND=playwright
RENDER_STARTUP_MODE=probe
RENDER_STORAGE_PATH=/ms-playwright
RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":true,"close_on_exit":true,"cleanup_legacy_cache":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}
```

Only set `skip_browser_install=true` when the browser is actually present in the
runtime image.

## 2. Package Installation

Install the exact package version under test:

```bash
python -m pip install -U nonebot-plugin-yijing==0.1.4
```

For commit-level validation before a release:

```bash
python -m pip install "nonebot-plugin-yijing @ git+https://github.com/newcovid/nonebot-plugin-yijing.git@<commit-sha>"
```

Do not load both a local plugin directory and the installed package at the same
time. Keep only one `nonebot_plugin_yijing` source on `sys.path`.

## 3. ORM Checks

After first install or upgrade:

```bash
nb orm upgrade
nb orm check
```

Expected result:

```text
no missing revision
no duplicate branch label
no autogenerate drift
```

Do not use `ALEMBIC_STARTUP_CHECK=false` as a normal deployment setting. It is
only a temporary local troubleshooting aid.

If Alembic reports a missing revision, inspect the database `alembic_version`
table and the installed migration files before changing database state. Back up
the database before any manual repair.

## 4. Startup Log Check

Restart the NoneBot process with the package installed, then inspect logs.

Expected result:

```text
nonebot_plugin_yijing loads successfully
nonebot_plugin_access_control loads successfully
nonebot_plugin_htmlrender startup probe succeeds
no MissingGreenlet
no Playwright browser executable not found
no Alembic duplicate branch label
no Alembic missing revision
```

## 5. Chat Command Acceptance

Run these commands in a low-risk test chat:

```text
易经帮助
易经设置
随机一卦
起卦 测试问题
起卦 测试问题 铜钱
起卦 测试问题 大衍
起卦 测试问题 手动
解卦 需
易经历史
易经记录 <ID>
```

Manual coin input:

```text
铜钱
正反正 反反正 正正反 正反反 反正正 反反反
```

Manual yarrow input:

```text
大衍
7 8 9 6 7 8
```

Expected result:

```text
commands return images or expected prompt images
new records appear in history
易经记录 <ID> renders the saved record
similar repeated questions trigger the configured repeat handling
sensitive-topic prompts include a professional-advice notice
```

## 6. Shared Rendering Regression

If the same NoneBot project has other image-rendering plugins, run at least one
known command from each plugin after enabling yijing.

Expected result:

```text
the shared htmlrender / Playwright setup still works
no other plugin reports Chromium startup errors
```

## 7. Failure Report Template

When reporting a deployment failure, include:

```bash
python -V
python -m pip freeze | grep -E "nonebot|htmlrender|playwright|SQLAlchemy|orm|yijing"
nb orm heads
nb orm current
nb orm check
```

Also include:

- The package version or commit SHA under test.
- The command that failed.
- The relevant startup or command log excerpt.
- Whether LLM support is enabled.
- Whether `YIJING_STORE_QUESTION=false` is enabled.
