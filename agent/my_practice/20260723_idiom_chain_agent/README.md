# 成语接龙 AI 游戏

基于 DeepSeek API 的成语接龙 Web 游戏，支持广义成语（四字成语、歇后语、俗语等）和宽松拼音匹配。

## 功能特性

- **广义成语支持**：不限于四字成语，包括歇后语、俗语、惯用语等
- **宽松拼音匹配**：
  - 声调不同可匹配（如：一声和四声）
  - 平舌音和卷舌音互通（z/zh、c/ch、s/sh）
  - 前鼻音和后鼻音互通（an/ang、en/eng、in/ing）
- **AI 智能接龙**：使用 DeepSeek 大语言模型，支持多轮对话
- **Web 界面**：基于 Gradio 的简洁交互界面
- **游戏状态管理**：记录得分、历史对局、防止重复

## 项目结构

```
20260723_idiom_chain_agent/
├── idiom_chain_agent.py      # 主程序
├── idiom_chain_prompts.md    # AI 系统提示词
├── requirements.txt          # Python 依赖
└── README.md                 # 项目说明
```

## 环境要求

- Python 3.10+
- DeepSeek API Key

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖包：
- `openai` - OpenAI 兼容 API 客户端
- `gradio` - Web 界面框架
- `httpx` - HTTP 客户端
- `pypinyin` - 汉字拼音转换

## 配置

设置环境变量：

```powershell
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-xxx"

# 可选配置
$env:DEEPSEEK_MODEL="deepseek-chat"  # 默认：deepseek-chat
$env:WEB_PORT="7865"                  # 默认：7864
$env:WEB_HOST="127.0.0.1"            # 默认：127.0.0.1
```

## 运行

```bash
python idiom_chain_agent.py
```

启动后访问：http://127.0.0.1:7864

## 游戏规则

1. 玩家输入一个成语/短语（至少 4 个字）
2. AI 用最后一个字的读音开头接龙
3. 不能重复已用过的成语
4. 拼音匹配规则宽松（声调、平翘舌、前后鼻音均可）
5. AI 无法接龙时回复"认输"，游戏结束

## 示例

```
玩家：无话可说
AI：说三道四

玩家：四面楚歌
AI：歌功颂德

玩家：德高望重
AI：重见天日
```

## 技术细节

- **拼音工具**：使用 `pypinyin` 库获取汉字拼音，通过 `normalize_pinyin()` 实现宽松匹配
- **AI 调用**：最多重试 5 次，首次调用前等待 5 秒预热，重试间隔 3 秒
- **成语提取**：正则表达式匹配 2-12 个连续汉字，遍历所有候选成语

## 许可证

MIT
