# Quick Translator

A small Windows client for the existing Gradio translation assistant. Select text in a normal application and press a global shortcut to translate and save it in the background. Browse saved entries in the main window whenever convenient. The client reuses the remote service's prompt and model configuration.

## Requirements and Setup

- Windows 10 or later with Python 3.14 and Tkinter
- Access to a Gradio translator exposing `/translate(message: str)`
- A project-local `.venv` and the dependency in `requirements.txt`

The project is in `D:\personal\git\personal_code\projects\20261028_quick_translator`. Its existing virtual environment and dependencies are preserved. Start it through `deliverables/start.cmd`, which resolves project paths from its parent directory. Use the virtual environment's Python executable directly; activation scripts and installed command wrappers can retain their original creation paths. Rebuild the environment only if a verified runtime path issue requires it.

Open PowerShell in this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`gradio_client` handles Gradio's queued API protocol. Windows shortcuts, clipboard access, and native windows use the Python standard library. No local Docker or model credentials are required.

## Startup and Use

Double-click `deliverables/start.cmd` after setup, or run:

```powershell
.\.venv\Scripts\pythonw.exe app.py
```

Use `python.exe app.py` instead when console diagnostics are needed.

1. Click the Settings button to open its separate window, then choose modifiers and a letter, digit, or F1–F11 key. The default is `Ctrl+Alt+T`. `Ctrl+C` is reserved for capturing text and cannot be the trigger. Closing settings leaves the application running; clicking Settings again restores the same window.
2. Set the translation service URL. The initial address is `http://122.51.135.229:7861`, matching the existing deployed translator. This field accepts a Gradio app base URL, not an arbitrary REST endpoint.
3. Save the settings, then optionally minimize the main window using its button or title bar. It hides from the taskbar and remains available through the notification-area (system tray) icon near the clock.
4. Select copyable text in a browser or editor, press the shortcut, and release its keys. Each successful capture is saved immediately and shows a non-activating 已添加翻译 notification at the center of the primary screen for one second. The main window stays hidden. Further captures are queued while earlier translations run; one remote request runs at a time in capture order. Overlapping clipboard captures report a retry message.
5. The main window directly shows the original directory on the left and details on the right. Directory original labels contain at most 20 characters, including an ellipsis when truncated. The full original remains available on the right. Status symbols are an hourglass for pending, a check for completed, and a cross for failed; the status column is centered and fixed in width.
6. Click Clear All beside Original Directory to remove every entry and clear the detail area immediately, without an additional confirmation dialog. Clearing also removes waiting translation tasks. Captures and requests started before clearing cannot restore entries when they finish. A remote request may still complete and consume the model account's balance.
7. Use Exit or close the main window to stop the application.

Double-click the tray icon to restore the main window, or right-click it and choose Open Main Window. The same menu provides Exit. Look inside the `^` hidden-icons area if the icon is not visible beside the clock. Windows controls whether the icon is folded or always visible, according to the user's notification-area preferences. The application does not change those preferences. If the tray icon cannot be created, the main window remains accessible and shows an error.

Settings are stored in `%LOCALAPPDATA%\QuickTranslator\settings.json`. Saving applies the shortcut and URL immediately. If a shortcut is occupied, the previous shortcut is retained when possible. A Windows session mutex prevents duplicate instances. If the application is already running, a second launch exits; use the tray icon to reopen the main window.

## Login Startup

Login startup uses the Administrator user's Startup folder:

```text
C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\QuickTranslator.lnk
```

The shortcut runs this project's `.venv\Scripts\pythonw.exe` with the absolute `app.py` path and `--background`. It starts after Administrator logs in, with no console or main window; use the tray icon to open the main interface. A tray initialization failure restores the main window so the application stays accessible. This is a user login startup entry and uses the user's normal execution privileges.

After the directory move on 2026-10-30, the startup shortcut points to `D:\personal\git\personal_code\projects\20261028_quick_translator\.venv\Scripts\pythonw.exe`, with the project's absolute `app.py` path and `--background`, and uses the project directory as its working directory. The shortcut properties were verified; actual sign-out/sign-in startup remains to be observed.

To install or refresh that shortcut from this project directory:

```powershell
.\deliverables\enable_startup.ps1
```

The script targets the Administrator profile explicitly. It checks the Python executable and application paths before creating the shortcut. Remove `QuickTranslator.lnk` from the folder above to disable login startup. After a move, review and update the known shortcut's target, arguments, and working directory: the installer deliberately rejects an existing shortcut pointing to a different executable path. Once those paths match, the installer can refresh the shortcut normally. Manual `deliverables/start.cmd` launches still show the main window when no instance is already running.

Records are stored in `%LOCALAPPDATA%\QuickTranslator\history.sqlite3` using Python's standard-library SQLite support. They survive restarts. Recapturing the exact same trimmed original updates that entry; matching is case-sensitive. Entries interrupted while pending are marked failed on the next start. Only one translation request is active at a time; clearing while it runs does not open another request slot until it finishes. Capturing remains available during translation. Repeated identical originals keep one record, and older requests cannot overwrite the latest accepted capture. Settings can be saved once capture and translation work is idle.

The client sends only the selected text to the configured service. Translations can consume the remote model account's balance. It stores original text, results, and status locally, without credentials. Gradio client analytics are disabled. Translation jobs time out after 120 seconds; connection operations have a 20-second timeout. Exiting releases the shortcut immediately and attempts to cancel the current job; connection cleanup can take additional time, and an already submitted remote model request may continue. Capture and translation errors appear in the main status area, with translation errors also saved against their original entry. Saving and clearing failures are reported in the status area.

## Selection and Display Limits

Capture simulates `Ctrl+C` after the shortcut keys are released. It supports applications that copy their selection this way. Images, scanned PDFs, protected content, administrator windows, and applications with different copy shortcuts may not work. If no fresh text is copied, the client reports an error instead of sending old clipboard content.

Previous Unicode clipboard text is restored when possible, provided no other clipboard change occurs. Other clipboard formats, including images and rich formatting, are not preserved. Avoid changing windows or copying other content during capture. Restoring clipboard text can create clipboard-history entries.

The result renders common Markdown headings, bold, italic, lists, quotations, fenced code blocks, links, horizontal rules, and pipe tables using Tkinter. Visible text remains selectable and copyable; the original response is stored unchanged. HTTP/HTTPS links open only when clicked. Advanced CommonMark, embedded HTML, and remote images are outside this lightweight renderer. Minimizing keeps the global shortcut active in the background; completed and failed translations never open a result window. This release does not add OCR or an executable installer. Native windows are a deliberate project exception to the repository's default web interface.

## Design and Specification

See [SPEC.md](SPEC.md) for confirmed requirements and acceptance criteria.

| File | Purpose |
| --- | --- |
| `app.py` | Main records/detail interface, settings, and background request coordination |
| `markdown_view.py` | Selectable Tkinter rendering for common Markdown |
| `history.py` | Transactional local SQLite record storage |
| `deliverables/start.cmd` | Double-click launcher using the project's Python environment |
| `deliverables/enable_startup.ps1` | Install the Administrator user's login startup shortcut |
| `startup.py` | Windows session mutex for duplicate-instance prevention |
| `windows.py` | Windows hotkey registration and clipboard selection capture |
| `tray.py` | Native Windows notification-area icon, restore menu, and exit cleanup |
| `translator.py` | Settings, shortcut validation, and Gradio calls |
| `requirements.txt` | Pinned Gradio client dependency |

## Verification

Center-position correction verified on 2026-10-29: native `GetWindowRect` measurements on a 1280-by-800 primary screen placed the notification center at (640, 399.5), within one pixel of the screen center. First display, repeated display, and a longer message all passed position, visibility, foreground-preservation, and one-second auto-hide checks. The Win32 display function now receives the calculated coordinates directly instead of reading stale positions from a hidden Tk window.

Verified on 2026-10-29: 29 focused checks passed using temporary history databases and simulated remote translations. Coverage includes common Markdown formatting and code literals, horizontal scrolling for wide tables/code, the minimum window size, FIFO translation while further captures are saved, duplicate-result ordering, failures and recovery, clearing queued work and late events, and notification visibility/timer renewal. Native Win32 visibility and foreground-window checks confirmed that the one-second notification appears with a hidden main window and preserves the foreground window. Python source parsing, changed-file whitespace checks, and `pip check` passed. No new dependency was added, no real model request was made, and existing user records were not modified. Full physical shortcut-to-selection interaction remains a manual desktop check. Exit the running tray instance and launch `deliverables/start.cmd` to load these changes.

The development test files and temporary bytecode cache were removed during archiving according to repository policy. The results below record verification completed before archiving. Archive checks focus on relocation, startup paths, preserved dependencies, and access to existing data.

Archive verification on 2026-10-28 passed: the preserved virtual environment resolved its prefix to the archive directory and imported Tkinter, `gradio_client` 2.7.2, and all application modules. Runtime source files, launchers, and the dependency list retained identical SHA-256 hashes. The existing translation database was readable and passed SQLite `quick_check`; its file hash was unchanged. A native hidden-window smoke check from the archive directory registered the tray icon and configured global shortcut, displayed simulated background results using a temporary database, and released its resources on exit. No translation request was made and no existing user records were written during this check.

Verified on Windows on 2026-10-28:

- All 55 regression tests passed, covering clipboard freshness, competing changes, shortcut conflicts, settings rollback, repeated triggers, remote failures, timeouts, exit cancellation, tray lifecycle, minimize paths, menu actions, tray failure recovery, persistence, duplicate updates, clearing while requests are active, directory label limits, and startup behavior
- `pip check`, Python compilation, and the tracked diff whitespace check passed
- The previous release verified real `/translate` metadata and a real `Hello` request returning 1,237 characters; the remote-call implementation is unchanged in this update
- An actual hidden Tk main-window check passed for list population, selecting a record to display its full original/result, background completion without restoring or creating a window, clearing the list/details, ignoring a late result, and database emptiness after reopening; this check used simulated translation events and mocked hotkey/tray services
- A transparent Tk layout check passed at 820×520 and 1000×700: status cell bounding boxes fit completely, all three status symbols were populated, directory labels were limited to 20 characters, full originals remained in details, Clear All shared the directory header, and no notebook tabs remained. The separate settings window was reused after closing and reopening, and its save behavior passed with mocked persistence
- A real cross-process named-mutex check rejected a second process and allowed a new process after release. A hidden Tk check confirmed background mode left the main window withdrawn, using mocked tray and hotkey services. The PowerShell installer passed parsing and its generated shortcut properties were read back after installation
- The previous release verified actual hotkey registration and a native tray lifecycle check, including double-click message delivery through Tk; physical mouse interaction remains a manual check

To check tray behavior manually after restarting the application, minimize the main window using each minimize control, find the icon near the clock or under `^`, double-click to restore it, and try both context-menu commands. The icon's placement in overflow follows Windows settings.

Full selection-to-saved-record interaction in an external desktop application has not been manually verified. Start the application, minimize it, select `Hello` in an ordinary editor, press `Ctrl+Alt+T`, and release the keys. Confirm the one-second notification appears at the center of the primary screen without changing foreground focus or restoring the main window. Select several different texts while the first translation is pending and confirm each appears in the directory and completes in order. Later open the main window through the tray and select the saved entry to view its translation. Restart to check persistence, recapture the same original to check duplicate updates, and use Clear All while a translation is running to check that the old result does not return. Also check that settings remain saved. These real translations use the remote model account.
