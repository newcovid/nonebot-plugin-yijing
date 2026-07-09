# Server Smoke Test

本清单用于服务器升级、换镜像、换 `nonebot-plugin-htmlrender` / Playwright 基线、从本地 `plugin_dirs` 切换到 GitHub commit / wheel / PyPI 安装后验证 `nonebot-plugin-yijing`。

## 1. 环境基线

推荐记录并确认：

```bash
python -V
pip show nonebot2 nonebot-plugin-htmlrender playwright nonebot-plugin-orm nonebot-plugin-yijing
```

当前 v0.1.1 服务器基线建议：

```text
nonebot2>=2.5.0
nonebot-plugin-htmlrender>=0.7.1
playwright>=1.60.0
```

如果 Docker 镜像把 Playwright Chromium 预装到 `/ms-playwright`，需要确认：

```env
RENDER_BACKEND=playwright
RENDER_STARTUP_MODE=probe
RENDER_STORAGE_PATH=/ms-playwright
RENDER_PLAYWRIGHT={"engine":"chromium","skip_browser_install":true,"close_on_exit":true,"cleanup_legacy_cache":true,"launch_args":"--no-sandbox --disable-dev-shm-usage --disable-gpu"}
```

如果没有预装浏览器，不要使用 `skip_browser_install=true`。

## 2. ORM 检查

```bash
nb orm upgrade
nb orm check
```

通过标准：

```text
无 migration 缺失错误
无 autogenerate mismatch
无表名 / 索引名不一致问题
```

不要把 `ALEMBIC_STARTUP_CHECK=false` 作为生产默认配置。它只能作为临时排障手段。

## 3. 安装方式

如果只是验证 PyPI 包自动安装链路，优先不要全量重建镜像。可在现有容器内临时安装并重启容器：

```bash
docker exec -it nonebot bash -lc 'python -m pip install -U nonebot-plugin-yijing==0.1.1'
docker restart nonebot
```

这适合快速验证“PyPI 包可下载、包资源完整、NoneBot 能加载插件”。验证通过后，再把依赖写回 `/srv/stack/nonebot/requirements.txt`，避免下次重建镜像时丢失：

```bash
grep -q '^nonebot-plugin-yijing' /srv/stack/nonebot/requirements.txt \
  && sed -i 's/^nonebot-plugin-yijing.*/nonebot-plugin-yijing==0.1.1/' /srv/stack/nonebot/requirements.txt \
  || echo 'nonebot-plugin-yijing==0.1.1' >> /srv/stack/nonebot/requirements.txt
```

只有在需要验证 Dockerfile、Playwright 浏览器缓存、系统依赖或重新固化镜像时，才重建：

```bash
docker compose build --no-cache nonebot
docker compose up -d --force-recreate nonebot
```

## 4. 启动日志检查

重启后查看日志：

```bash
docker logs -f --tail=200 nonebot
```

通过标准：

```text
nonebot_plugin_yijing 成功加载
nonebot_plugin_access_control 成功加载
nonebot_plugin_htmlrender 启动探测通过
无 MissingGreenlet
无 Playwright browser executable not found
无 render_template base_url / file directory page 相关错误
```

## 5. 真实群聊命令验收

在一个测试群或低风险群中逐条执行：

```text
易经帮助
易经设置
随机一卦
起卦 此行去山西实习一程怎么样
起卦 此行去山西实习一程怎么样 铜钱
起卦 此行去山西实习一程怎么样 大衍
起卦 此行去山西实习一程怎么样 手动
解卦 需
易经历史
易经记录 <ID>
```

手动起卦建议分别测试：

```text
铜钱
正反正 反反正 正正反 正反反 反正正 反反反
```

```text
大衍
7 8 9 6 7 8
```

通过标准：

```text
所有命令均返回图片或预期的提示图片
历史记录中能看到刚刚起出的记录
易经记录 <ID> 可复现完整长图
重复问题会触发短期相似问题提示
敏感关键词问题会追加专业人士提示
```

## 6. 共享 htmlrender 栈回归

如果同一个 NoneBot 实例还有其他依赖 htmlrender 的插件，至少确认它们仍可渲染。例如：

```text
运行状态
tps
```

通过标准：

```text
共享 htmlrender / Playwright 环境没有被 yijing 插件配置破坏
其他图片插件没有 Chromium 启动错误
```

## 7. 从本地目录切换到包安装时的注意事项

不要同时保留本地插件目录和 pip 安装包：

```text
/srv/stack/nonebot/lolbot/plugins/nonebot_plugin_yijing
```

推荐顺序：

1. 备份 SQLite。
2. 移除本地插件目录或从 `plugin_dirs` 中排除。
3. 安装 GitHub commit、wheel 或 PyPI 版本。
4. 确认 `pyproject.toml` 或 NoneBot 配置中只加载 `nonebot_plugin_yijing` 一份。
5. 执行 ORM 检查。
6. 执行真实群聊命令验收。

## 8. 失败时收集信息

至少保留：

```bash
docker logs --tail=300 nonebot
pip freeze | grep -E "nonebot|htmlrender|playwright|SQLAlchemy|orm|yijing"
nb orm check
```

同时记录失败命令、群聊返回内容、是否启用 LLM、是否启用 `YIJING_STORE_QUESTION=false`。
