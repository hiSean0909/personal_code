# Computer Dashboard

A local Windows dashboard showing C/D drive storage usage and live upload/download rates.

See [deliverables](deliverables/README.md) for the available startup or access instructions.

## Features

- Total, used, and free capacity for C: and D:, with usage bars
- Disk information refreshed every 5 seconds and on demand
- Upload and download rates sampled every second, displayed in B/s, KiB/s, or MiB/s
- Separate status messages for unavailable drives and network readings

Disk capacity uses binary units: 1 GiB = 1024³ bytes. Network rates measure actual traffic across local network interfaces, including LAN traffic, rather than testing the maximum speed of an internet connection. Virtual adapters can count the same traffic more than once.

## Requirements

- Windows and Python 3.10+
- A project-local `.venv/`
- `psutil` for reading Windows network counters; other backend functionality uses the Python standard library

## Setup and Startup

Open PowerShell in this project directory. For the first run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the server:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:8765> in a browser. Press `Ctrl+C` in the terminal to stop the server.

The server listens only on `127.0.0.1` and reads information from the computer running it. Network sampling runs while the server is active. The first network reading requires two samples, approximately one second apart. All browser tabs share the same samples.

## Files

| File | Purpose |
|---|---|
| `app.py` | Local HTTP server, disk readings, and network sampling |
| `index.html` | Dashboard layout |
| `style.css` | Styling and responsive layout |
| `app.js` | API requests, rendering, and automatic refresh |
| `requirements.txt` | Pinned Python dependencies |

## API

- `GET /api/disks`: timestamp and availability, total, used, and free bytes for each drive
- `GET /api/network`: sample timestamp, availability, and upload/download rates in bytes per second; unavailable readings include a message

Network rates use the difference between consecutive per-interface counters divided by the actual elapsed time from a monotonic clock. New or reset interfaces establish a baseline before contributing traffic. Sampling failures clear the baseline; readings resume after two successful samples.
