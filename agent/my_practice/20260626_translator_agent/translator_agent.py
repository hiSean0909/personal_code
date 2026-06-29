import os
from openai import OpenAI

# 获取脚本所在目录，后续所有文件路径都基于此目录，避免运行目录不同导致找不到文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 1. 配置与初始化
# ==========================================

# ---- 方案一：DeepSeek（优先使用） ----
# API Key 只从环境变量读取，不硬编码，防止泄露
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = "deepseek-v4-flash"

# ---- 方案二：Ollama 本地模型（降级方案） ----
# Ollama 是本地部署的开源大模型，完全离线运行、不需要联网
# 需要先启动 Ollama 服务（命令行运行: ollama serve）
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_API_KEY = "ollama"
OLLAMA_MODEL = "qwen2.5:7b"


# ---- 自动选择：先测试 DeepSeek，失败则降级到 Ollama ----
def init_client():
    """
    先尝试连接 DeepSeek。
    如果 DeepSeek 通（网络正常、API Key 有效），就返回 DeepSeek 客户端；
    如果 DeepSeek 不通，自动降级到本地 Ollama 模型。
    """
    print("🔄 正在测试 DeepSeek 连接...")
    try:
        test_client = OpenAI(
            base_url=DEEPSEEK_BASE_URL,
            api_key=DEEPSEEK_API_KEY
        )
        # 发一个极简请求测试连通性（只返回 1 个 token，省流量）
        test_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1
        )
        print(f"✅ DeepSeek 连接成功，使用模型: {DEEPSEEK_MODEL}")
        return test_client, DEEPSEEK_MODEL
    except Exception as e:
        print(f"❌ DeepSeek 连接失败: {e}")
        print(f"🔄 降级到 Ollama 本地模型: {OLLAMA_MODEL}")
        ollama_client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key=OLLAMA_API_KEY
        )
        return ollama_client, OLLAMA_MODEL


# 程序启动时执行初始化，确定最终使用哪个模型
client, MODEL_NAME = init_client()


# ==========================================
# 2. 读取提示词文件
# ==========================================
def load_prompt(file_path="translator_agent_prompts.md"):
    """
    从本地 Markdown 文件中读取系统提示词（System Prompt）。
    如果文件不存在，会返回一个默认的提示词作为兜底。
    """
    # 基于脚本所在目录拼接完整路径，不管从哪里运行都能找到文件
    full_path = os.path.join(SCRIPT_DIR, file_path)

    # 检查文件是否存在，避免 FileNotFoundError
    if not os.path.exists(full_path):
        print(f"⚠️ 未找到提示词文件（{full_path}），使用默认提示词。")
        return "你是一个专业的中英翻译助手。"

    # 以 UTF-8 编码读取文件内容，并去掉首尾多余空白
    with open(full_path, "r", encoding="utf-8") as f:
        prompt_content = f.read().strip()

    return prompt_content


# 提前加载提示词，后续直接复用（只读取一次）
SYSTEM_PROMPT = load_prompt()


# ==========================================
# 3. 核心问答函数（Gradio 和 CLI 共用）
# ==========================================
def ask_agent(user_input: str) -> str:
    """
    向大模型发送请求，返回 AI 的回答文本。
    每次都是独立请求，只传 system prompt + 当前用户输入，不累积历史。
    """
    user_input = user_input.strip()  # 去除首尾空白字符（空格、tab、换行）
    if not user_input:
        return "输入为空，请重新输入。"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ 调用 {MODEL_NAME} 出错: {e}"


# ==========================================
# 4. 命令行模式（CLI）
# ==========================================
def run_cli():
    """
    命令行交互模式。
    在终端中逐行输入、逐行输出，输入 'exit' 退出。
    """
    prompt_line_count = SYSTEM_PROMPT.count("\n") + 1
    print(f"📝 已加载系统提示词（共 {prompt_line_count} 行）")
    print(f"🤖 当前模型：{MODEL_NAME}")
    print("🤖 翻译助手已启动！输入 'exit' 退出。")

    while True:
        user_input = input("\n👤 用户: ")
        if user_input.lower() == 'exit':
            print("👋 再见！")
            break

        ai_reply = ask_agent(user_input)
        print(f"🤖 AI: {ai_reply}")


# ==========================================
# 5. Web 界面模式（Gradio）
# ==========================================
def run_web():
    """
    Web 交互模式。
    启动一个本地浏览器页面，通过对话框与 Agent 交互。
    """
    prompt_line_count = SYSTEM_PROMPT.count("\n") + 1
    print(f"📝 已加载系统提示词（共 {prompt_line_count} 行）")
    print(f"🤖 当前模型：{MODEL_NAME}")

    import gradio as gr

    # Gradio ChatInterface 要求回调函数签名：fn(message, history) -> str
    def respond(message, history):
        return ask_agent(message)

    with gr.Blocks(css="""
        #input-box textarea {
            background-color: #e8f4fd !important;
        }
        .chatbot-container {
            height: calc(100vh - 320px) !important;
            min-height: 200px;
        }
    """) as demo:
        gr.ChatInterface(
            fn=respond,
            chatbot=gr.Chatbot(elem_classes="chatbot-container"),
            textbox=gr.Textbox(elem_id="input-box", placeholder="输入英文单词、短语或中文句子...", lines=3),
            title="📖 翻译助手 Translator Agent",
            description=(
                "输入**英文单词**、**短语**、**中文词语**或**中文句子**，"
                "AI 将自动识别并按照对应模板解析翻译。"
            ),
        )

    demo.launch(
        server_name="127.0.0.1",  # 只监听本地，不暴露到局域网
        server_port=7860,          # Gradio 默认端口
        share=False,               # 不生成公网链接
    )


# ==========================================
# 6. 启动程序
# ==========================================
if __name__ == "__main__":
    print("请选择启动模式：")
    print("  1. Web 界面（浏览器）")
    print("  2. 命令行模式")
    choice = input("输入 1 或 2，回车确认: ").strip()

    if choice == "2":
        run_cli()
    else:
        run_web()
