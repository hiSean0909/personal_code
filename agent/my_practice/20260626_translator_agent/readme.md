# 20260626_translator_agent — 翻译助手 Agent

基于 DeepSeek API 的中英翻译助手，支持 Web（Gradio）和 CLI 两种交互模式。云服务器容器化部署。

---

## 文件清单（9 个，全部有用）

| # | 文件                            | 作用                                                                                                                                              | 必需？            |
| - | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| 1 | `translator_agent.py`         | **主程序** — 读取环境变量连接 DeepSeek API；加载 prompt 文件；CLI + Web（Gradio）双模式；`RUN_MODE` 环境变量控制 Docker 下跳过交互式选择 | ✅ 核心           |
| 2 | `translator_agent_prompts.md` | **System Prompt** — 翻译模板 + 意图识别规则 + 4 种输入格式（单词/短语/中文词/中文句），提示词与代码完全分离                                | ✅ 核心           |
| 3 | `requirements.txt`            | **Python 依赖** — `openai`、`gradio`、`httpx`，已限大版本上限（`<2`、`<7`、`<1`）防止未来破坏性升级                            | ✅ 构建           |
| 4 | `Dockerfile`                  | **容器镜像定义** — 基于 `python:3.12-slim`；apt/pip 国内源加速；非 root 用户运行；时区上海                                               | ✅ 部署           |
| 5 | `docker-compose.yml`          | **容器编排** — 端口映射（7860）；健康检查（curl 每 30s）；日志轮转（50MB×3）；自动重启；从 `.env` 注入 API Key                          | ✅ 部署           |
| 6 | `.env.example`                | **环境变量模板** — 复制为 `.env` 后填入 `DEEPSEEK_API_KEY`；含端口 / 反代子路径等可选配置，防 .env 误提交 Git                          | ✅ 配置           |
| 7 | `deploy.sh`                   | **服务端一键脚本** — `install_docker` / `start` / `stop` / `restart` / `update` / `logs` / `status` 共 7 个子命令            | ✅ 运维           |
| 8 | `.gitignore`                  | **Git 忽略规则** — 屏蔽 `.env`、`__pycache__`、`.pem` 私钥、构建产物 `*.zip`                                                       | ⚠️ 非必需但推荐 |
| 9 | `readme.md`                   | **本文档** — 项目说明、文件作用、部署步骤、运维速查                                                                                        | ⚠️ 说明文档     |

> 已删除：`upload.ps1`（语法错误的 Windows 上传脚本），打包上传改用两条手打命令更稳。

---

## 本地运行（本地电脑 · PowerShell）

设置 API Key：

```powershell
$env:DEEPSEEK_API_KEY="sk-xxxxxxxx"
```

安装依赖：

```powershell
pip install -r requirements.txt
```

启动（3 秒内可选择 CLI 或 Web，超时默认 Web）：

```powershell
python translator_agent.py
```

---

## 运维速查

### 日常操作（云端服务器 · SSH 终端）

先 cd 到项目目录：

```bash
cd /opt/translator-agent
```

看服务状态：

```bash
docker ps
```

看实时日志：

```bash
docker logs translator-agent --tail 50
```

重启（不改代码）：

```bash
docker compose restart
```

停服务：

```bash
docker compose down
```

重新启动：

```bash
docker compose up -d
```

### 更新代码

#### 方案一：完整打包部署（改任意文件时用）

改完 `.py` / `.md` / `Dockerfile` / `requirements.txt` 后：

**本地电脑 · PowerShell** — 先 cd 到项目目录：

```powershell
cd d:\personal\git\personal_code\agent\my_practice\20260626_translator_agent
```

打包所有文件为 zip：

```powershell
Compress-Archive -Path translator_agent.py, translator_agent_prompts.md, requirements.txt, Dockerfile, docker-compose.yml, .env.example, deploy.sh -DestinationPath translator-agent-deploy.zip -Force
```

上传 zip 到服务器：

```powershell
scp -P 22 -o "StrictHostKeyChecking=accept-new" translator-agent-deploy.zip ubuntu@122.51.135.229:/tmp/
```

**云端服务器 · SSH 终端** — 先 cd 到项目目录：

```bash
cd /opt/translator-agent
```

解压覆盖文件：

```bash
unzip -o /tmp/translator-agent-deploy.zip
```

重新构建并启动容器：

```bash
docker compose up -d --build
```

> `.env`（含 API Key）不在 zip 白名单中，不会被覆盖。

#### 方案二：服务器端直接编辑（最常用）

如果**只修改 `translator_agent_prompts.md`**（最频繁的操作），无需走完整打包部署流程。前提是服务器端 `docker-compose.yml` 已配置 volume 挂载（将 prompts 文件挂入容器而非打包进镜像），只需两步：

**云端服务器 · SSH 终端** — 先 cd 到项目目录：

```bash
cd /opt/translator-agent
```

直接编辑 prompts 文件：

```bash
nano translator_agent_prompts.md
```

重启容器即可生效（无需 --build）：

```bash
docker compose restart
```

> 原理：`docker-compose.yml` 中通过 `volumes` 将宿主机上的 `translator_agent_prompts.md` 挂载到容器内，容器启动时读取的是挂载版本而非镜像中的副本，因此修改后只需重启容器。

#### 方案三：本地编辑 + scp 上传（Windows 推荐）

如果在本地修改 `translator_agent_prompts.md`，然后上传覆盖服务器文件：

**本地电脑 · PowerShell** — 先 cd 到项目目录：

```powershell
cd d:\personal\git\personal_code\agent\my_practice\20260626_translator_agent
```

上传 prompts 文件到服务器：

```powershell
scp -P 22 -o "StrictHostKeyChecking=accept-new" translator_agent_prompts.md ubuntu@122.51.135.229:/opt/translator-agent/
```

**云端服务器 · SSH 终端** — 先 cd 到项目目录：

```bash
cd /opt/translator-agent
```

重启容器生效（无需 --build）：

```bash
docker compose restart
```

### 清理（云端服务器 · SSH 终端）

清理悬空旧镜像（频繁 rebuild 后）：

```bash
docker image prune -f
```

清理所有构建缓存：

```bash
docker builder prune -f
```

### 常见问题

**浏览器访问超时**

检查云服务器防火墙是否放行 7860 TCP。

**容器启动后秒退**

查看日志定位错误：

```bash
docker logs translator-agent
```

通常是 API Key 未设或网络不通。

**DeepSeek 连接失败**

检查 `.env` 中 `DEEPSEEK_API_KEY` 格式（`sk-` 开头），以及额度是否充足。
