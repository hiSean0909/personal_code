# Agent Guide

## Input Mapping

- Apply these mappings when the entire user input is the standalone keyword
- `start` means `inspect this project briefly`
- `end` means synchronize the current project to Git: inspect its changes, commit the relevant project changes, and push them to the remote repository; after synchronization completes, quit local Docker Desktop

## Local Development Environment

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

## Development Defaults

- Develop projects locally by default
- Use a frontend web page as the default user interface
- Minimize implementation cost by choosing simple, direct solutions that meet the confirmed requirements
- Use Spec-Driven Development by default: define requirements and acceptance criteria first, obtain human confirmation before implementation, and verify the result against the specification

## Project Structure

- Develop new projects on the `main` branch by default and place their directories under `doing/` by default
- While developing in `doing/`, prepare projects for a later move to `archive/`: use relative paths or runtime path discovery for project files, identify external startup entries that require relocation, and minimize the files that need changes during archiving
- Name all project directories, including placeholder directories, using `YYYYMMDD_<name>`
- Each Python project must maintain its own `.venv/` directory and `requirements.txt` file
- Each project must include a `README.md` describing its purpose, setup, and startup steps

## Application Access

- Develop projects without application login or authentication by default; add login or authentication when explicitly requested
- For user-facing Web services deployed to the cloud, provide direct access through the server's public IP address or domain by default and allow all source IP addresses without IP allowlists or blocklists
- Bind the deployed service to the required public-facing interface and permit its required service ports through the host and cloud firewalls; open only the ports needed by the service
- Use SSH tunnels for application access when explicitly requested
- Verify the public access URL after deployment and document the address and access method in the project's README

## Large Language Models

- For work involving large language models, first read `D:\personal\codex\.secrets\README.md` and select the provider and exact API model ID that best fit the project's requirements
- Prefer the default provider and its default model when they meet the requirements; when another choice is needed, prefer a lower-cost model that meets the required quality, capabilities, and API compatibility
- After selecting the provider and model, read the required settings from `D:\personal\codex\.secrets\llm.env`; use `LLM_DEFAULT` and `<PROVIDER>_DEFAULT_MODEL` to resolve defaults
- Keep project-specific selections in the project and preserve centralized defaults unless the user explicitly confirms changing them

### Shared Cloud Model Configuration

- Store shared model configuration on the cloud server in `/home/ubuntu/.config/llm.env`; have each Docker Compose project reference this file through `env_file`
- Manage this configuration separately from project deployments; preserve the existing file when uploading or updating a project and keep credentials outside source code and container images
- Load configuration into the container environment when creating the container; running containers retain their existing configuration until explicitly recreated
- After updating the shared file, apply the changes only to the projects that need them by running `docker compose up -d --no-build --force-recreate <service>` from each project's deployment directory; this recreates the container using the existing image and briefly interrupts the service
- Use container recreation to refresh environment variables; `docker compose restart` retains the existing environment
- Preserve explicit project-specific provider and model selections when refreshing shared configuration; projects using shared defaults adopt changed defaults when their containers are recreated

## Documentation

- Write all README files in English
- At every directory level, index README files must describe only the immediate subdirectories, using links and brief descriptions
- Keep project features, setup, and startup instructions in each project's own README
- When project functionality, setup, or startup steps change, update the project's README and relevant parent-directory README entries

## Project Archive

- When moving a project from `doing/` to `archive/`, remove temporary files and test files
- Update the project listings in `doing/README.md` and `archive/README.md`
- Preserve the same project functionality and behavior after archiving as before archiving; update path-dependent startup entries and configuration as needed
- Keep archiving limited to moving the project directory, removing temporary and test files, updating relevant README files, and making the path adaptations necessary to preserve functionality
- Preserve the existing virtual environment and dependencies during archiving; rebuild them only when a confirmed path issue requires it
- Verify the destination and README links; run functional checks only when code changes or an observed issue requires them

## Cloud Server

- For work involving a server, first read `D:\personal\codex\.secrets\README.md`, select the server that best fits the project, and prefer the documented default server when suitable
- Connect to the selected server using the SSH alias, existing key, and host verification procedure documented in that README
- Use SSH key authentication by default; read or use `D:\personal\codex\.secrets\cloud.env` only when the user explicitly requests it
- Follow the existing human-confirmation process before modifying the server
- Design cloud deployments for easy maintenance of files expected to change independently, such as prompts and configuration. Use external files or mounts where appropriate, and document their locations, update procedures, and the reload, restart, or container recreation required to apply changes

### Container Development and Deployment

- When local Docker is needed, check the engine status first; if it is not running, start Docker Desktop in the background and wait for the engine to become ready before continuing
- Use this default workflow: develop locally, build a Linux container image for the target server architecture, test that image locally, assign a version tag, export and upload the image, then import, configure, and run it on the cloud server
- Build for `linux/amd64` when targeting the current default server; package the application, runtime, and dependencies in the image and keep the local Windows `.venv` on the development computer
- Deploy the same image that passed local testing; use the cloud server to import and run the prepared image, with runtime and dependency installation completed during the local image build
- Keep shared model configuration, credentials, and independently maintained files such as prompts outside the image; apply the documented environment injection or file mounts when starting the container
- Retain identifiable image versions for rollback and verify container health and the project's core functionality after deployment
