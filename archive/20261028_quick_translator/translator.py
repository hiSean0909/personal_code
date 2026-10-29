"""Configuration and the existing Gradio translation protocol."""

import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit


DEFAULT_URL = "http://122.51.135.229:7861"
DEFAULT_HOTKEY = "Ctrl+Alt+T"
SETTINGS_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "QuickTranslator" / "settings.json"
MODIFIERS = {"Ctrl": 0x0002, "Alt": 0x0001, "Shift": 0x0004}
KEYS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + [f"F{i}" for i in range(1, 12)]


def parse_hotkey(value):
    parts = value.split("+")
    modifiers, key = parts[:-1], parts[-1]
    if (not modifiers or len(set(modifiers)) != len(modifiers)
            or any(part not in MODIFIERS for part in modifiers) or key not in KEYS):
        raise ValueError("请选择 Ctrl、Alt、Shift 中至少一个修饰键，以及字母、数字或 F1–F11。")
    if modifiers == ["Ctrl"] and key == "C":
        raise ValueError("Ctrl+C 用于获取选中文本，请选择其他快捷键。")
    mask = sum(MODIFIERS[part] for part in modifiers)
    vk = 0x70 + int(key[1:]) - 1 if key.startswith("F") and len(key) > 1 else ord(key)
    return mask, vk


def validate_url(value):
    value = value.strip().rstrip("/")
    try:
        parsed = urlsplit(value)
        parsed.port  # Validate the port as well as the hostname.
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or any(c.isspace() for c in value)):
            raise ValueError
    except ValueError:
        raise ValueError("请输入完整的 http:// 或 https:// Gradio 服务地址，不含账号、查询参数或片段。") from None
    return value


def load_settings(path=SETTINGS_PATH):
    if not path.exists():
        return {"hotkey": DEFAULT_HOTKEY, "url": DEFAULT_URL}
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
        parse_hotkey(settings["hotkey"])
        return {"hotkey": settings["hotkey"], "url": validate_url(settings["url"])}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise ValueError("无法读取设置文件。已显示默认值，请检查并重新保存。") from None


def save_settings(settings, path=SETTINGS_PATH):
    parse_hotkey(settings["hotkey"])
    data = {"hotkey": settings["hotkey"], "url": validate_url(settings["url"])}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def translate(text, url, client_factory=None, stop=None):
    text = text.strip()
    if not text:
        raise ValueError("未获取到选中文本，请选中文字后重试。")
    url = validate_url(url)
    if client_factory is None:
        from gradio_client import Client
        client_factory = Client
    client = None
    job = None
    try:
        # A fresh client/session keeps requests independent of prior translations.
        client = client_factory(url, verbose=False, httpx_kwargs={"timeout": 20.0},
                                analytics_enabled=False, download_files=False, max_workers=1)
        if stop is not None and stop.is_set():
            raise RuntimeError("已退出快捷翻译。")
        job = client.submit(message=text, api_name="/translate")
        deadline = time.monotonic() + 120
        while True:
            if stop is not None and stop.is_set():
                job.cancel()
                raise RuntimeError("已退出快捷翻译。")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            try:
                result = job.result(timeout=min(0.2, remaining))
                break
            except TimeoutError:
                continue
        if not isinstance(result, str) or not result.strip():
            raise RuntimeError("翻译服务返回了空内容或不支持的结果格式。")
        return result
    except TimeoutError:
        if job is not None:
            try:
                job.cancel()
            except Exception:
                pass
        raise RuntimeError("翻译请求超时，请稍后重试。") from None
    except Exception:
        raise RuntimeError("翻译失败，请检查服务地址、网络和远程翻译服务状态。") from None
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
