import os

from openai import OpenAI
import httpx

# 获取脚本所在目录，后续所有文件路径都基于此目录，避免运行目录不同导致找不到文件
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 1. 配置与初始化
# ==========================================

# ---- 唯一 LLM 后端：DeepSeek（云端 API，OpenAI 兼容接口） ----
# 所有参数都通过环境变量注入，代码中不保留任何硬编码（换模型零代码改动）
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ---- 上下文窗口：送入模型的最大历史轮数（一轮 = user + assistant 两条消息） ----
# 防止长对话 token 无限膨胀；前端仍显示完整历史
MAX_HISTORY_ROUNDS = 20

# 提示词文件缺失时的兜底
DEFAULT_PROMPT = "你是一个乐于助人的个人助手，回答简洁、准确、友好。"


def init_client():
    """
    初始化 DeepSeek 客户端并做一次连通性探测。
    失败直接抛出，避免把一个不可用的 client 传到后面。
    """
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "未设置 DEEPSEEK_API_KEY 环境变量。\n"
            "  - 本地开发：先在 PowerShell 执行  $env:DEEPSEEK_API_KEY='sk-xxx'"
        )

    print("🔄 正在测试 DeepSeek 连接...")
    try:
        client = OpenAI(
            base_url=DEEPSEEK_BASE_URL,
            api_key=DEEPSEEK_API_KEY,
            timeout=httpx.Timeout(120.0, connect=15.0),
        )
        client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
            timeout=30,
        )
    except Exception as e:
        raise RuntimeError(
            f"DeepSeek 连接失败: {e}\n  请检查：DEEPSEEK_API_KEY 是否正确 / 能否访问 {DEEPSEEK_BASE_URL}"
        ) from e

    print(f"✅ DeepSeek 连接成功，使用模型: {DEEPSEEK_MODEL}")
    return client


# ==========================================
# 2. 读取提示词文件（提示词即产品：助手的一切行为在这里定义）
# ==========================================

def load_prompt(file_path="personal_assistant_prompts.md"):
    """从本地 Markdown 文件中读取系统提示词，文件不存在时用默认提示词兜底。"""
    full_path = os.path.join(SCRIPT_DIR, file_path)

    if not os.path.exists(full_path):
        print(f"⚠️ 未找到提示词文件（{full_path}），使用默认提示词。")
        return DEFAULT_PROMPT

    with open(full_path, "r", encoding="utf-8") as f:
        return f.read().strip()


# 程序启动时执行初始化
client = init_client()
SYSTEM_PROMPT = load_prompt()


# ==========================================
# 3. 核心对话函数（上下文即状态：每轮组装完整上下文交给模型）
# ==========================================

def respond(message, history):
    """
    ChatInterface 的流式回调（生成器）。
    ① 组装消息：系统提示词 + 历史窗口 + 当前输入
    ② 流式调用大模型，每收到一段就 yield 给前端 → 打字机效果
    这里没有任何业务规则，助手的行为完全由系统提示词驱动。
    """
    if not message.strip():
        yield "请输入内容。"
        return

    # 上下文组装：system + 最近 MAX_HISTORY_ROUNDS 轮历史 + 当前输入
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history[-MAX_HISTORY_ROUNDS * 2:]
    messages.append({"role": "user", "content": message})

    try:
        stream = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            stream=True,
        )
        reply = ""
        for chunk in stream:
            # 流式增量可能为空（如最后的 usage 块），跳过即可
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                reply += chunk.choices[0].delta.content
                yield reply
    except Exception as e:
        yield f"❌ 调用 {DEEPSEEK_MODEL} 出错: {e}"


# ==========================================
# 4. Web 界面（自然语言即界面：聊天框 + 流式输出）
# ==========================================

def run_web():
    import gradio as gr

    prompt_line_count = SYSTEM_PROMPT.count("\n") + 1
    print(f"📝 已加载系统提示词（共 {prompt_line_count} 行）")

    with gr.Blocks(title="🤖 个人助手") as demo:
        gr.ChatInterface(
            fn=respond,
            chatbot=gr.Chatbot(height=520),
            textbox=gr.Textbox(placeholder="随便聊点什么...", lines=1),
            title="🤖 个人助手 Personal Assistant",
            description="本地个人助手：多轮对话、流式输出，背后由大模型驱动。",
        )

    # 仅本地监听；端口可用 WEB_PORT 覆盖
    server_port = int(os.getenv("WEB_PORT", "7867"))
    demo.launch(server_name="127.0.0.1", server_port=server_port)


# ==========================================
# 5. 启动
# ==========================================
if __name__ == "__main__":
    run_web()
