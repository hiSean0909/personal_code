# Codex Status Bar Specification

- Version: v1.1, confirmed requirements with an English editorial update
- Created: 2026-10-29
- Current stage: requirements, design, and tasks confirmed; implementation feasibility checks in progress
- Project directory: `doing/20261029_codex_status_bar`
- Reference: [Lorie7813/codex-usage-card](https://github.com/Lorie7813/codex-usage-card)

## 1. Goal and Selected Workflow

Show account allowance and current-conversation context remaining in the center of the Codex desktop application's top bar on the user's Windows computer.

The repository defaults to two steps: confirm a specification, then implement with verification and documentation. This project retains the expanded six-stage workflow because it integrates with internal desktop interfaces and the user explicitly requested design review and task planning. Produce one selected stage's deliverables, obtain confirmation, then proceed to the next selected stage. Implementation requires confirmation of the task plan and explicit development authorization.

All deliverables, including documents, code comments, interface labels, and operational messages, use English.

## 2. Confirmed Requirements

| ID | Requirement |
| --- | --- |
| R-01 | Develop for the user's local Windows environment, using the reference project as inspiration |
| R-02 | Keep the status display fixed at the center of the top bar |
| R-03 | Show remaining 5-hour allowance, weekly allowance, and current-conversation context percentages from left to right |
| R-04 | Create the project under doing as 20261029_codex_status_bar using the current date |
| R-05 | Follow the selected workflow and obtain user confirmation before entering each subsequent selected stage; retain design and task planning for this project |
| R-06 | Use ring icons with percentages in their centers; colors move from green through yellow to red as remaining capacity decreases from 100% to 0% |
| R-07 | Write all project deliverables in English |

## 3. Release Behavior

### 3.1. Placement and Appearance

- Interpret the top bar as the bar inside the Codex application window, centered against the entire client-window width.
- Arrange three ring icons horizontally, each with a centered percentage. Short labels identify `5h`, `Weekly`, and `Context`.
- Ring arc length represents remaining capacity: a full arc at 100% and zero progress at 0%. The central percentage remains readable.
- Change the icon color continuously from green at 100%, through yellow at 50%, to red at 0%. Exact color values belong in the technical design.
- Keep the display centered when the window moves or resizes, and fixed when conversation content scrolls.
- Preserve existing top-bar controls and window dragging. Support the user's normal window sizes, display scaling, and light and dark themes.
- Include the rings and centered percentages in the first release. Additional charts and interactive actions require a later requirements discussion.

### 3.2. Metric Semantics

| Metric | Meaning | Data requirement |
| --- | --- | --- |
| 5h | Remaining allowance in the signed-in account's 5-hour window | Identify the actual window and convert used percentage into remaining percentage |
| Weekly | Remaining allowance in the signed-in account's weekly window | Identify the actual window and convert used percentage into remaining percentage |
| Context | Remaining capacity in the effective context window for the conversation currently visible in this window | Use that conversation's latest valid context statistics and corresponding window capacity |

- Display valid percentages as integers from 0% to 100%, rounded to the nearest integer.
- Account allowance is shared across conversations using the same account. Context follows the currently visible conversation.
- Use statistics that describe current context occupancy. Historical cumulative token consumption serves a different purpose and must not be used directly as current occupancy.
- After context compaction or a model change, update the percentage when corresponding new statistics become available.
- Context represents the latest valid statistics. Available data determines refresh granularity during streaming; the design must describe that boundary.

### 3.3. Refresh, Switching, and Unavailable Data

- Read the metrics automatically on startup and refresh while running.
- Actively refresh account allowance every 60 seconds and apply relevant data-source notifications when available.
- Update context within 5 seconds after new context statistics become available. After a conversation switch, show that conversation's data or an unavailable state within 5 seconds.
- Clear the previous conversation's context value when switching, before applying the target conversation's data.
- Show `--` for a new conversation without statistics, missing statistics, a failed read, or an unidentified active conversation.
- Show `--` in a neutral gray ring when data is unavailable.
- Mark affected metrics unavailable after a read failure and retry automatically. Preserve other valid metrics.
- When no conversation is open, show context as `--` while continuing to show account allowance.

### 3.4. Start and Stop

- Provide explicit manual start, status, and stop entry points.
- If startup requires reopening Codex, the user saves work and quits voluntarily before using the startup entry point. Preserve ongoing work.
- Repeated startup keeps exactly one metric group per target window.
- Stopping removes the tool's interface and ends its background tasks while leaving Codex open.
- Validate the first release with one Codex main window. Discuss multiple-window support separately.

## 4. Scope and Constraints

- Target the user's Windows computer and installed Codex desktop application. Record the compatibility version during design and acceptance.
- Preserve installed application files, signatures, and existing login configuration. Explain runtime behavior, data sources, and required permissions in the design.
- Reuse existing tools and runtimes. Explain and obtain confirmation before adding dependencies or changing the environment.
- Resolve project files relative to the scripts or at runtime so the project can later move from doing to archive.
- Keep operational data local. Record only necessary operational status in logs and keep credentials and message bodies private.
- Include top-bar display, metric reads, automatic refresh, and manual lifecycle management in the first release. Sign-in startup, automatic updates, cloud deployment, account management, and quota-reset actions require separate scope confirmation.
- Establish reference-code reuse and applicable license obligations during design.

## 5. Acceptance Criteria

These criteria define the confirmed behavior. Runtime acceptance has not been performed.

| ID | Scenario | Pass condition |
| --- | --- | --- |
| AC-01 | Start with a conversation open | Three horizontal rings appear at the top center with centered percentages in R-03 order |
| AC-02 | Move or resize the window and scroll the conversation | Placement remains correct and existing top-bar operations remain usable |
| AC-03 | Check account allowance | Both values match authoritative reads for the same account and windows, allowing refresh delay and integer rounding |
| AC-04 | Check context | The value uses the visible conversation's valid statistics and matching capacity, with a verified calculation basis |
| AC-05 | Switch between conversations with different context statistics | Within 5 seconds show the target data or --, clearing the previous conversation's value during the switch |
| AC-06 | New context statistics or compaction | Apply the corresponding new statistics within 5 seconds of their availability |
| AC-07 | Account allowance changes | With successful reads, update during the 60-second active refresh cycle or earlier through notifications |
| AC-08 | New conversation, no conversation, or failed metric read | Affected metrics show --, other valid metrics remain readable, and recovered reads update automatically |
| AC-09 | Repeated start and stop | Exactly one group appears per target window; stopping removes the group and owned background processes while keeping Codex open |
| AC-10 | Inspect logs and modification scope | Privacy constraints are met and application files and login configuration remain intact |
| AC-11 | Check ring progress and colors | Arc length represents remaining capacity; colors transition continuously from green at 100% through yellow at 50% to red at 0%, with readable central text at 0% |
| AC-12 | Check unavailable appearance | A gray ring with -- is distinguishable from a valid red 0% state |

## 6. Confirmed Decisions

| ID | Decision | Confirmed value |
| --- | --- | --- |
| Q-01 | Top bar and centering reference | Internal Codex top bar, horizontally centered against the entire client window |
| Q-02 | Continuous color transition and midpoint | Green at 100%, yellow at 50%, red at 0% |
| Q-03 | Refresh timing | Account allowance every 60 seconds; conversation switching and new context statistics within 5 seconds |
| Q-04 | First-release startup and window scope | Manual startup and single-window acceptance; discuss sign-in startup and multiple windows later |
| Q-05 | Deliverable language and stage selection | English deliverables; complexity-based stage selection, retaining this project's explicitly requested design and task reviews |

## 7. Technical Questions Carried into Design

- Account allowance has been read successfully in this chat; an independently running tool still needs a verified read path.
- The current conversation's records contain recent token usage and context-window capacity. Verify the calculation against native client behavior.
- Reliable identification of the visible conversation, switch detection, and actual top-bar mounting require verification.
- The reference project's debugging connection has not been enabled and Codex has not been restarted with debugging parameters.
- Address these questions through design and subsequent authorized verification. Return to requirements review if limitations affect confirmed behavior.

## 8. Review History

| Version | Status | Notes |
| --- | --- | --- |
| v0.1 | Superseded | Initial requirements draft |
| v0.2 | Confirmed | User approved the rings, centered percentages, and corresponding acceptance criteria |
| v1.0 | Requirements baseline | Recorded approval without changing v0.2 behavior |
| v1.1 | English update | User requested English deliverables and adaptive stage selection, confirmed the design, and requested task planning; product behavior remains unchanged |
