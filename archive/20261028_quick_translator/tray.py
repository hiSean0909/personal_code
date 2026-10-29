"""Native system tray integration, dispatched by Tk's Windows message loop."""

import ctypes
from ctypes import wintypes
import os

from windows import signature, user32, kernel32


shell32 = ctypes.WinDLL("shell32", use_last_error=True)
LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
TRAY_MESSAGE = 0x8001


class WNDCLASS(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]


class NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT), ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128), ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD), ("szInfo", wintypes.WCHAR * 256),
                ("uVersion", wintypes.UINT), ("szInfoTitle", wintypes.WCHAR * 64),
                ("dwInfoFlags", wintypes.DWORD), ("guidItem", wintypes.DWORD * 4),
                ("hBalloonIcon", wintypes.HICON)]


signature(kernel32, "GetModuleHandleW", [wintypes.LPCWSTR], wintypes.HMODULE)
signature(user32, "RegisterClassW", [ctypes.POINTER(WNDCLASS)], wintypes.ATOM)
signature(user32, "UnregisterClassW", [wintypes.LPCWSTR, wintypes.HINSTANCE], wintypes.BOOL)
signature(user32, "CreateWindowExW", [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
          wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
          wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p], wintypes.HWND)
signature(user32, "DefWindowProcW", [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM], LRESULT)
signature(user32, "DestroyWindow", [wintypes.HWND], wintypes.BOOL)
signature(user32, "LoadIconW", [wintypes.HINSTANCE, ctypes.c_void_p], wintypes.HICON)
signature(user32, "RegisterWindowMessageW", [wintypes.LPCWSTR], wintypes.UINT)
signature(user32, "CreatePopupMenu", [], wintypes.HMENU)
signature(user32, "AppendMenuW", [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR], wintypes.BOOL)
signature(user32, "DestroyMenu", [wintypes.HMENU], wintypes.BOOL)
signature(user32, "GetCursorPos", [ctypes.POINTER(wintypes.POINT)], wintypes.BOOL)
signature(user32, "SetForegroundWindow", [wintypes.HWND], wintypes.BOOL)
signature(user32, "TrackPopupMenu", [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int,
          ctypes.c_int, wintypes.HWND, ctypes.c_void_p], wintypes.UINT)
signature(user32, "PostMessageW", [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM], wintypes.BOOL)
signature(shell32, "Shell_NotifyIconW", [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATA)], wintypes.BOOL)


class TrayIcon:
    def __init__(self, events):
        self.events = events
        self.hwnd = None
        self.added = False
        self.registered = False
        self.instance = kernel32.GetModuleHandleW(None)
        self.class_name = f"QuickTranslatorTray_{os.getpid()}_{id(self)}"
        self.taskbar_created = user32.RegisterWindowMessageW("TaskbarCreated")
        self.callback = WNDPROC(self.window_proc)
        window_class = WNDCLASS()
        window_class.lpfnWndProc = self.callback
        window_class.hInstance = self.instance
        window_class.lpszClassName = self.class_name
        if not user32.RegisterClassW(ctypes.byref(window_class)):
            raise RuntimeError("无法初始化托盘图标，请重新启动软件。")
        self.registered = True
        try:
            # A hidden top-level window also receives Explorer's TaskbarCreated broadcast.
            self.hwnd = user32.CreateWindowExW(0, self.class_name, "Quick Translator", 0,
                                              0, 0, 0, 0, None, None, self.instance, None)
            if not self.hwnd:
                raise RuntimeError("无法创建托盘窗口，请重新启动软件。")
            self.data = NOTIFYICONDATA()
            self.data.cbSize = ctypes.sizeof(self.data)
            self.data.hWnd = self.hwnd
            self.data.uID = 1
            self.data.uFlags = 0x87  # callback, shared icon, tooltip, version-4 tooltip
            self.data.uCallbackMessage = TRAY_MESSAGE
            self.data.hIcon = user32.LoadIconW(None, 32512)
            self.data.szTip = "快捷翻译 · 双击打开主界面"
            self.add()
        except Exception:
            self.close()
            raise

    def add(self):
        if not shell32.Shell_NotifyIconW(0, ctypes.byref(self.data)):
            raise RuntimeError("无法创建托盘图标，主界面将保持可见。")
        self.added = True
        self.data.uVersion = 4
        shell32.Shell_NotifyIconW(4, ctypes.byref(self.data))

    def ensure_visible(self):
        # Refresh the existing entry, or recreate it if Explorer discarded it.
        if not self.added or not shell32.Shell_NotifyIconW(1, ctypes.byref(self.data)):
            self.added = False
            self.add()

    def window_proc(self, hwnd, message, wparam, lparam):
        try:
            if message == TRAY_MESSAGE:
                action = lparam & 0xFFFF
                if action in (0x0203, 0x0401):  # double-click or keyboard activation
                    self.events.put(("tray_open",))
                elif action in (0x007B, 0x0205):  # context menu or legacy right-button release
                    self.show_menu()
                return 0
            if self.taskbar_created and message == self.taskbar_created:
                self.added = False
                self.add()
                return 0
        except Exception:
            self.events.put(("tray_error", "托盘图标暂时不可用，已恢复主界面。"))
            return 0
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    def show_menu(self):
        menu = user32.CreatePopupMenu()
        if not menu:
            self.events.put(("tray_open",))
            return
        try:
            user32.AppendMenuW(menu, 0, 1, "打开主界面")
            user32.AppendMenuW(menu, 0, 2, "退出")
            point = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(point))
            user32.SetForegroundWindow(self.hwnd)
            command = user32.TrackPopupMenu(menu, 0x0102, point.x, point.y, 0, self.hwnd, None)
            user32.PostMessageW(self.hwnd, 0, 0, 0)
            if command in (1, 2):
                self.events.put(("tray_open" if command == 1 else "tray_exit",))
        finally:
            user32.DestroyMenu(menu)

    def close(self):
        if self.added:
            shell32.Shell_NotifyIconW(2, ctypes.byref(self.data))
            self.added = False
        if self.hwnd:
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None
        if self.registered:
            user32.UnregisterClassW(self.class_name, self.instance)
            self.registered = False
