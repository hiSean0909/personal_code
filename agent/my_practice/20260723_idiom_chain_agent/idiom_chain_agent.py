import os
import re
import time
from openai import OpenAI
from pypinyin import pinyin, Style

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 匹配连续汉字（2-12字）
RE_IDIOM = re.compile(r'[\u4e00-\u9fff]{2,12}')

DEFAULT_PROMPT = (
    "你是成语接龙助手。广义成语包括四字成语、歇后语、俗语、惯用语等，不限字数。"
    "用玩家成语最后一个字的读音开头接龙，平舌卷舌、前后鼻音、声调不同均可。"
    "只回复成语本身，不要其他内容。"
    "非常重要：不要轻易认输！放宽思路，任何读音相近的常用表达都可以。"
    "只有确实找不到时才回复'认输'。"
)


# ==========================================
# 1. 拼音工具
# ==========================================

def get_pinyin(char: str) -> str:
    """获取单个汉字的拼音（不带声调）。"""
    result = pinyin(char, style=Style.NORMAL)
    return result[0][0] if result and result[0] else ""


def normalize_pinyin(py: str) -> str:
    """
    标准化拼音，用于宽松匹配：
    - 卷舌音 zh/ch/sh → 平舌音 z/c/s
    - 后鼻音 ang/eng/ing → 前鼻音 an/en/in
    """
    py = py.lower()
    for zh, z in [("zh", "z"), ("ch", "c"), ("sh", "s")]:
        if py.startswith(zh):
            py = z + py[2:]
            break
    for hou, qian in [("ang", "an"), ("eng", "en"), ("ing", "in")]:
        if py.endswith(hou):
            py = py[:-3] + qian
            break
    return py


def chars_match(char_a: str, char_b: str) -> bool:
    """判断两个汉字是否读音相近（宽松匹配）。"""
    if char_a == char_b:
        return True
    return normalize_pinyin(get_pinyin(char_a)) == normalize_pinyin(get_pinyin(char_b))


# ==========================================
# 2. 配置
# ==========================================

RUN_MODE = os.getenv("RUN_MODE", "").upper()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def init_client():
    """初始化并验证 DeepSeek 连接。"""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            "未设置 DEEPSEEK_API_KEY 环境变量。\n"
            "  - 本地开发：$env:DEEPSEEK_API_KEY='sk-xxx'\n"
            "  - Docker：在 .env 文件里填 DEEPSEEK_API_KEY=sk-xxx"
        )
    print("🔄 正在测试 DeepSeek 连接...")
    try:
        c = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=DEEPSEEK_API_KEY, timeout=15)
        c.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
            timeout=15,
        )
    except Exception as e:
        raise RuntimeError(f"DeepSeek 连接失败: {e}") from e
    print(f"✅ DeepSeek 连接成功，模型: {DEEPSEEK_MODEL}")
    return c


def load_prompt(file_path="idiom_chain_prompts.md") -> str:
    """从文件读取系统提示词。"""
    full_path = os.path.join(SCRIPT_DIR, file_path)
    if not os.path.exists(full_path):
        return DEFAULT_PROMPT
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read().strip()


# ==========================================
# 3. 游戏状态
# ==========================================

class IdiomGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.history = []       # [(玩家成语, AI成语), ...]
        self.used = set()       # 已用过的成语集合
        self.score = 0          # 连续接龙次数
        self.game_over = False

    def get_last_char(self):
        """获取 AI 最后一个成语的最后一个字。"""
        if not self.history:
            return None
        last_idiom = self.history[-1][1]
        return last_idiom[-1] if last_idiom else None

    def add_round(self, player_idiom, ai_idiom):
        self.history.append((player_idiom, ai_idiom))
        self.used.add(player_idiom)
        self.used.add(ai_idiom)
        self.score += 1


# ==========================================
# 4. AI 接龙
# ==========================================

def _call_ai(client, model: str, system_prompt: str, user_msg: str) -> str:
    """调用 AI 并返回回复文本，失败返回空字符串。"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=80,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except Exception as e:
        print(f"❌ AI 调用出错: {e}")
        return ""


def _build_user_msg(last_char: str, used_list: str, attempt: int) -> str:
    """构建发给 AI 的用户消息，attempt 越大语气越鼓励。"""
    last_py = get_pinyin(last_char)
    base = (
        f"请用读音为「{last_py}」的字开头（平舌卷舌、前后鼻音、声调不同均可），"
        f"给出一个成语或常用短语。\n"
        f"已用过的（不能重复）：{used_list}"
    )
    if attempt >= 2:
        base += "\n⚠️ 千万不要认输！放宽思路，俗语、歇后语、常见搭配、四字词语都可以，一定要接上！"
    if attempt >= 4:
        base += "\n🔥 这是最后机会！任何读音相近的常用表达都可以，请务必给出一个答案！"
    return base


def _extract_idiom(reply: str, last_char: str) -> str:
    """从 AI 回复中提取首字匹配的成语，失败返回空字符串。"""
    if not reply or "认输" in reply:
        return ""
    for match in RE_IDIOM.finditer(reply):
        idiom = match.group()
        if chars_match(idiom[0], last_char):
            return idiom
    return ""


MAX_RETRIES = 5
RETRY_DELAY = 3  # 重试间隔（秒），避免 API 限流返回空字符串
INITIAL_DELAY = 5  # 首次调用前等待时间（秒），让 API 预热


def get_ai_response(game: IdiomGame, last_char: str, client, model: str, system_prompt: str) -> str:
    """让 AI 用 last_char 读音相近的字开头的成语/短语接龙，最多重试 MAX_RETRIES 次。"""
    used_list = "、".join(game.used) if game.used else "无"

    # 首次调用前等待，让 API 预热
    time.sleep(INITIAL_DELAY)

    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            time.sleep(RETRY_DELAY)
        reply = _call_ai(client, model, system_prompt, _build_user_msg(last_char, used_list, attempt))
        if attempt == 1:
            print(f"🤖 AI 回复: '{reply}'")
        else:
            print(f"🤖 AI 第{attempt}次重试: '{reply}'")

        idiom = _extract_idiom(reply, last_char)
        if idiom:
            return idiom

    print(f"⚠️ {MAX_RETRIES}次尝试均未匹配，AI 认输")
    return "认输"


# ==========================================
# 5. Web 界面
# ==========================================

def run_web():
    import gradio as gr

    # 初始化（避免模块级副作用）
    client = init_client()
    system_prompt = load_prompt()
    game = IdiomGame()

    with gr.Blocks(title="🀄 成语接龙") as demo:
        gr.Markdown("# 🀄 成语接龙\n输入成语、歇后语、俗语等，AI 用最后一个字的读音接龙（平舌卷舌、前后鼻音均可），看你能坚持几轮！")

        chat_display = gr.Chatbot(label="对局记录", height=400)

        with gr.Row():
            score_display = gr.Markdown("**得分：0**")
            hint_display = gr.Markdown("")

        with gr.Row():
            user_input = gr.Textbox(label="输入成语", placeholder="例如：一心一意", scale=4)
            submit_btn = gr.Button("接龙", variant="primary", scale=1)

        with gr.Row():
            restart_btn = gr.Button("🔄 重新开始")
            give_up_btn = gr.Button("🏳️ 认输")

        # ---- 事件处理 ----

        def handle_submit(user_idiom, chat_history):
            user_idiom = user_idiom.strip()

            if not user_idiom:
                return "", chat_history, f"**得分：{game.score}**", "️ 请输入成语"

            if game.game_over:
                return "", chat_history, f"**得分：{game.score}**", "⚠️ 游戏已结束，请重新开始"

            if len(user_idiom) < 4:
                return "", chat_history, f"**得分：{game.score}**", "️ 至少输入4个字（成语、俗语、歇后语等）"

            if user_idiom in game.used:
                return "", chat_history, f"**得分：{game.score}**", f"⚠️ 「{user_idiom}」已经用过了"

            if game.history:
                last_char = game.get_last_char()
                if not chars_match(user_idiom[0], last_char):
                    last_py = get_pinyin(last_char)
                    return "", chat_history, f"**得分：{game.score}**", f"⚠️ 必须以读音相近的字开头（参考：「{last_char}」{last_py}）"

            ai_idiom = get_ai_response(game, user_idiom[-1], client, DEEPSEEK_MODEL, system_prompt)
            game.add_round(user_idiom, ai_idiom)

            chat_history = chat_history or []
            chat_history.append({"role": "user", "content": user_idiom})
            chat_history.append({"role": "assistant", "content": ai_idiom})

            if ai_idiom == "认输":
                game.game_over = True
                hint = f"🎉 AI 认输！你赢了！最终得分：{game.score}"
            else:
                last_py = get_pinyin(ai_idiom[-1])
                hint = f"✅ 成功！请接读音为「{last_py}」的字（平舌卷舌、前后鼻音均可）"

            return "", chat_history, f"**得分：{game.score}**", hint

        def handle_restart():
            game.reset()
            return None, "**得分：0**", "🎮 新游戏开始！请输入一个成语"

        def handle_give_up():
            if game.game_over:
                return None, f"**得分：{game.score}**", "游戏已结束"
            game.game_over = True
            return None, f"**得分：{game.score}**", f"🏳️ 你认输了！最终得分：{game.score}"

        submit_btn.click(
            fn=handle_submit,
            inputs=[user_input, chat_display],
            outputs=[user_input, chat_display, score_display, hint_display],
        )
        user_input.submit(
            fn=handle_submit,
            inputs=[user_input, chat_display],
            outputs=[user_input, chat_display, score_display, hint_display],
        )
        restart_btn.click(fn=handle_restart, outputs=[chat_display, score_display, hint_display])
        give_up_btn.click(fn=handle_give_up, outputs=[chat_display, score_display, hint_display])

    # 端口配置
    default_port = "7860" if RUN_MODE else "7864"
    server_name = os.getenv("WEB_HOST", "0.0.0.0" if RUN_MODE else "127.0.0.1")
    server_port = int(os.getenv("WEB_PORT", default_port))

    prompt_lines = system_prompt.count("\n") + 1
    print(f"📝 已加载提示词（{prompt_lines} 行）")
    print(f"🤖 模型：{DEEPSEEK_MODEL}")

    demo.launch(server_name=server_name, server_port=server_port, theme=gr.themes.Soft())


# ==========================================
# 6. 启动
# ==========================================
if __name__ == "__main__":
    run_web()
