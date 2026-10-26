# spec.md — 20261013_local_RAG

依据 intent.md 的技术规格说明。遵循原则：代码精简、优先跑通、不过度设计。

## 1. 架构与数据流

```
【一次性建库】
knowledge_base/ (15+ 份文件)
    │  build_knowledge_base.py
    │  ① 解析（按类型选 parser）→ ② 分块 → ③ 本地 Embedding → ④ 写入 Chroma
    ▼
chroma_db/ (本地持久化向量库)

【运行时问答】
用户提问 (Gradio Web)
    │  rag_agent.py
    │  ① 问题 Embedding → ② Chroma 相似度检索 top-k
    │     ├─ 最高相似度 < 阈值 → 直接回复「知识库中无相关内容」
    │     └─ 命中 → ③ 组装 Prompt（系统提示词 + 检索片段 + 问题）
    │              → ④ DeepSeek 生成答案（附来源引用）→ ⑤ 返回界面
    ▼
用户看到带引用的回答
```

## 2. 项目结构

```
20261013_local_RAG/
├── intent.md                    # 意图文档
├── spec.md                      # 本文档
├── rag_agent_prompts.md         # 系统提示词（与代码分离，沿用既有约定）
├── build_knowledge_base.py      # 一次性建库脚本：解析→分块→向量化→入库
├── rag_agent.py                 # Gradio Web 问答 Agent
├── requirements.txt
├── .env.example
├── .gitignore
├── knowledge_base/              # 知识库原始文件（开发期间收集）
│   ├── pdf/    (≥3 份)
│   ├── docx/   (≥3 份)
│   ├── txt/    (≥3 份)
│   ├── md/     (≥3 份)
│   └── html/   (≥3 份)
├── chroma_db/                   # Chroma 持久化目录（git 忽略，可随时重建）
└── README.md                    # 项目说明（开发完成后编写）
```

## 3. 知识库文件规划（15 份，主题：汉武帝）

| 类型 | 文件（暂定名） | 内容来源策略 |
|---|---|---|
| PDF ×3 | 汉武帝传选段 / 汉武帝时期政策研究 / 资治通鉴汉纪选段 | 优先互联网直接下载可公开获取的 PDF；无合适资源时，用抓取的权威网页内容本地生成 PDF |
| DOCX ×3 | 维基百科·汉武帝 / 汉匈战争专题 / 盐铁专卖与财政改革 | 抓取权威网页内容，用 python-docx 保存 |
| TXT ×3 | 史记·孝武本纪（原文）/ 汉书·武帝纪（原文）/ 汉武帝大事年表 | 维基文库等公开史料原文，保存为纯文本 |
| MD ×3 | 汉武帝生平概述 / 推恩令专题解析 / 罢黜百家独尊儒术专题 | 抓取权威网页内容，整理保存为 Markdown |
| HTML ×3 | 维基百科 / 百度百科 / 历史文章页面 | 直接保存网页为本地 .html 文件 |

- 实施时按实际可获取性调整具体条目，保持每类 ≥3 份、内容主题相关且互有区分（保证检索测试有意义）
- PDF 必须为文字版（非扫描件），否则 pypdf 无法抽取文本

## 4. 建库管线（build_knowledge_base.py）

### 4.1 解析

| 类型 | 库 | 说明 |
|---|---|---|
| .pdf | pypdf | 逐页提取文本 |
| .docx | python-docx | 提取段落文本 |
| .txt | 内置 | 直接读取 |
| .md | 内置 | 去除 Markdown 标记符号后读取 |
| .html | beautifulsoup4 | 提取 `<body>` 可见文本 |

### 4.2 分块

- 中文按段落聚合：以空行/换行切段，段落数量不足时按字符数切
- `CHUNK_SIZE = 500` 字符，`CHUNK_OVERLAP = 50`（切分点回退到最近的句号/换行，避免句子截断）
- 每块 metadata：`{"source": 文件名, "type": 文件类型, "chunk_id": 序号}`

### 4.3 向量化

- 模型：`BAAI/bge-small-zh-v1.5`（sentence-transformers 加载，约 100MB，本地运行）
- 文档块：不加前缀直接编码
- 查询：加 BGE 官方检索指令前缀「为这个句子生成表示以用于检索相关文章：」
- 向量归一化后存入 Chroma（余弦相似度）

### 4.4 存储

- Chroma PersistentClient，路径 `./chroma_db`，collection 名称 `han_wudi`
- 建库脚本可重复执行：每次先删除重建 collection

## 5. 问答 Agent（rag_agent.py）

1. 接收用户问题 → 编码（带 BGE 查询前缀）→ `collection.query(n_results=TOP_K=5)`
2. 相似度阈值判断：最高相似度 `< 0.30` → 直接回复「知识库中无相关内容」，不调用 LLM
3. 命中则组装 Prompt：
   - 系统提示词来自 `rag_agent_prompts.md`（load_prompt 沿用既有项目模式）
   - 上下文：检索片段标注编号与来源 `[1] (来源: xxx.pdf)` 后拼接
   - 要求 LLM：仅依据资料回答、引用来源编号、资料不足时如实说明
4. 调用 DeepSeek（OpenAI 兼容接口，`deepseek-chat`）生成回答
5. 回答后附「参考来源」清单（去重后的命中文件名）

## 6. 界面（Gradio）

- 单聊天框 + 对话历史（gr.ChatInterface，沿用成语接龙项目风格）
- 默认地址 `http://127.0.0.1:7866`（端口可由环境变量 `WEB_PORT` 覆盖）

## 7. 系统提示词（rag_agent_prompts.md，要点）

- 角色设定：汉武帝历史知识答疑助手
- 硬性规则：只根据提供的资料回答；回答末尾标注引用的来源编号；资料不含答案时明确说明，不编造
- 输出格式：先直接回答，再列引用

## 8. 配置（.env.example）

```
DEEPSEEK_API_KEY=sk-xxx        # 必填
DEEPSEEK_MODEL=deepseek-chat    # 可选，默认 deepseek-chat
HF_ENDPOINT=https://hf-mirror.com  # 可选，国内网络加速模型下载
WEB_PORT=7866                   # 可选
```

## 9. 依赖（requirements.txt）

```
openai>=1.40,<2
gradio>=4.44,<7
chromadb>=0.5,<2
sentence-transformers>=3.0,<6
pypdf>=4,<6
python-docx>=1.1,<2
beautifulsoup4>=4.12,<5
```

说明：sentence-transformers 会安装 PyTorch（体积较大，属本地 Embedding 的必要成本）；首次运行自动下载 bge-small-zh-v1.5 模型。

## 10. 运行步骤

```powershell
pip install -r requirements.txt
# 配置 .env（DEEPSEEK_API_KEY 必填）
python build_knowledge_base.py   # 一次性建库
python rag_agent.py              # 启动 Web 问答
```

## 11. 测试计划

| 用例 | 问题 | 预期 |
|---|---|---|
| T1 建库 | 执行建库脚本 | 15+ 文件全部解析，chunk 数 > 0，chroma_db 生成 |
| T2 知识命中 | 推恩令的内容是什么？ | 基于资料回答 + 引用 md/docx 来源 |
| T3 史料命中 | 卫青取得了哪些战功？ | 基于资料回答 + 引用对应来源 |
| T4 知识命中 | 汉武帝在思想上采取了什么措施？ | 命中「罢黜百家」相关文档并正确回答 |
| T5 拒答 | 明朝的皇帝有哪些？ | 相似度低于阈值，明确回复知识库无相关内容，不编造 |

## 12. 开发顺序

1. 收集知识库文件（互联网搜索/下载/格式转换）
2. `rag_agent_prompts.md` + `.env.example` + `requirements.txt` + `.gitignore`
3. `build_knowledge_base.py`（建库并本地验证 chunk 结果）
4. `rag_agent.py`（Gradio + 检索 + DeepSeek）
5. 按测试计划逐项验证
6. 编写 README.md
