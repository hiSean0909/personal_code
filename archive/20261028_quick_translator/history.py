"""Local translation records. Accessed only from the Tk main thread."""

import sqlite3

from translator import SETTINGS_PATH


HISTORY_PATH = SETTINGS_PATH.with_name("history.sqlite3")
STATUS_LABELS = {"pending": "翻译中", "completed": "完成", "failed": "失败"}


class HistoryStore:
    def __init__(self, path=HISTORY_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        try:
            with self.connection:
                self.connection.execute("""CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY,
                    original TEXT NOT NULL UNIQUE,
                    translation TEXT NOT NULL,
                    status TEXT NOT NULL
                )""")
                self.connection.execute(
                    "UPDATE records SET status = 'failed', translation = ? WHERE status = 'pending'",
                    ("上次翻译因软件退出而中断，请重新选中原文并按快捷键。",))
        except Exception:
            self.connection.close()
            raise

    def put(self, original, translation, status):
        original = original.strip()
        if not original:
            raise ValueError("原文不能为空。")
        if status not in STATUS_LABELS:
            raise ValueError("不支持的翻译状态。")
        with self.connection:
            self.connection.execute("""INSERT INTO records (original, translation, status)
                VALUES (?, ?, ?) ON CONFLICT(original) DO UPDATE SET
                translation = excluded.translation, status = excluded.status""",
                (original, translation, status))

    def records(self):
        return self.connection.execute("SELECT * FROM records ORDER BY id DESC").fetchall()

    def clear(self):
        with self.connection:
            self.connection.execute("DELETE FROM records")

    def close(self):
        self.connection.close()
