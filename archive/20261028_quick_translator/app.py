"""Native selected-text translation client. Run with pythonw.exe on Windows."""

import argparse
from collections import deque
import os
from queue import Empty, Queue
import sqlite3
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from translator import (DEFAULT_HOTKEY, DEFAULT_URL, KEYS, MODIFIERS,
                        load_settings, parse_hotkey, save_settings, translate, validate_url)
from history import HistoryStore, STATUS_LABELS
from markdown_view import MarkdownText


STATUS_ICONS = {"pending": "⌛", "completed": "✓", "failed": "✕"}
STATUS_COLUMN_WIDTH = 56


def directory_title(original):
    title = " ".join(original.split())
    return title if len(title) <= 20 else title[:19] + "…"


class Application:
    def __init__(self, root, history=None, background=False):
        from windows import HotkeyListener

        self.root = root
        self.events = Queue()
        self.busy = False
        self.capturing = False
        self.pending = deque()
        self.latest = {}
        self.sequence = 0
        self.toast = None
        self.toast_timer = None
        self.saving = False
        self.closing = False
        self.stop = threading.Event()
        self.history_epoch = 0
        self.tray = None
        self.settings_window = None
        self.settings = {"hotkey": DEFAULT_HOTKEY, "url": DEFAULT_URL}
        warning = None
        try:
            self.settings = load_settings()
        except ValueError as error:
            warning = str(error)
        self.history = history if history is not None else HistoryStore()
        self.listener = HotkeyListener(self.events)
        root.title("快捷翻译")
        root.geometry("1000x700")
        root.minsize(820, 520)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        toolbar = ttk.Frame(root, padding=10)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)
        ttk.Label(toolbar, text="快捷键取词，后台翻译并保存").grid(row=0, column=0, sticky="w")
        ttk.Button(toolbar, text="设置", command=self.open_settings).grid(row=0, column=1, padx=6)
        ttk.Button(toolbar, text="最小化到托盘", command=self.minimize_to_tray).grid(row=0, column=2, padx=6)
        ttk.Button(toolbar, text="退出", command=self.close).grid(row=0, column=3)
        self.build_records_view()
        self.status = tk.StringVar(value="正在注册快捷键…")
        ttk.Label(root, textvariable=self.status, wraplength=790, padding=10).grid(row=2, column=0, sticky="ew")
        self.refresh_records()
        self.owner = root.winfo_id()
        root.bind("<Unmap>", self.on_unmap, add="+")
        try:
            from tray import TrayIcon
            self.tray = TrayIcon(self.events)
        except RuntimeError as error:
            warning = str(error) if warning is None else f"{warning}\n{error}"
            if background:
                self.restore_settings()
        self.listener.configure(self.settings["hotkey"], self.initialized)
        root.after(40, self.poll)
        if warning:
            if background:
                self.status.set(warning)
            else:
                root.after(100, lambda: messagebox.showwarning("设置", warning, parent=root))

    def open_settings(self):
        if self.settings_window is not None:
            self.settings_window.deiconify()
            self.settings_window.lift()
            return
        window = tk.Toplevel(self.root)
        self.settings_window = window
        window.title("快捷翻译 · 设置")
        window.geometry("620x330")
        window.minsize(580, 330)
        window.transient(self.root)
        window.protocol("WM_DELETE_WINDOW", window.withdraw)
        window.columnconfigure(0, weight=1)
        frame = ttk.Frame(window, padding=20)
        frame.grid(sticky="nsew")
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="设置取词快捷键与远程翻译服务", font=("Microsoft YaHei UI", 12)).grid(sticky="w", pady=(0, 16))
        ttk.Label(frame, text="全局快捷键").grid(sticky="w")
        row = ttk.Frame(frame)
        row.grid(sticky="w", pady=(4, 12))
        parts = self.settings["hotkey"].split("+")
        self.modifiers = {}
        for index, name in enumerate(MODIFIERS):
            variable = tk.BooleanVar(value=name in parts[:-1])
            self.modifiers[name] = variable
            ttk.Checkbutton(row, text=name, variable=variable).grid(row=0, column=index, padx=(0, 12))
        self.key = tk.StringVar(value=parts[-1])
        ttk.Combobox(row, textvariable=self.key, values=KEYS, state="readonly", width=7).grid(row=0, column=3)
        ttk.Label(frame, text="远程翻译服务地址（Gradio 应用地址）").grid(sticky="w")
        self.url = tk.StringVar(value=self.settings["url"])
        ttk.Entry(frame, textvariable=self.url).grid(sticky="ew", pady=(4, 12))
        buttons = ttk.Frame(frame)
        buttons.grid(sticky="w")
        self.save_button = ttk.Button(buttons, text="保存设置", command=self.save)
        self.save_button.grid(row=0, column=0, padx=(0, 12))
        ttk.Label(frame, textvariable=self.status, wraplength=560).grid(sticky="w", pady=(16, 0))

    def build_records_view(self):
        pane = ttk.Panedwindow(self.root, orient="horizontal")
        pane.grid(row=1, column=0, sticky="nsew", padx=10)
        left = ttk.Frame(pane, padding=8)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)
        pane.add(left, weight=1)
        heading = ttk.Frame(left)
        heading.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="原文目录").grid(row=0, column=0, sticky="w")
        ttk.Button(heading, text="一键清空", command=self.clear_records).grid(row=0, column=1, sticky="e")
        ttk.Style(self.root).configure("Records.Treeview", font=("Segoe UI Symbol", 10), rowheight=26)
        self.entries = ttk.Treeview(left, columns=("status",), show="tree headings", selectmode="browse", style="Records.Treeview")
        self.entries.heading("#0", text="原文")
        self.entries.heading("status", text="状态")
        self.entries.column("#0", width=260, minwidth=0, stretch=False)
        self.entries.column("status", width=STATUS_COLUMN_WIDTH, minwidth=STATUS_COLUMN_WIDTH, stretch=False, anchor="center")
        self.entries.bind("<Configure>", self.resize_directory_columns)
        self.entries.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.entries.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.entries.configure(yscrollcommand=scrollbar.set)
        self.entries.bind("<<TreeviewSelect>>", self.display_record)
        right = ttk.Frame(pane, padding=8)
        right.rowconfigure(4, weight=1)
        right.columnconfigure(0, weight=1)
        pane.add(right, weight=3)
        self.record_status = tk.StringVar(value="选择左侧条目查看结果")
        ttk.Label(right, textvariable=self.record_status).grid(row=0, column=0, sticky="w")
        ttk.Label(right, text="原文").grid(row=1, column=0, sticky="w", pady=8)
        self.original = ScrolledText(right, height=5, wrap="word", font=("Microsoft YaHei UI", 10), state="disabled")
        self.original.grid(row=2, column=0, sticky="ew")
        ttk.Label(right, text="翻译 / 解析").grid(row=3, column=0, sticky="w", pady=8)
        self.translation = MarkdownText(right, wrap="word", font=("Microsoft YaHei UI", 11), state="disabled")
        self.translation.grid(row=4, column=0, sticky="nsew")

    def refresh_records(self):
        selection = self.entries.selection()
        records = self.history.records()
        self.records = {str(row["id"]): row for row in records}
        children = self.entries.get_children()
        if children:
            self.entries.delete(*children)
        for key, row in self.records.items():
            self.entries.insert("", "end", iid=key, text=directory_title(row["original"]), values=(STATUS_ICONS[row["status"]],))
        key = selection[0] if selection and selection[0] in self.records else next(iter(self.records), None)
        if key is not None:
            self.entries.selection_set(key)
        self.display_record()

    def resize_directory_columns(self, event):
        self.entries.column("#0", width=max(0, event.width - STATUS_COLUMN_WIDTH - 4))
        self.entries.column("status", width=STATUS_COLUMN_WIDTH)

    def display_record(self, event=None):
        selection = self.entries.selection()
        row = self.records.get(selection[0]) if selection else None
        self.record_status.set(STATUS_LABELS[row["status"]] if row else "选择左侧条目查看结果")
        self.original.configure(state="normal")
        self.original.delete("1.0", "end")
        self.original.insert("1.0", row["original"] if row else "")
        self.original.configure(state="disabled")
        self.translation.render(row["translation"] if row else "")

    def show_toast(self, message="已添加翻译"):
        from windows import show_without_activation
        if self.toast_timer is not None:
            self.root.after_cancel(self.toast_timer)
        if self.toast is None:
            window = tk.Toplevel(self.root)
            window.withdraw()
            window.overrideredirect(True)
            window.attributes("-topmost", True)
            self.toast = window
            self.toast_label = ttk.Label(window, padding=(24, 14), font=("Microsoft YaHei UI", 12))
            self.toast_label.pack()
        self.toast_label.configure(text=message)
        self.toast.update_idletasks()
        width = self.toast.winfo_reqwidth()
        height = self.toast.winfo_reqheight()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.toast.geometry(f"{width}x{height}+{x}+{y}")
        self.toast.update_idletasks()
        show_without_activation(self.toast, x, y)
        self.toast_timer = self.root.after(1000, self.hide_toast)

    def hide_toast(self):
        if self.toast_timer is not None:
            self.root.after_cancel(self.toast_timer)
        self.toast_timer = None
        if self.toast is not None:
            self.toast.withdraw()

    def clear_records(self):
        try:
            self.history.clear()
        except sqlite3.Error:
            self.status.set("清空失败，请检查本地记录文件是否被占用或可写。")
            return
        self.history_epoch += 1
        self.pending.clear()
        self.latest.clear()
        self.hide_toast()
        self.refresh_records()
        self.status.set("已清空全部记录。")

    def handle_translation_event(self, kind, epoch, token, text, result=""):
        if kind == "captured" or kind == "capture_failed":
            self.capturing = False
        else:
            self.busy = False
        if epoch != self.history_epoch:
            self.start_next_translation()
            return
        if kind == "capture_failed":
            self.status.set(result)
            self.show_toast(result)
            return
        if kind == "captured":
            state = "pending"
            value = "等待翻译…"
        else:
            if self.latest.get(text) != token:
                self.start_next_translation()
                return
            state = "completed" if kind == "done" else "failed"
            value = result
        try:
            self.history.put(text, value, state)
        except sqlite3.Error:
            self.status.set("保存翻译记录失败，请检查本地记录文件是否被占用或可写。")
            self.start_next_translation()
            return
        if kind == "captured":
            self.latest[text] = token
            self.pending.append((epoch, token, text, self.settings["url"]))
            self.show_toast()
        self.refresh_records()
        self.status.set("已添加翻译，等待后台处理。" if kind == "captured" else
                        "翻译完成，已保存到记录。" if kind == "done" else "翻译失败，详情已保存到记录。")
        self.start_next_translation()

    def start_next_translation(self):
        if self.busy or self.closing:
            return
        while self.pending:
            epoch, token, text, url = self.pending.popleft()
            if epoch == self.history_epoch and self.latest.get(text) == token:
                break
        else:
            return
        self.busy = True
        self.status.set(f"正在后台翻译，等待 {len(self.pending)} 条。")

        def work():
            try:
                result = translate(text, url, stop=self.stop)
                self.events.put(("done", epoch, token, text, result))
            except Exception as error:
                message = str(error) if isinstance(error, (RuntimeError, ValueError)) else "翻译失败，请稍后重试。"
                self.events.put(("failed", epoch, token, text, message))

        threading.Thread(target=work, daemon=True).start()

    def initialized(self, error):
        self.status.set(error or f"已就绪：{self.settings['hotkey']}。可最小化此窗口。")

    def minimize_to_tray(self):
        if self.closing:
            return
        try:
            if self.tray is None:
                from tray import TrayIcon
                self.tray = TrayIcon(self.events)
            self.tray.ensure_visible()
        except RuntimeError as error:
            self.restore_settings()
            self.status.set(str(error))
            return
        self.root.withdraw()

    def on_unmap(self, event):
        if event.widget is self.root and self.root.state() == "iconic":
            self.minimize_to_tray()

    def restore_settings(self):
        self.root.deiconify()
        self.root.lift()


    def save(self):
        if self.saving:
            return
        if self.busy or self.capturing or self.pending:
            self.status.set("正在取词或翻译，请完成后保存设置。")
            return
        try:
            hotkey = "+".join([name for name, var in self.modifiers.items() if var.get()] + [self.key.get()])
            parse_hotkey(hotkey)
            new = {"hotkey": hotkey, "url": validate_url(self.url.get())}
        except ValueError as error:
            messagebox.showerror("设置无效", str(error), parent=self.root)
            return
        self.saving = True
        self.save_button.state(["disabled"])
        old = dict(self.settings)

        def configured(error):
            if error:
                self.finish_save(error)
                return
            try:
                save_settings(new)
            except OSError:
                self.listener.configure(old["hotkey"], lambda rollback: self.finish_save(
                    "设置保存失败，请检查本地设置目录权限。" + (rollback or "")))
                return
            self.settings = new
            self.url.set(new["url"])
            self.finish_save(f"已保存并生效：{new['hotkey']}")

        self.listener.configure(hotkey, configured)

    def finish_save(self, status):
        self.saving = False
        self.save_button.state(["!disabled"])
        self.status.set(status)

    def poll(self):
        if self.closing:
            return
        try:
            while True:
                event = self.events.get_nowait()
                kind, *data = event
                if kind == "configured":
                    callback, error = data
                    callback(error)
                elif kind == "tray_open":
                    self.restore_settings()
                elif kind == "tray_exit":
                    self.close()
                    return
                elif kind == "tray_error":
                    self.restore_settings()
                    self.status.set(data[0])
                elif kind == "hotkey":
                    if self.saving:
                        self.status.set("正在保存设置，请稍后重新取词。")
                        self.show_toast("正在保存设置，请稍后重试")
                    elif self.capturing:
                        self.status.set("正在取词，请释放快捷键后重试。")
                        self.show_toast("正在取词，请释放快捷键后重试")
                    else:
                        self.start_translation(data[0])
                elif kind in ("captured", "capture_failed", "done", "failed"):
                    self.handle_translation_event(kind, *data)
        except Empty:
            pass
        self.root.after(40, self.poll)

    def start_translation(self, foreground):
        self.capturing = True
        self.status.set("正在读取选中文本，请释放快捷键…")
        epoch = self.history_epoch
        self.sequence += 1
        token = self.sequence

        def work():
            from windows import capture_selection
            try:
                text = capture_selection(foreground, self.owner)
                self.events.put(("captured", epoch, token, text))
            except Exception as error:
                message = str(error) if isinstance(error, (RuntimeError, ValueError)) else "取词失败，请重新选中文字后重试。"
                self.events.put(("capture_failed", epoch, token, "", message))

        threading.Thread(target=work, daemon=True).start()

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.stop.set()
        self.pending.clear()
        if self.toast_timer is not None:
            self.root.after_cancel(self.toast_timer)
        if self.tray is not None:
            self.tray.close()
        self.listener.close()
        self.history.close()
        self.root.destroy()


def main(argv=None):
    if os.name != "nt":
        raise SystemExit("Quick Translator requires Windows.")
    parser = argparse.ArgumentParser(description="Windows 快捷翻译")
    parser.add_argument("--background", action="store_true", help="启动时隐藏主界面，保留托盘图标")
    args = parser.parse_args(argv)
    from startup import acquire_instance, release_instance
    instance = acquire_instance()
    if instance is None:
        return
    try:
        root = tk.Tk()
        if args.background:
            root.withdraw()
        try:
            Application(root, background=args.background)
        except (OSError, sqlite3.Error):
            root.withdraw()
            messagebox.showerror("无法启动", "无法打开本地翻译记录，请检查记录目录权限和数据库文件。", parent=root)
            root.destroy()
            return
        root.mainloop()
    finally:
        release_instance(instance)


if __name__ == "__main__":
    main()
