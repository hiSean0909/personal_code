import json
from openai import OpenAI

# ==========================================
# 1. 配置与初始化
# ==========================================
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)
MODEL_NAME = "qwen2.5:7b"

# ==========================================
# 2. 定义本地工具函数
# ==========================================
def get_weather(city: str) -> str:
    """获取指定城市的实时天气情况"""
    return f"{city}目前的天气是晴天，气温25度，微风。"

def calculate(expression: str) -> str:
    """计算数学表达式，例如 '12 * 8 + 5'"""
    try:
        # 使用 eval 进行计算（注意：在生产环境中应使用更安全的库如 simpleeval）
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算出错: {str(e)}"

TOOLS_MAP = {
    "get_weather": get_weather,
    "calculate": calculate
}

# ==========================================
# 3. 定义工具的“说明书”
# ==========================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，例如：北京"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "用于执行数学运算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "需要计算的数学表达式字符串"}
                },
                "required": ["expression"]
            }
        }
    }
]

# ==========================================
# 4. 优化的 System Prompt (关键修改)
# ==========================================
SYSTEM_PROMPT = """你是一个智能助手。你可以使用工具来回答问题。
重要规则：
1. 如果用户的问题包含多个任务（例如既问天气又问数学），请**一次只调用一个工具**。
2. 先解决第一个任务，等拿到结果后，再思考下一个任务。
3. 不要编造数据，不要直接回答需要工具才能知道的信息。
4. 始终保持冷静，按步骤执行。
"""

# ==========================================
# 5. 核心循环
# ==========================================
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print("🤖 Agent 已启动！输入 'exit' 退出。")

while True:
    user_input = input("\n👤 用户: ")
    if user_input.lower() == 'exit':
        break

    messages.append({"role": "user", "content": user_input})

    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools
            )
            msg = response.choices[0].message

            # 情况 A: 模型决定调用工具
            if msg.tool_calls:
                messages.append(msg)  # 记录模型的请求

                for tool_call in msg.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    print(f"\n🛠️ [系统] 正在执行: {func_name}, 参数: {func_args}")

                    # 执行真正的 Python 函数
                    if func_name in TOOLS_MAP:
                        result = TOOLS_MAP[func_name](**func_args)
                    else:
                        result = "错误：找不到该工具"

                    print(f"👀 [观察] 工具返回结果: {result}")

                    # 将工具的结果反馈给模型
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": result
                    })

            # 情况 B: 模型给出了最终回答
            else:
                print(f"\n🤖 [AI 最终回答]: {msg.content}")
                messages.append(msg)  # 记录回答到历史
                break  # 跳出内部循环，等待用户下一次输入

        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            break