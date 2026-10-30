"""Serve a local dashboard showing disk usage and network transfer rates."""

import json
import shutil
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import psutil


PROJECT_DIR = Path(__file__).resolve().parent
ADDRESS = ("127.0.0.1", 8765)
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class NetworkMonitor:
    def __init__(self):
        self._previous = None
        self._lock = threading.Lock()
        self._reading = {"available": False, "message": "正在采样，请稍候…"}

    def sample(self):
        reading = {"updated_at": datetime.now().astimezone().isoformat()}
        try:
            counters = psutil.net_io_counters(pernic=True)
            sampled_at = time.monotonic()
            if not counters:
                self._previous = None
                reading.update(available=False, message="暂无可读取的网卡")
            else:
                previous = self._previous
                self._previous = (sampled_at, counters)
                if previous is None:
                    reading.update(available=False, message="正在采样，请稍候…")
                else:
                    elapsed = sampled_at - previous[0]
                    # Compare each interface separately so reconnects cannot cause spikes.
                    comparable = [
                        name for name, counter in counters.items()
                        if name in previous[1]
                        and counter.bytes_sent >= previous[1][name].bytes_sent
                        and counter.bytes_recv >= previous[1][name].bytes_recv
                    ]
                    if elapsed > 0 and comparable:
                        upload = sum(
                            counters[name].bytes_sent - previous[1][name].bytes_sent
                            for name in comparable
                        ) / elapsed
                        download = sum(
                            counters[name].bytes_recv - previous[1][name].bytes_recv
                            for name in comparable
                        ) / elapsed
                        reading.update(
                            available=True,
                            upload_bytes_per_second=upload,
                            download_bytes_per_second=download,
                        )
                    else:
                        reading.update(available=False, message="网卡状态变化，正在重新采样…")
        except (OSError, psutil.Error):
            self._previous = None
            reading.update(available=False, message="网速暂不可用，将自动重试")
        with self._lock:
            self._reading = reading

    def snapshot(self):
        with self._lock:
            return self._reading.copy()

    def run(self, stop_event):
        self.sample()
        while not stop_event.wait(1):
            self.sample()


def read_disks():
    disks = []
    for drive in ("C:", "D:"):
        disk = {"drive": drive, "available": False}
        try:
            usage = shutil.disk_usage(drive + "\\")
            disk.update(
                available=True,
                total=usage.total,
                used=usage.used,
                free=usage.free,
            )
        except OSError:
            disk["message"] = "无法读取此磁盘，请确认磁盘存在且可访问"
        disks.append(disk)
    return {"updated_at": datetime.now().astimezone().isoformat(), "disks": disks}


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/disks":
            content = json.dumps(read_disks(), ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif path == "/api/network":
            content = json.dumps(
                self.server.network_monitor.snapshot(), ensure_ascii=False
            ).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif path in STATIC_FILES:
            filename, content_type = STATIC_FILES[path]
            content = (PROJECT_DIR / filename).read_bytes()
        else:
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)


def main():
    with ThreadingHTTPServer(ADDRESS, DashboardHandler) as server:
        server.network_monitor = NetworkMonitor()
        stop_event = threading.Event()
        sampler = threading.Thread(
            target=server.network_monitor.run, args=(stop_event,), daemon=True
        )
        sampler.start()
        print(f"电脑信息看板已启动：http://{ADDRESS[0]}:{ADDRESS[1]}", flush=True)
        print("按 Ctrl+C 停止服务。", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止。", flush=True)
        finally:
            stop_event.set()
            sampler.join()


if __name__ == "__main__":
    main()
