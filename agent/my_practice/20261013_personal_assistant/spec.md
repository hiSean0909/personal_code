# spec.md — 20261013_personal_assistant

依据 intent.md 的技术规格说明。遵循原则：代码精简、优先跑通、不过度设计。

## 1. AI Native 设计映射

| AI Native 思想 | 本项目落地方式 |
|---|---|
| 提示词即产品 | 助手人设 / 能力 / 风格全部在 `personal_assistant_prompts.md`，代码零业务规则 |
| 上下文即状态 | 会话历史是唯一核心状态，每轮组装 `system + 历史窗口 + 新输入` 送入模型 |
| 模型即引擎 | OpenAI 兼容接口 + 全环境变量配置，换模型不改代码 |
| 自然语言即界面 | 聊天框 + 流式输出（打字机效果） |
| 代码是薄外壳 | 单文件实现：配置加载 → 上下文组装 → LLM 流式调用 → Gradio UI |

## 2. 架构与数据流

```
用户输入 (Gradio 对话框)
    │  personal_assistant.py
    │  ① 组装消息列表：系统提示词 + 最近 MAX_HISTORY_ROUNDS 轮历史 + 当前输入
    │  ② 调用 DeepSeek（stream=True 流式接口）
    │  ③ 每收到一段 delta 就 yield 给前端 → 打字机效果
    │  ④ 本轮 user / assistant 消息由 ChatInterface 自动记入会话历史
    ▼
流式呈现的 AI 回复
```

## 3. 项目结构

```
20261013_personal_assistant/
├── intent.md                       # 意图文档
├── spec.md                         # 本文档
├── personal_assistant_prompts.md   # 系统提示词（产品逻辑载体，与代码分离）
├── personal_assistant.py           # 对话助手（唯一源码文件）
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md                       # 项目说明（开发完成后编写）
```

## 4. 对话助手（personal_assistant.py）

1. `init_client()`：读取环境变量并做一次连通性探测（沿用既有项目模式），失败直接抛错
2. `load_prompt()`：从 `personal_assistant_prompts.md` 读取系统提示词，文件缺失时用内置兜底
3. `respond(message, history)`（生成器，供 ChatInterface 流式调用）：
   - 组装 `messages = [system] + history[-MAX_HISTORY_ROUNDS*2:] + [当前输入]`
   - `client.chat.completions.create(stream=True)`，逐段拼接 delta 并 `yield` 部分回复
   - 异常时 yield 一条错误提示，不中断会话
4. `MAX_HISTORY_ROUNDS = 20`：送入模型的历史窗口，防止 token 无限膨胀（前端仍显示完整历史）

## 5. 界面（Gradio）

- `gr.ChatInterface`：单聊天框 + 完整对话历史展示，fn 为生成器即自动流式刷新
- 标题「🤖 个人助手」，默认地址 `http://127.0.0.1:7867`（`WEB_PORT` 可覆盖，仅本地监听）

## 6. 系统提示词（personal_assistant_prompts.md，要点）

- 角色：通用个人助手（知识问答、写作、头脑风暴、日常闲聊等）
- 风格：简洁直接，先给结论再展开；用户用什么语言提问就用什么语言回答
- 边界：不确定就说不确定，不编造

## 7. 配置（.env.example）

```
DEEPSEEK_API_KEY=sk-xxx                      # 必填
DEEPSEEK_BASE_URL=https://api.deepseek.com   # 可选
DEEPSEEK_MODEL=deepseek-chat                  # 可选，默认 deepseek-chat
WEB_PORT=7867                                 # 可选
```

说明：本地运行时在 PowerShell 设置 `$env:DEEPSEEK_API_KEY='sk-xxx'`（沿用既有项目方式，不引入 dotenv）。

## 8. 依赖（requirements.txt）

```
openai>=1.40,<2
gradio>=4.44,<7
httpx>=0.27,<1
```

## 9. 运行步骤

```powershell
pip install -r requirements.txt
$env:DEEPSEEK_API_KEY='sk-xxx'
python personal_assistant.py
```

## 10. 测试计划

| 用例 | 操作 | 预期 |
|---|---|---|
| T1 连接 | 启动脚本 | 连通性探测通过，浏览器打开 http://127.0.0.1:7867 |
| T2 多轮上下文 | 说「我叫小明」→ 再问「我叫什么名字？」 | 正确回答「小明」 |
| T3 流式 | 任意提问 | 回复逐字呈现，非一次性出现 |
| T4 长历史 | 连续对话 25+ 轮后继续提问 | 正常回答（历史窗口截断生效，无报错） |
| T5 人设热改 | 修改提示词文件后重启 | 助手风格按新提示词变化，代码零改动 |

## 11. 开发顺序

1. `personal_assistant_prompts.md` + `.env.example` + `requirements.txt` + `.gitignore`
2. `personal_assistant.py`（配置加载 + 上下文组装 + 流式调用 + Gradio）
3. 按测试计划逐项验证
4. 编写 README.md
