"""Small Win32 bridge: registered shortcuts, Unicode clipboard, and Ctrl+C."""

import ctypes
from ctypes import wintypes
from queue import Empty, Queue
import threading
import time

from translator import parse_hotkey


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ULONG_PTR = ctypes.c_size_t
CF_UNICODETEXT = 13
WM_HOTKEY = 0x0312
HOTKEY_ID = 1


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", wintypes.DWORD), ("data", INPUT_UNION)]


def signature(dll, name, args, result):
    function = getattr(dll, name)
    function.argtypes = args
    function.restype = result
    return function


signature(user32, "RegisterHotKey", [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT], wintypes.BOOL)
signature(user32, "UnregisterHotKey", [wintypes.HWND, ctypes.c_int], wintypes.BOOL)
signature(user32, "PeekMessageW", [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT], wintypes.BOOL)
signature(user32, "GetForegroundWindow", [], wintypes.HWND)
signature(user32, "GetAsyncKeyState", [ctypes.c_int], wintypes.SHORT)
signature(user32, "SendInput", [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int], wintypes.UINT)
signature(user32, "GetClipboardSequenceNumber", [], wintypes.DWORD)
signature(user32, "OpenClipboard", [wintypes.HWND], wintypes.BOOL)
signature(user32, "CloseClipboard", [], wintypes.BOOL)
signature(user32, "IsClipboardFormatAvailable", [wintypes.UINT], wintypes.BOOL)
signature(user32, "GetClipboardData", [wintypes.UINT], wintypes.HANDLE)
signature(user32, "EmptyClipboard", [], wintypes.BOOL)
signature(user32, "SetClipboardData", [wintypes.UINT, wintypes.HANDLE], wintypes.HANDLE)
signature(kernel32, "GlobalLock", [wintypes.HGLOBAL], ctypes.c_void_p)
signature(kernel32, "GlobalUnlock", [wintypes.HGLOBAL], wintypes.BOOL)
signature(kernel32, "GlobalAlloc", [wintypes.UINT, ctypes.c_size_t], wintypes.HGLOBAL)
signature(kernel32, "GlobalFree", [wintypes.HGLOBAL], wintypes.HGLOBAL)


class HotkeyListener:
    def __init__(self, events):
        self.events = events
        self.commands = Queue()
        self.stopping = threading.Event()
        self.current = None
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def configure(self, value, callback):
        parse_hotkey(value)
        self.commands.put((value, callback))

    def run(self):
        message = wintypes.MSG()
        try:
            while not self.stopping.is_set():
                try:
                    value, callback = self.commands.get_nowait()
                except Empty:
                    pass
                else:
                    old = self.current
                    if value == old:
                        self.events.put(("configured", callback, None))
                    else:
                        if old:
                            user32.UnregisterHotKey(None, HOTKEY_ID)
                        modifiers, key = parse_hotkey(value)
                        if user32.RegisterHotKey(None, HOTKEY_ID, modifiers | 0x4000, key):
                            self.current = value
                            error = None
                        else:
                            self.current = None
                            error = "快捷键注册失败，可能已被其他应用占用，请选择其他组合。"
                            if old:
                                modifiers, key = parse_hotkey(old)
                                if user32.RegisterHotKey(None, HOTKEY_ID, modifiers | 0x4000, key):
                                    self.current = old
                                else:
                                    error += " 原快捷键也无法恢复，请重新保存设置。"
                        self.events.put(("configured", callback, error))
                while user32.PeekMessageW(ctypes.byref(message), None, WM_HOTKEY, WM_HOTKEY, 1):
                    if message.wParam == HOTKEY_ID:
                        self.events.put(("hotkey", user32.GetForegroundWindow()))
                self.stopping.wait(0.015)
        finally:
            if self.current:
                user32.UnregisterHotKey(None, HOTKEY_ID)

    def close(self):
        self.stopping.set()
        self.thread.join(timeout=2)


def open_clipboard(owner=None):
    deadline = time.monotonic() + 0.5
    while not user32.OpenClipboard(owner):
        if time.monotonic() >= deadline:
            raise RuntimeError("剪贴板正被其他程序占用，请稍后重试。")
        time.sleep(0.01)


def read_clipboard():
    # Caller holds the clipboard open.
    if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
        return None
    handle = user32.GetClipboardData(CF_UNICODETEXT)
    pointer = kernel32.GlobalLock(handle) if handle else None
    if not pointer:
        raise RuntimeError("无法读取剪贴板文本，请重试。")
    try:
        return ctypes.wstring_at(pointer)
    finally:
        kernel32.GlobalUnlock(handle)


def restore_clipboard(text, sequence, owner):
    open_clipboard(owner)
    try:
        if user32.GetClipboardSequenceNumber() != sequence:
            return
        raw = (text + "\0").encode("utf-16-le")
        handle = kernel32.GlobalAlloc(0x0002, len(raw))
        if not handle:
            raise RuntimeError("无法恢复原剪贴板文本。")
        transferred = False
        try:
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                raise RuntimeError("无法恢复原剪贴板文本。")
            try:
                ctypes.memmove(pointer, raw, len(raw))
            finally:
                kernel32.GlobalUnlock(handle)
            if not user32.EmptyClipboard() or not user32.SetClipboardData(CF_UNICODETEXT, handle):
                raise RuntimeError("无法恢复原剪贴板文本。")
            transferred = True
        finally:
            if not transferred:
                kernel32.GlobalFree(handle)
    finally:
        user32.CloseClipboard()


def send_copy():
    inputs = (INPUT * 4)()
    for event, vk, flags in zip(inputs, (0x11, 0x43, 0x43, 0x11), (0, 0, 2, 2)):
        event.type = 1
        event.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
    if user32.SendInput(4, inputs, ctypes.sizeof(INPUT)) != 4:
        # Release synthetic keys even when only a prefix was injected.
        release = (INPUT * 2)()
        for event, vk in zip(release, (0x43, 0x11)):
            event.type = 1
            event.ki = KEYBDINPUT(vk, 0, 2, 0, 0)
        user32.SendInput(2, release, ctypes.sizeof(INPUT))
        raise RuntimeError("无法复制选中文本，请在普通权限窗口中重试。")


def capture_selection(foreground, owner):
    deadline = time.monotonic() + 2
    while any(user32.GetAsyncKeyState(key) & 0x8000 for key in (0x10, 0x11, 0x12, 0x5B, 0x5C)):
        if time.monotonic() >= deadline:
            raise RuntimeError("请释放快捷键后重试。")
        time.sleep(0.01)
    if not foreground or user32.GetForegroundWindow() != foreground:
        raise RuntimeError("当前窗口已改变，请重新选中文字并按快捷键。")
    open_clipboard(owner)
    try:
        previous = read_clipboard()
        before = user32.GetClipboardSequenceNumber()
    finally:
        user32.CloseClipboard()
    if user32.GetForegroundWindow() != foreground:
        raise RuntimeError("当前窗口已改变，请重新选中文字并按快捷键。")
    send_copy()
    deadline = time.monotonic() + 1.5
    while user32.GetClipboardSequenceNumber() == before:
        if time.monotonic() >= deadline:
            raise RuntimeError("未获取到新文本，请选中可复制的文字后重试。")
        time.sleep(0.01)
    open_clipboard(owner)
    try:
        selected = read_clipboard()
        captured_sequence = user32.GetClipboardSequenceNumber()
    finally:
        user32.CloseClipboard()
    if previous is not None:
        try:
            restore_clipboard(previous, captured_sequence, owner)
        except RuntimeError:
            # Translation remains useful if a competing clipboard owner prevents restoration.
            pass
    if not selected or not selected.strip():
        raise RuntimeError("未获取到选中文本，请选中可复制的文字后重试。")
    return selected.strip()


def show_without_activation(window, x, y):
    """Show a Tk notification without taking the selected application's focus."""
    signature(user32, "GetAncestor", [wintypes.HWND, wintypes.UINT], wintypes.HWND)
    signature(user32, "ShowWindow", [wintypes.HWND, ctypes.c_int], wintypes.BOOL)
    signature(user32, "SetWindowPos", [wintypes.HWND, wintypes.HWND, ctypes.c_int,
              ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT], wintypes.BOOL)
    hwnd = user32.GetAncestor(window.winfo_id(), 2)
    user32.SetWindowPos(hwnd, -1, x, y,
                        window.winfo_reqwidth(), window.winfo_reqheight(), 0x0010)
    user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
