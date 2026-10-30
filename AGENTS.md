# Project Types

## Windows Local Projects

Environment snapshot verified on 2026-10-28. Check the actual environment before compatibility or installation work and prefer reusing existing tools.

| Component | Configuration |
| --- | --- |
| Operating system | Windows 10 Pro 22H2, build 19045.6466, x64 |
| Default shell | PowerShell 7.6.4 |
| Git | 2.54.0.windows.1 |
| WSL | Software version 3.0.3.0, using the WSL 2 architecture |
| Docker Desktop | 4.97.0, using the WSL 2 backend |
| Docker Engine | 29.9.2 |
| Docker Compose | v5.6.1 |
| Docker installation directory | `D:\software\Docker` |
| Docker data directory | `D:\Data\DockerData` |
| Cloud container image target platform | `linux/amd64` |

## Cloud Server Projects

See the Cloud Deployment section for server access and deployment conventions.

## Mobile Applications

- Develop small Android applications for personal use, with compatibility across Android devices where practical
- Use Android 10 (API 29) as the default minimum supported version; adjust it when project requirements justify a different baseline
- Use the user's vivo X300 (V2509A, OriginOS 6) as a primary test device
- Verify the phone's Android version during development
- Provide an installation package for the user to verify compatibility on the phone; record the user's feedback


### Shared Android Development Tools

Environment snapshot verified on 2026-10-30. Check the actual environment before compatibility or installation work and reuse existing tools where practical.

The shared tools are installed under `D:\software\AndroidDev`:

- JDK 17, Gradle 8.13, and the Gradle dependency cache
- Android SDK command-line tools, Platform 36, Build Tools 35.0.0, and Platform Tools including ADB

Android Studio, the Android Emulator, and emulator system images are not installed.

# General Conventions

## Input Mapping

- Apply these mappings when the entire user input is the standalone keyword
- `start` means `inspect this project briefly`
- `end` means synchronize the current project to Git: inspect its changes, commit the relevant project changes, and push them to the remote repository; after synchronization completes, quit local Docker Desktop

## Development Defaults

- Develop projects locally by default
- Use a frontend web page as the default user interface
- Minimize implementation cost by choosing simple, direct solutions that meet the confirmed requirements
- Use the Spec-Driven Development workflow below for new projects and subsequent iterations

## Database Selection

- For local projects, prefer a database on the local computer; consider a server database when data must be shared across devices
- For cloud projects, prefer SQLite when it meets the requirements; consider the existing MySQL service when concurrent writes, shared access, or other needs make SQLite unsuitable
- Access remote data through a server application or a client/server database; avoid directly accessing SQLite files over a network share
- Persist cloud SQLite files outside disposable containers and arrange backups for persistent data according to its importance

## Spec-Driven Development Workflow

### Stages and Deliverables

Select all or a subset of the six stages according to the project's actual complexity and the user's instructions. By default, use only two steps: produce and confirm `spec.md`, then implement the code with relevant verification and documentation. Add separate technical design, task planning, acceptance, or delivery stages when the project needs them or the user explicitly requests them. State the selected workflow and its rationale before proceeding.

Produce and present the deliverables for one selected stage at a time. Wait for explicit human confirmation before entering the next selected stage. Approval to create or revise a document authorizes only that document change; implementation requires confirmation of the specification and explicit development authorization, plus confirmation of any additional pre-implementation stages selected for the project.

| Stage | Purpose | Deliverables | Completion Gate |
| --- | --- | --- | --- |
| 1. Requirements | Define the problem, intended behavior, scope, and success criteria | `spec.md` containing goals, scope, scenarios, functional behavior, constraints, acceptance criteria, and open questions | User confirms the requirements version and authorizes the next selected stage |
| 2. Technical Design | Determine how to satisfy the confirmed requirements | `design.md` containing the technical approach, module responsibilities, data flow, interfaces, key decisions, feasibility findings, and verification strategy | User confirms the design and authorizes the next selected stage |
| 3. Task Planning | Define implementation order and reviewable outcomes | `tasks.md` containing tasks, dependencies, expected outcomes, verification methods, and completion status | User confirms the implementation scope and explicitly authorizes development |
| 4. Implementation | Build the confirmed scope | Source code, necessary tests, configuration examples, and synchronized documentation | Relevant checks pass and the user confirms completion or authorizes the next selected stage |
| 5. Acceptance | Verify the implementation against the confirmed specification | Acceptance results with evidence for each criterion, outstanding items, and known limitations | User confirms acceptance and authorizes the next selected stage or completion |
| 6. Delivery and Feedback | Make the result usable and maintainable in its target environment | A runnable version or release package, `README.md`, and applicable installation, operation, update, and rollback instructions | Target-environment verification passes and the user confirms delivery |

### Document Responsibilities and Review

- Use `AGENTS.md` for stable development rules and `spec.md` for project-specific requirements and acceptance criteria
- Use `spec.md` to describe expected behavior and user-specified constraints; use `design.md` to describe implementation choices; use `tasks.md` to track implementation work
- For a new project, create and review `spec.md` first; iterate on it until the user explicitly confirms the requirements version before entering the next selected stage
- Summarize proposed document changes and obtain human confirmation before writing them; after writing, present the actual deliverable for review
- Keep unresolved questions and unverified assumptions explicit; resolve decisions needed by the next stage before requesting transition approval
- Scale documentation to project complexity; in the default two-step workflow, include necessary implementation notes in `spec.md` and keep verification and delivery within implementation; create separate documents only for selected stages that need them
- Treat each confirmation as approval of the stated content and next action; complete work within that authorization and obtain confirmation before expanding its scope

### Iterations and Changes During Development

- For a feature iteration or a change to expected behavior, first identify the affected `spec.md` sections, proposed changes, reasons, and impact; obtain confirmation before updating the specification
- Present the revised specification for confirmation, then update and review any affected design or task documents included in the selected workflow before requesting development authorization
- If investigation or implementation reveals an infeasible requirement or a conflicting constraint, return to the affected requirements or design stage and obtain confirmation of the revised deliverable before continuing dependent work
- For a defect where the implementation deviates from the confirmed specification, explain the root cause and proposed fix, obtain confirmation before modifying the implementation, and verify against the existing acceptance criteria; revise the specification when expected behavior changes
- Keep all selected deliverables consistent; verify against the confirmed requirements version even when acceptance and delivery are included within implementation

## Project Structure

- Develop new projects on the `main` branch by default and place their directories under `projects/`
- Keep project directories stable when their status changes; use relative paths or runtime path discovery where practical
- Name all project directories, including placeholder directories, using `YYYYMMDD_<name>`
- Each Python project must maintain its own `.venv/` directory and `requirements.txt` file
- Each project must include a `README.md` describing its purpose, setup, and startup steps
- Use a `deliverables/` directory in each project for the key files and startup instructions needed to use or run the project
- Include applicable deliverables such as APKs, executable files, and startup scripts; keep intermediate build files and other process files outside this directory

## Documentation

- Write all deliverables in English, including specifications, designs, task plans, README files, code comments, user-facing text, configuration examples, and verification or delivery reports
- Use the root README to index projects with links, brief descriptions, and statuses
- Keep project features, setup, and startup instructions in each project's own README
- When project functionality, setup, or startup steps change, update the project's README and relevant parent-directory README entries

# Project Status Management

## Project Statuses

- `doing` identifies projects under active development
- `hold` identifies projects temporarily suspended, with their work and context preserved for a possible restart
- `done` identifies projects whose current version is complete

## Status Transitions

- Start new projects with `doing` status; change suspended projects to `hold` after user confirmation
- Change a resumed project from `hold` to `doing` after user confirmation, then review its existing specification and remaining work
- Change a completed project to `done` after user confirmation; change it back to `doing` when a confirmed iteration begins
- Confirm the intended status with the user before any other transition

## Updating Project Status

- Update the root project index and preserve project files, dependencies, and progress when changing status
- On completion, remove temporary files and test files; preserve functionality, virtual environments, and dependencies

# Large Language Models

## Provider and Model Selection

- For work involving large language models, first read `D:\personal\codex\.secrets\README.md` and select the provider and exact API model ID that best fit the project's requirements
- Prefer the default provider and its default model when they meet the requirements; when another choice is needed, prefer a lower-cost model that meets the required quality, capabilities, and API compatibility
- After selecting the provider and model, read the required settings from `D:\personal\codex\.secrets\llm.env`; use `LLM_DEFAULT` and `<PROVIDER>_DEFAULT_MODEL` to resolve defaults
- Keep project-specific selections in the project and preserve centralized defaults unless the user explicitly confirms changing them

## Shared Cloud Model Configuration

- Store shared model configuration on the cloud server in `/home/ubuntu/.config/llm.env`; have each Docker Compose project reference this file through `env_file`
- Manage this configuration separately from project deployments; preserve the existing file when uploading or updating a project and keep credentials outside source code and container images
- Load configuration into the container environment when creating the container; running containers retain their existing configuration until explicitly recreated
- After updating the shared file, apply the changes only to the projects that need them by running `docker compose up -d --no-build --force-recreate <service>` from each project's deployment directory; this recreates the container using the existing image and briefly interrupts the service
- Use container recreation to refresh environment variables; `docker compose restart` retains the existing environment
- Preserve explicit project-specific provider and model selections when refreshing shared configuration; projects using shared defaults adopt changed defaults when their containers are recreated

# Cloud Deployment

## Server Access and Maintenance

- For work involving a server, first read `D:\personal\codex\.secrets\README.md`, select the server that best fits the project, and prefer the documented default server when suitable
- Connect to the selected server using the SSH alias, existing key, and host verification procedure documented in that README
- Use SSH key authentication by default; read or use `D:\personal\codex\.secrets\cloud.env` only when the user explicitly requests it
- Follow the existing human-confirmation process before modifying the server
- Design cloud deployments for easy maintenance of files expected to change independently, such as prompts and configuration. Use external files or mounts where appropriate, and document their locations, update procedures, and the reload, restart, or container recreation required to apply changes

## Application Access

- Develop projects without application login or authentication by default; add login or authentication when explicitly requested
- For user-facing Web services deployed to the cloud, provide direct access through the server's public IP address or domain by default and allow all source IP addresses without IP allowlists or blocklists
- Bind the deployed service to the required public-facing interface and permit its required service ports through the host and cloud firewalls; open only the ports needed by the service
- Use SSH tunnels for application access when explicitly requested
- Verify the public access URL after deployment and document the address and access method in the project's README

## Container Development and Deployment

### Default: Local Build and Test, Cloud Runtime

- Before using local Docker, check that Docker Engine is ready; if it is not ready, start the engine through the current installation's startup mechanism and wait for readiness. In the current Windows Docker Desktop installation, start Docker Desktop in the background to prepare the WSL 2 backend and Docker Engine
- Use Docker CLI commands for Docker operations; the CLI runs on demand and requires no separate startup or shutdown. Docker Desktop can run in the background without interaction with its graphical interface
- Use this default workflow: develop locally, build a Linux container image for the target server architecture, test that image locally, assign a version tag, export and upload the image, then import, configure, and run it on the cloud server
- Complete runtime and dependency installation during the local image build; use the cloud server to import and run the prepared image

### Alternative: Cloud Build, Test, and Runtime

- Use this workflow when explicitly selected for the project: develop locally, upload source code and build files, build a version-tagged image on the cloud server, verify it in a separate test container, then deploy the tested image
- Operate the server's Docker CLI and Engine through SSH; local Docker installation is optional for this workflow
- Before building and testing, check available server CPU, memory, and disk resources and assess the impact on existing services; use separate test container names and ports to preserve running services during verification

### Shared Requirements

- Build for `linux/amd64` when targeting the current default server; package the application, runtime, and dependencies in the image and keep the local Windows `.venv` on the development computer
- Deploy the same image that passed testing in the selected workflow
- Keep shared model configuration, credentials, and independently maintained files such as prompts outside the image; apply the documented environment injection or file mounts when starting the container
- Retain identifiable image versions for rollback and verify container health and the project's core functionality after deployment
