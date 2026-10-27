# Local Translator

A minimal local reproduction of `20260626_translator_agent`, reusing its original translation prompt.

## Features

- English words: Chinese meaning, American pronunciation, etymology, meaning evolution, and related vocabulary
- English phrases and sentences: Chinese translation and context
- Chinese words: natural American English equivalents and usage guidance
- Chinese sentences and paragraphs: English translation and translation strategy
- A local Gradio web interface and a command-line interface
- Independent requests: conversation history is displayed in the web interface but is not sent to the model

The application runs locally and sends translation requests to the provider selected by `LLM_DEFAULT`. An internet connection, an OpenAI-compatible Chat Completions API, and a valid API key are required.

## Setup

Open PowerShell in this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The application reads configuration exclusively from `D:\personal\codex\.secrets\llm.env`:

- `LLM_DEFAULT`: required provider identifier, matching its uppercase variable prefix
- `<PROVIDER>_API_KEY`: required API authentication key
- `<PROVIDER>_BASE_URL`: required API endpoint
- `<PROVIDER>_DEFAULT_MODEL`: required model name

For example, `LLM_DEFAULT=DEEPSEEK` selects `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, and `DEEPSEEK_DEFAULT_MODEL`. Missing settings are reported by variable name. Restart the application after changing configuration.

Use the centralized credential file to manage credentials.

## Run

Start the web interface:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:7860>. Press `Ctrl+C` in the terminal to stop the server.

Start command-line mode:

```powershell
.\.venv\Scripts\python.exe app.py --cli
```

Enter one input per line. Enter `exit` to quit CLI mode. In web mode, `exit` is treated as translation input, following the prompt.

## Files

| File | Purpose |
|---|---|
| `app.py` | Shared translation function and local Web/CLI entry points |
| `translator_agent_prompts.md` | Original prompt copied from the reference project |
| `requirements.txt` | Python dependencies |

Errors are shown as brief messages without displaying credentials or raw API responses. Blank input is rejected before making an API request.
