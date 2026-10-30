# Codex Status Bar

A planned local Windows tool that displays remaining 5-hour allowance, weekly allowance, and current-conversation context percentage in the center of the Codex desktop application's top bar.

## Status

The project is on hold at the user's request. The [specification](spec.md) v1.1, [technical design](design.md) v1.0, and [task plan](tasks.md) v1.0 are confirmed. Runtime discovery and independent allowance reads are verified. Live desktop feasibility remains incomplete: direct startup of the packaged Codex executable failed with `EPERM`, and an alternative launch method requires verification. Ring rendering and continuous monitoring are not implemented yet.

This project retains the expanded workflow because of its desktop integration risks and the explicitly requested design and task reviews. Simpler projects in this repository default to specification followed by implementation. All deliverables use English.

## Prerequisites

- Windows with the Microsoft Store Codex desktop application installed and signed in.
- An existing executable managed Codex CLI under the user's local OpenAI installation.
- Node.js 24 or later, either on PATH or in the existing Codex companion runtime. The PowerShell entry checks both locations and leaves system Node.js unchanged.
- Use a normal PowerShell session under the same Windows account as Codex. No npm installation is required.
- The launcher supports Windows PowerShell 5.1 and PowerShell 7. Runtime discovery parses `node --version` so it does not depend on shell-specific JavaScript argument quoting.

## Feasibility Commands

Open PowerShell in this project directory:

```powershell
./manage.ps1 doctor
./manage.ps1 quota
```

`doctor` reports runtime and application discovery plus whether debugging is available. `quota` reads usage windows through an owned app-server, prints only duration and used percentage, then stops that server. These are diagnostic used percentages; the final rings will show remaining percentages.

To continue the approved desktop feasibility check:

1. Save work and fully quit Codex voluntarily.
2. From PowerShell in this directory, run:

   ```powershell
   ./manage.ps1 start
   ```

3. Return to this chat in the reopened Codex application and ask to continue implementation.

The current `start` command enables loopback debugging for inspection only. It does not start a ring monitor. It refuses to interrupt an existing Codex process. Debugging startup is implemented but remains unverified on this installation until the first user-managed restart.

Once Codex exposes debugging, the read-only inspection command is:

```powershell
./manage.ps1 inspect
```

It reports window type, viewport dimensions, visible top-bar rectangles, active-page count, and whether the location contains a conversation ID. It omits conversation IDs and message bodies. The visible conversation adapter will be finalized after live inspection.

## Debugging Lifecycle

The debugging endpoint uses `127.0.0.1:39222`. CDP allows window-script execution and is accessible to other local processes; keep it on loopback and do not forward it. The client package and login configuration are preserved.

No background monitor exists at this feasibility stage. To close the debugging endpoint, fully quit Codex and reopen it through its original icon. The final start/status/stop monitor interface will be added after the feasibility gate passes.

## Verification So Far

- Existing Node.js v24.19.0 and codex-cli 0.162.0-alpha.17.2 discovered successfully.
- Standalone allowance reads returned both required windows and matched the desktop read within ongoing usage changes.
- Eight focused tests passed, covering protocol behavior, endpoint restrictions, and saved-file launcher compatibility with Windows PowerShell 5.1 and PowerShell 7.
- The launcher was verified against the real installation in both PowerShell hosts. Runtime discovery uses `node --version`; management errors retain their diagnostics and exit codes.
- Starting while Codex is active without debugging is refused, preserving ongoing work.
- Live debugging startup, route identity, top-bar placement, switching latency, and ring rendering remain unverified.

Run the existing tests using Node.js 24:

```powershell
# Use the same Node.js 24 executable selected by the launcher.
& "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe" --test feasibility.test.cjs launcher.test.cjs
```

The implementation keeps project files relative to the scripts. Move the entire project folder together when archiving; no external startup entry is registered.

## Reference

Inspired by [Lorie7813/codex-usage-card](https://github.com/Lorie7813/codex-usage-card). The confirmed design calls for independent implementation; any direct reuse requires source verification and preservation of applicable license notices.
