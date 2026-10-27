"""A minimal local Web/CLI translator using the reference project's prompt."""

import argparse
from pathlib import Path

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI, OpenAIError


PROJECT_DIR = Path(__file__).resolve().parent
CREDENTIAL_FILE = Path(r"D:\personal\codex\.secrets\llm.env")


def create_translator():
    config = dotenv_values(CREDENTIAL_FILE)
    provider = config.get("LLM_DEFAULT")
    if not provider:
        raise RuntimeError(f"请在 {CREDENTIAL_FILE} 中配置 LLM_DEFAULT。")
    keys = {name: f"{provider}_{name}" for name in ("API_KEY", "BASE_URL", "DEFAULT_MODEL")}
    missing = [key for key in keys.values() if not config.get(key)]
    if missing:
        raise RuntimeError(f"请在 {CREDENTIAL_FILE} 中配置：{', '.join(missing)}。")

    client = OpenAI(
        api_key=config[keys["API_KEY"]],
        base_url=config[keys["BASE_URL"]],
        timeout=120,
        max_retries=0,
    )
    model = config[keys["DEFAULT_MODEL"]]
    prompt = (PROJECT_DIR / "translator_agent_prompts.md").read_text(encoding="utf-8").strip()

    def translate(message, history=None):
        text = message.strip()
        if not text:
            return "请输入英文单词、短语、中文词语或句子。"
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
            )
            return response.choices[0].message.content or "模型返回了空内容，请重试。"
        except AuthenticationError:
            return f"API 授权失败，请检查集中凭据文件中的 {keys['API_KEY']}。"
        except APIConnectionError:
            return "连接模型服务失败或请求超时，请检查网络后重试。"
        except APIStatusError as error:
            return f"模型服务请求失败（HTTP {error.status_code}），请稍后重试。"
        except OpenAIError:
            return "模型服务响应异常，请稍后重试。"

    return translate


def main():
    parser = argparse.ArgumentParser(description="本地中英翻译助手")
    parser.add_argument("--cli", action="store_true", help="在命令行中交互，默认启动 Web 界面")
    args = parser.parse_args()
    try:
        translate = create_translator()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None

    if args.cli:
        print("翻译助手已启动。输入 exit 退出。")
        try:
            while True:
                text = input("\n你：")
                if text.strip().lower() == "exit":
                    break
                print(translate(text))
        except (EOFError, KeyboardInterrupt):
            print()
    else:
        import gradio as gr

        gr.ChatInterface(
            fn=translate,
            title="翻译助手 · Local Translator",
            description="输入英文单词、短语、中文词语或句子。每次独立解析，不携带历史对话。",
            textbox=gr.Textbox(placeholder="输入需要翻译或解析的内容…", lines=1),
            analytics_enabled=False,
        ).launch(server_name="127.0.0.1", server_port=7860, share=False)


if __name__ == "__main__":
    main()
