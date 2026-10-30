# Codex Status Bar Task Plan

- Version: v1.0, confirmed
- Requirements: [spec.md v1.1](spec.md), confirmed
- Design: [design.md v1.0](design.md), confirmed
- Current stage: implementation
- Implementation status: T-01 complete; T-02 awaiting user-managed Codex reopening

## 1. Selected Workflow and Authorization

This project uses the expanded six-stage workflow because desktop UI integration depends on internal routes, layout, authentication context, and local records. The user explicitly requested separate design and task deliverables. The repository's default for simpler projects remains specification followed by implementation.

The user confirmed tasks.md, authorizing progression into implementation of T-01 through T-07 within the approved scope. T-08 and T-09 belong to the later acceptance and delivery stages, each subject to its stage confirmation gate.

Produce all files, interface labels, status messages, and verification records in English. Use existing runtimes and standard libraries. Keep runtime artifacts under ignored `.runtime/`, and use synthetic fixtures instead of copying personal conversation content into tests.

## 2. Task Overview

| ID | Task | Dependencies | Expected outcome | Status |
| --- | --- | --- | --- | --- |
| T-01 | Verify runtime, executable discovery, and independent allowance reads | Development authorization | Reusable discovery and verified account-data access | Complete |
| T-02 | Verify live CDP, visible conversation identity, and top-bar placement | T-01 and user-managed Codex reopening when needed | Proven target selection and feasible placement for the observed client | In progress, awaiting user reopening |
| T-03 | Implement metric calculations | T-01, T-02 | Verified allowance, context, rounding, color, and unavailable-state calculations | Not started |
| T-04 | Implement the data readers | T-03 | Serialized quota reads and read-only incremental context reads | Not started |
| T-05 | Implement the ring component | T-02, T-03 | Three centered rings with lifecycle cleanup and theme support | Not started |
| T-06 | Integrate scheduling and management | T-04, T-05 | Working start, status, stop, switching, and reconnection | Not started |
| T-07 | Verify implementation and finish operating documentation | T-06 | Relevant checks passed and an implementation review ready for the user | Not started |
| T-08 | Perform acceptance against the specification | T-07 and user confirmation to enter acceptance | Criterion-by-criterion acceptance results | Not started |
| T-09 | Deliver the verified local version | T-08 and user confirmation to enter delivery | Runnable handoff and documented operating boundaries | Not started |

## 3. Implementation Tasks

### T-01. Runtime and Allowance Feasibility

- [x] Discover existing Node.js 24, verify WebSocket, fetch, and node:sqlite, and preserve the system Node.js installation.
- [x] Discover an executable managed Codex CLI and the installed desktop application without fixed version directories.
- [x] Start an owned app-server over stdio, initialize it, and perform a read-only allowance request through existing login state.
- [x] Compare returned windows with the desktop account's authoritative allowance; keep credentials and account identifiers out of diagnostic output.
- [x] Verify clean exit of the owned app-server and record sanitized feasibility results.

Expected files: the necessary discovery and app-server portions of `manage.ps1`, `manage.cjs`, and `codex-data.cjs`, plus `.gitignore` entries for runtime artifacts. Document any material incompatibility before further integration work.

Verification: the actual existing Node.js 24 and CLI execute successfully; both requested windows can be identified when provided by the account; failure produces an explicit unavailable result and cleanup leaves no owned child behind.

### T-02. Desktop Integration Feasibility Gate

- [ ] Coordinate a user-managed save and complete Codex exit if a compatible CDP endpoint is unavailable; preserve the current active session until the user reopens the app.
- [ ] Confirm that the installed desktop application accepts loopback-only debugging arguments and exposes the expected main-window target.
- [ ] Inspect the actual active page and route. Verify exact conversation identity while the user switches between two existing local conversations and returns home.
- [ ] Measure the top bar and center region at the user's normal window sizes and scaling; check controls, dragging, and available ring-group space.
- [ ] Record the observed selectors and supported conditions in design.md as implementation evidence, preserving the approved behavior.

Expected outcome: a concrete, verified adapter for the observed client rather than an assumption based solely on static bundle markers. Use temporary diagnostic work only inside ignored runtime storage.

Verification: visible conversation ID matches each selected conversation; home is unavailable; the centered component has usable space. If route identity, account alignment, debug startup, or placement cannot satisfy the specification, return to design review before proceeding to T-03. Obtain confirmation before changing the agreed design or requirements.

### T-03. Metric Calculations

- [ ] Implement finite-number validation, clamping, integer rounding, and exact 300/10080-minute window selection.
- [ ] Prefer the keyed Codex allowance bucket and handle missing, null, reordered, and partial window data.
- [ ] Calculate context remaining from the latest valid usage and its matching capacity, following the verified native formula.
- [ ] Calculate ring progress and continuous HSL color from the same raw percentage; keep unavailable distinct from valid 0%.

Expected file: `metrics.cjs`.

Verification: meaningful `node:test` cases cover conflicting quota buckets, distinct windows, partial data, null versus zero, latest versus cumulative usage, capacity validation, rounding, and color endpoints. Keep tests focused on data meaning and known failure modes.

### T-04. Data Readers

- [ ] Complete app-server request correlation, timeout, notification merging, account-change invalidation, and serialized refresh/retry behavior.
- [ ] Open the discovered state database read-only and use a parameterized ID-to-rollout lookup.
- [ ] Validate the target record's session ID and extract only required token metadata.
- [ ] Support chunked initial reading, partial trailing lines, incremental reads, truncation, and file replacement.
- [ ] Invalidate context after relevant compaction or model changes until corresponding statistics arrive.
- [ ] Clear unavailable data on failure and recover without modifying conversations, login configuration, or the index.

Expected file: `codex-data.cjs`.

Verification: use a synthetic SQLite index, synthetic JSONL records, and a stub stdio peer to verify ID mismatch, cumulative-usage exclusion, partial records, invalidation, notification deltas, failure recovery, and owned-child cleanup. Perform a sanitized real read for the selected conversation.

### T-05. Ring Rendering

- [ ] Mount a project-owned component at the verified top-bar location and center it against the whole client window.
- [ ] Render `5h`, `Weekly`, and `Context` rings with centered percentages, raw-value progress, theme-aware text, and the approved color transition.
- [ ] Represent valid 0% with a red state marker and unavailable data with a gray ring and `--`.
- [ ] Preserve existing pointer, button, and drag behavior; handle resize, scrolling, theme changes, and top-bar reconstruction.
- [ ] Make mounting idempotent and provide complete owned-component and observer cleanup.

Expected file: `renderer.js`.

Verification: inspect 100%, 75%, 50%, 25%, 0%, and unavailable states in the target client; inspect centering and control overlap at the observed dimensions. Record any limitations rather than declaring an untested layout supported.

### T-06. Scheduling and Lifecycle Integration

- [ ] Coordinate the data readers and renderer in `agent.cjs`.
- [ ] Detect conversation changes and clear context before starting a new read; reject responses for older conversation IDs or selection generations.
- [ ] Schedule 1-second conversation and record checks, 60-second allowance refresh, and the approved timeout and retry intervals without overlapping reads.
- [ ] Complete `manage.ps1` and `manage.cjs` with start, status, and stop operations backed by a user/project-scoped named pipe.
- [ ] Enforce one monitor, hide background consoles, attach to compatible existing CDP, and preserve active Codex sessions without debugging enabled.
- [ ] Recover from transient CDP loss and stop when the client exits. On explicit stop, remove the UI and terminate only owned background tasks while leaving Codex open.

Verification: repeated startup produces one component; rapid switching cannot display the previous conversation's value; a temporary data-source failure recovers; stop removes observers, timers, and owned processes. Status reports readiness and freshness without credentials or message bodies.

### T-07. Implementation Review and Documentation

- [ ] Run relevant syntax checks and focused automated tests; perform end-to-end checks on the local single-window setup.
- [ ] Measure context/switch latency and allowance refresh using sanitized timestamps; distinguish record availability time from token generation time.
- [ ] Update README.md with verified prerequisites, exact startup/status/stop commands, supported client conditions, CDP behavior, recovery, and path-relocation notes.
- [ ] Review logs and the change list for privacy, project scope, source attribution, and preserved client/login files.
- [ ] Summarize implementation results, checks, and remaining limitations for user review before entering acceptance.

Expected outcome: a working implementation and usable English documentation. An implementation check is not a claim that user acceptance or delivery has been approved.

## 4. Acceptance and Delivery Tasks

### T-08. Specification Acceptance

- [ ] After user confirmation to enter acceptance, evaluate AC-01 through AC-12 and record evidence and pass/fail status in an English acceptance record.
- [ ] Reuse implementation evidence where sufficient, and perform additional checks only for gaps or unresolved concerns.
- [ ] Ask the user to perform necessary manual conversation switches or normal client actions; keep existing conversations intact.
- [ ] Verify compaction and model-change behavior through focused fixtures and actual events when available; label live scenarios that remain unobserved.
- [ ] Resolve failed criteria within authorized scope or obtain confirmation of any proposed requirement/design revision.
- [ ] Present the acceptance result and await confirmation before delivery.

### T-09. Local Delivery

- [ ] After user confirmation to enter delivery, verify that the documented manual entry points work in the target environment.
- [ ] Hand off the runnable project and document how to stop monitoring and close the debugging endpoint through an ordinary Codex restart.
- [ ] Keep runtime artifacts ignored, record supported conditions and outstanding limitations, and present completion for user confirmation.

## 5. Acceptance Coverage

| Criteria | Primary tasks |
| --- | --- |
| AC-01, AC-02 | T-02, T-05, T-07, T-08 |
| AC-03, AC-07 | T-01, T-03, T-04, T-06, T-08 |
| AC-04, AC-05, AC-06 | T-02, T-03, T-04, T-06, T-08 |
| AC-08, AC-12 | T-03, T-04, T-05, T-06, T-08 |
| AC-09 | T-01, T-05, T-06, T-08 |
| AC-10 | T-04, T-07, T-08, T-09 |
| AC-11 | T-03, T-05, T-08 |

## 6. Review Status

Requirements, design, and this task plan are confirmed. Implementation is authorized within T-01 through T-07. Follow the feasibility gate in T-02 before proceeding to T-03, and record actual verification results as tasks progress.

### Implementation Evidence

- Runtime discovery selected existing Node.js v24.19.0 and codex-cli 0.162.0-alpha.17.2 without changing installed tools.
- The standalone allowance probe returned 300-minute and 10080-minute windows. Their used percentages were 55 and 29; the subsequent desktop read returned 56 and 29 during ongoing usage.
- The owned allowance server exited after the read. Six focused tests passed for initialization, request correlation, sanitized rejection, timeout cleanup, notification delivery, and CDP endpoint restrictions.
- PowerShell parsing and JavaScript syntax checks passed.
- An initial sandboxed CLI read failed with a configuration permission error. The approved execution outside that sandbox succeeded; this result does not require the user to run the launcher as an administrator.
- The start entry correctly returned SAVE_WORK_AND_FULLY_QUIT_CODEX_BEFORE_START while Codex was running without CDP, preserving the current session.
- The debugging startup and read-only inspection commands are ready. Live route identity, placement, and switching remain unverified until the user voluntarily reopens Codex through the launcher.
- T-03 and later tasks remain pending the explicit T-02 feasibility gate in this approved plan. Ring monitoring has not been implemented.
- Fixed the Windows PowerShell 5.1 saved-file launcher failure: native argument handling removed quotes from the JavaScript version expression, producing split(.) and a syntax error hidden by the broad catch. Discovery now parses node --version and management execution preserves native errors and exit codes.
- Verified the saved launcher against the real installation using Windows PowerShell 5.1 and PowerShell 7. All eight current tests passed, including two launcher regressions covering successful runtime selection and a failing management entry with exit code 7.
