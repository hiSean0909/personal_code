# 20261013_personal_assistant — 本地个人助手

本地运行的对话式个人助手：一个聊天窗口，背后调用 DeepSeek 大模型，支持多轮上下文与流式输出。按「AI Native」思想开发——**大模型是引擎，代码是薄外壳**。

---

## AI Native 设计

| 思想 | 落地方式 |
|---|---|
| 提示词即产品 | 助手人设 / 风格 / 边界全部在 `personal_assistant_prompts.md`，代码零业务规则；改提示词 = 改产品 |
| 上下文即状态 | 会话历史是唯一核心状态，每轮组装 `系统提示词 + 最近 20 轮历史 + 当前输入` 送入模型 |
| 模型即引擎 | OpenAI 兼容接口 + 全环境变量配置（`DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL`），换模型零代码改动 |
| 自然语言即界面 | 聊天框 + 流式打字机输出 |

## 文件清单（7 个，全部有用）

| # | 文件 | 作用 | 必需？ |
| - | --- | --- | --- |
| 1 | `personal_assistant.py` | **主程序** — 配置加载、上下文组装、流式调用、Gradio 界面，单文件约 150 行 | ✅ 核心 |
| 2 | `personal_assistant_prompts.md` | **System Prompt** — 助手的角色 / 风格 / 边界，产品逻辑载体，与代码完全分离 | ✅ 核心 |
| 3 | `requirements.txt` | **Python 依赖** — `openai`、`gradio`、`httpx`，限定大版本上限 | ✅ 构建 |
| 4 | `.env.example` | **环境变量模板** — 复制参考后设置 `DEEPSEEK_API_KEY` 等 | ✅ 配置 |
| 5 | `.gitignore` | **Git 忽略规则** — 屏蔽 `.env`、`__pycache__`、`.venv` | ⚠️ 推荐 |
| 6 | `intent.md` / `spec.md` | **设计文档** — 意图与技术规格 | ⚠️ 说明 |
| 7 | `readme.md` | **本文档** | ⚠️ 说明 |

## 本地运行（PowerShell）

```powershell
# 1. 创建虚拟环境并安装依赖（首次）
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# 2. 设置 API Key
$env:DEEPSEEK_API_KEY="sk-xxxxxxxx"

# 3. 启动
.\.venv\Scripts\python personal_assistant.py
```

浏览器打开 `http://127.0.0.1:7867` 开始对话（端口用 `WEB_PORT` 覆盖）。

## 已验证

- ✅ 多轮上下文：模型记住对话中提到的名字并正确回答
- ✅ 流式输出：逐段 yield，打字机效果
- ✅ 长对话：超过 20 轮自动截断历史窗口，token 不膨胀
- ✅ 浏览器端到端测试：两轮对话上下文连贯
