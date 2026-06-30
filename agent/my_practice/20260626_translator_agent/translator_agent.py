import os
from openai import OpenAI

# 获取脚本所在目录，后续所有文件路径都基于此目录，避免运行目录不同导致找不到文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 1. 配置与初始化
# ==========================================

# ---- 运行模式：CLI / WEB，云端 Docker 模式强制 WEB ----
RUN_MODE = os.getenv("RUN_MODE", "").upper()

# ---- 唯一 LLM 后端：DeepSeek（云端 API） ----
# 所有参数都通过环境变量注入，代码中不保留任何硬编码
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


def init_client():
    """
    初始化 DeepSeek 客户端并做一次连通性探测。
    失败直接抛出，避免把一个不可用的 client 传到后面，让请求在每次调用时才报错。
    """
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "未设置 DEEPSEEK_API_KEY 环境变量。\n"
            "  - 本地开发：先在 PowerShell 执行  $env:DEEPSEEK_API_KEY='sk-xxx'\n"
            "  - Docker 部署：在 .env 文件里填上 DEEPSEEK_API_KEY=sk-xxx 后重启容器"
        )

    print("🔄 正在测试 DeepSeek 连接...")
    try:
        test_client = OpenAI(
            base_url=DEEPSEEK_BASE_URL,
            api_key=DEEPSEEK_API_KEY,
            timeout=15,
        )
        test_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
            timeout=15,
        )
    except Exception as e:
        raise RuntimeError(f"DeepSeek 连接失败: {e}\n  请检查：DEEPSEEK_API_KEY 是否正确 / 服务器能否访问 {DEEPSEEK_BASE_URL}") from e

    print(f"✅ DeepSeek 连接成功，使用模型: {DEEPSEEK_MODEL}")
    return test_client, DEEPSEEK_MODEL


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

    with gr.Blocks() as demo:
        gr.ChatInterface(
            fn=respond,
            chatbot=gr.Chatbot(elem_classes="chatbot-container"),
            textbox=gr.Textbox(elem_id="input-box", placeholder="输入英文单词、短语或中文句子...", lines=1),
            title="📖 翻译助手 Translator Agent",
            description=(
                "输入**英文单词**、**短语**、**中文词语**或**中文句子**，"
                "AI 将自动识别并按照对应模板解析翻译。"
            ),
        )

    # 云端部署时监听所有网卡；本地开发默认只监听 127.0.0.1（用 WEB_HOST 环境变量覆盖）
    server_name = os.getenv("WEB_HOST", "0.0.0.0" if RUN_MODE else "127.0.0.1")
    server_port = int(os.getenv("WEB_PORT", "7860"))
    web_share = os.getenv("WEB_SHARE", "false").lower() == "true"
    web_root_path = os.getenv("WEB_ROOT_PATH", "") or None  # 反代子路径时使用，如 "/translator"

    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=web_share,
        root_path=web_root_path,
        css="""
        #input-box textarea { background-color: #e8f4fd !important; }
        """,
    )


# ==========================================
# 6. 启动程序
# ==========================================
def timed_input(prompt, timeout=3, default="1"):
    """带超时的输入函数，超时自动返回默认值"""
    import msvcrt
    import time

    print(prompt, end="", flush=True)
    start = time.time()
    chars = []

    while time.time() - start < timeout:
        if msvcrt.kbhit():
            ch = msvcrt.getwche()
            if ch == "\r":  # 回车
                print()
                return "".join(chars)
            elif ch == "\b":  # 退格
                if chars:
                    chars.pop()
                    print(" \b", end="", flush=True)  # 擦除字符
            else:
                chars.append(ch)
        else:
            time.sleep(0.05)

    # 超时，显示默认选择
    print(f"\n⏱ 超时，自动选择默认模式（{default}）")
    return default


if __name__ == "__main__":
    # 云端 / Docker 场景：设置 RUN_MODE=WEB 或 RUN_MODE=CLI，跳过交互式选择（容器没有 TTY）
    if RUN_MODE == "CLI":
        run_cli()
    elif RUN_MODE == "WEB":
        run_web()
    else:
        print("请选择启动模式：")
        print("  1. Web 界面（浏览器）")
        print("  2. 命令行模式")
        choice = timed_input("输入 1 或 2，回车确认（3秒无操作自动选 1）: ").strip()

        if choice == "2":
            run_cli()
        else:
            run_web()
