# Quick Translator Specification

## Purpose and Scope

Let a Windows user translate selected text without manually copying it into a browser. Reuse the existing remote Gradio translator and its prompt. Develop locally on `main`. This project uses native windows instead of the repository's default web interface because rapid desktop interaction is its primary purpose.

## Confirmed Requirements

- Run as a lightweight local Windows application with a main records/detail interface that minimizes to the system tray
- Open a separate settings window from a dedicated Settings button; show no records or settings tabs in the main window
- Place Clear All on the same header row as Original Directory
- Display at most 20 characters in each directory original label, using the first 19 characters plus an ellipsis for longer labels; retain the full original in storage and the detail area
- Show directory status using hourglass, check, and cross symbols, with a fixed centered status column that remains visible at the supported layout sizes
- Hide the main window from the taskbar when either minimize control is used; keep the shortcut listener active
- Restore the main window by double-clicking the tray icon or choosing Open Main Window from its context menu; provide Exit in that menu
- Follow Windows notification-area visibility preferences, including its hidden-icon overflow behavior
- Register a configurable global shortcut, initially `Ctrl+Alt+T`
- Capture selected, copyable text from the foreground application only when the shortcut is pressed
- Submit the text to a configurable remote Gradio service URL, initially `http://122.51.135.229:7861`
- Call the service's `/translate` endpoint with a single `message` argument and keep requests independent
- Translate in the background while keeping the main window hidden; after successfully saving a capture, show a non-activating notification reading 已添加翻译 at the center of the primary screen for one second
- List captured words, phrases, and paragraphs with translation status on the left of the main window; show the selected original and result on the right
- Persist records locally across restarts, updating the existing entry when the same trimmed original is captured again
- Provide one-click clearing of all records, including persisted data; results from requests started before a successful clear must not restore cleared entries
- Persist the shortcut and URL locally and apply saved settings without restarting
- Report shortcut conflicts, missing selection, connection errors, and request timeouts
- Capture new selections while translation is running, save them immediately, and translate queued captures in FIFO order with one remote request active at a time
- Serialize clipboard captures; explain overlapping capture attempts instead of silently dropping them
- Clear queued work along with history and ignore late capture or translation results from before clearing
- Use Python standard-library Windows integration and Tkinter; use `gradio_client` for the remote protocol
- Start automatically after the Administrator user logs in, using a shortcut in that user's Windows Startup folder
- Launch login startup with the main window hidden in the tray; manual startup continues to show the main window
- Keep one running application instance per Windows session, including when manual and login startup overlap

## Boundaries

- Support ordinary applications that copy selected text with `Ctrl+C`; OCR, elevated application interaction, and executable packaging are outside the first release
- Wait for shortcut modifiers to be released before simulating copy; avoid copying if the foreground window has changed
- Require a clipboard sequence change before reading text, so an old clipboard value is never submitted as a new selection
- Restore previous Unicode clipboard text after capture if the clipboard has not changed again; non-text clipboard formats are not preserved
- Only the explicitly captured text is sent to the configured remote service; persist original text, results, and status locally without storing model credentials
- Keep one translation request active at a time; a clear removes its records but does not guarantee cancellation of a remote request
- Mark translations interrupted by application exit as failed when the application next starts
- Render common Markdown headings, bold, italic, lists, quotations, fenced code, links, rules, and pipe tables as selectable text using Tkinter without new dependencies
- Preserve the original Markdown response in storage; advanced CommonMark, embedded HTML, and remote images are outside this renderer
- Repeated identical trimmed originals retain one record; only the latest accepted capture may update its result
- Keep the existing translator project and deployed service unchanged

## Acceptance Criteria

| ID | Scenario | Expected result |
| --- | --- | --- |
| A1 | Select text in an ordinary editor and press the configured shortcut | Capture it, make one request in the background, and save the original and translation; show only the one-second capture notification |
| A2 | Save a different valid shortcut and restart the application | New shortcut remains configured; the old shortcut is released |
| A3 | Save a different valid Gradio service URL and restart | The saved service is used |
| A4 | Shortcut is occupied by another application | Explain the conflict and keep the previous shortcut when possible |
| A5 | Copy produces no new clipboard text | Show a selection error and make no request |
| A6 | Remote service fails or exceeds the request timeout | Show a concise error and permit another request |
| A7 | Press the shortcut repeatedly during translation | Save each successful capture immediately and translate in FIFO order with one active remote request |
| A8 | Click a left-side record | Show that record's original, status, and translation on the right |
| A9 | Exit from the settings window | Release the global shortcut and stop the application |
| A10 | Capture while the clipboard previously contained Unicode text | Restore that text unless another application changed the clipboard |
| A11 | Minimize using the settings button or title bar | Hide the settings taskbar window, retain the tray icon, and keep translation available |
| A12 | Double-click the tray icon or choose Open Main Window | Restore the main window |
| A13 | Choose Exit from the tray menu | Remove the tray icon, release the shortcut, and stop the application |
| A14 | Tray icon creation fails | Keep settings accessible and explain the problem instead of hiding the window |
| A15 | Restart the application | Retain saved entries and results; mark previously pending translations as interrupted |
| A16 | Capture identical trimmed original text again | Update the same entry instead of duplicating it |
| A17 | Click Clear All | Empty the list, detail view, and persisted history immediately |
| A18 | A request started before Clear All completes later | Keep its result out of the cleared list and persisted history |
| A19 | Saving or clearing history fails | Display a status error and preserve previously committed records |
| A20 | Click Settings repeatedly | Open or restore one separate settings window with the existing save behavior |
| A21 | Browse a long original | Limit the directory label to 20 characters including ellipsis and show the full original on the right |
| A22 | Browse pending, completed, and failed records | Show hourglass, check, and cross status symbols in the directory |
| A23 | View the main window | Show records directly, without the previous records tab; place Clear All next to Original Directory |
| A24 | Administrator logs in | Run through the user's Startup shortcut and remain hidden in the system tray |
| A25 | Start another instance while one is already running | Exit the second instance before creating windows, registering a shortcut, or opening history |
| A26 | Background startup cannot create its tray icon | Restore the main window so the application remains accessible |

| A27 | Browse a Markdown response | Render common formatting and keep visible text selectable and copyable |
| A28 | Capture succeeds with the main window hidden | Show 已添加翻译 at the center of the primary screen for one second without stealing foreground focus |
| A29 | Clear history while captures are queued | Remove queued work and ignore late results from the cleared generation |
| A30 | Recapture the same original before an older request finishes | Keep one record and let only the latest capture update its result |

## Verification Plan

- Unit-test shortcut parsing, URL validation, settings persistence, independent remote calls, error mapping, clipboard sequence handling, and registration conflict behavior
- Verify real service metadata and one small translation request
- Smoke-test native window creation, real hotkey registration, clipboard capture, and cleanup where the execution environment permits
- Record the exact extent of verification and any remaining manual desktop checks in the README
- Verify tray lifecycle, restore/exit actions, both minimize paths, and safe handling of tray creation failures
- Verify local persistence, duplicate updates, record selection/detail, restart interruption handling, and clearing before and after capture events arrive
