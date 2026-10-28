# Translator

An English/Chinese translation and vocabulary assistant with Gradio Web and CLI interfaces. It reuses the original prompt from `20260626_translator_agent` and includes Docker deployment files.

## Features

- English words: Chinese meaning, American pronunciation, etymology, meaning evolution, and related vocabulary
- English phrases and sentences: Chinese translation and context
- Chinese words: natural American English equivalents and usage guidance
- Chinese sentences and paragraphs: English translation and translation strategy
- Independent requests: the web interface displays conversation history but sends only the original system prompt and current input to the model

Translation requires an internet connection, an OpenAI-compatible Chat Completions API, valid credentials, and an available API balance. Blank input is rejected before a request; errors are shown briefly without credentials or raw responses.

## Local Setup

Use Python 3.14 and the project's own `.venv`. The existing environment was preserved when the project moved from `archive/`. Use its Python executable directly; rebuild only if a path problem is confirmed.

For a fresh installation, open PowerShell in this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Direct dependencies are pinned to the already installed local versions: `openai==1.109.1`, `gradio==6.30.0`, and `python-dotenv==1.2.4`. Container builds install Linux dependencies afresh; transitive dependencies are not locked.

## Model Configuration

Select the provider and model using [the central configuration guide](D:/personal/codex/.secrets/README.md). Prefer the configured default when suitable: currently `DEEPSEEK` with `deepseek-flash`. This project preserves centralized defaults.

On Windows, the application reads `D:\personal\codex\.secrets\llm.env`. Process environment variables override that file. On Linux, including the container, configuration comes from process environment variables; the Windows credential path is not accessed.

| Variable | Purpose |
|---|---|
| `LLM_DEFAULT` | Required provider identifier matching the variable prefix |
| `<PROVIDER>_API_KEY` | Required API authentication key |
| `<PROVIDER>_BASE_URL` | Required OpenAI-compatible API base URL |
| `<PROVIDER>_DEFAULT_MODEL` | Required API model ID |
| `GRADIO_SERVER_NAME` | Web listening address, defaults to `127.0.0.1` locally and is set to `0.0.0.0` in the image |

For the default provider, provide `LLM_DEFAULT`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, and `DEEPSEEK_DEFAULT_MODEL`. Keep credentials in the central configuration or protected server configuration below. Missing settings are reported by variable name. Restart the local app after changing its configuration; apply cloud configuration updates using container recreation as described below.

### Shared Cloud Model Configuration

Use `/home/ubuntu/.config/llm.env` as the shared cloud configuration file. Multiple projects reference this same file through Compose `env_file`, avoiding separate copies of model credentials in each project. Manage the file independently of project deployments and preserve its existing contents when uploading or updating this project.

Compose reads the file when creating a container and injects all its variables into that container's environment, including settings for other providers. Running containers retain their existing environment. Newly added or changed variables become available to a project when its container is created or recreated.

After updating the shared file, run the following command from `/opt/translator` when this project needs the new configuration:

```bash
docker compose up -d --no-build --force-recreate translator
```

This briefly interrupts the service and recreates its container using the existing image, without rebuilding the image or reinstalling dependencies. `docker compose restart` retains the old environment and does not refresh model configuration. Other projects using the shared file must recreate their own affected service containers when they need an update; adding a provider alone does not require restarting projects that do not use it. Preserve explicit project-specific selections; projects using shared defaults adopt changed defaults when recreated.

## Local Startup

Start the web interface:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:7860>. Press `Ctrl+C` to stop the server.

Start CLI mode:

```powershell
.\.venv\Scripts\python.exe app.py --cli
```

Enter one input per line and `exit` to quit. In web mode, `exit` is translation input according to the original prompt. The container starts in web mode with Gradio sharing disabled.

## Updating the Translation Prompt

The application reads `translator_agent_prompts.md` once at startup. Local Web and CLI sessions use the file beside `app.py`; restart the application after editing it.

Compose mounts the file from the deployment directory onto `/app/translator_agent_prompts.md` as a read-only bind mount. After deployment, edit that server-side file and run the following command from `/opt/translator`:

```bash
docker compose restart translator
```

The restarted process loads the updated prompt without rebuilding the image. Keep the source file readable by the container's non-root user. Compose requires the existing source file and will report a missing file instead of creating a directory in its place. Keep the local prompt and deployed prompt synchronized when uploading changes. Application or dependency changes still require an image rebuild.

## Container Build and Server Deployment

### Current Deployment

Deployed and verified on 2026-10-28 on the default server at `/opt/translator`, using image `translator:20261028-1`. Local container testing and the deployed service both passed HTTP and real translation checks. The service was healthy, used approximately 177 MiB of memory at verification, and retained the existing shared model configuration. MySQL remained active. The previous deployment files are backed up in `/opt/translator/backups/before-20261028-1.tar`.

The service publishes port 7861 on all server IPv4 interfaces and is accessed directly at <http://122.51.135.229:7861/>. It allows all source IP addresses and has no application login, IP allowlist, or IP blocklist. This public service is separate from the local Python application on port 7860. Translation requests made by visitors use the configured model account.

Public access verified on 2026-10-28: the container publishes `0.0.0.0:7861:7860`, and the Tencent Cloud Lighthouse firewall allows inbound TCP 7861 from `0.0.0.0/0`. Existing cloud firewall rules were preserved. Direct requests from the development computer to <http://122.51.135.229:7861/> passed HTTP 200 and a real translation check without an SSH tunnel. The application has no login verification or IP access restrictions.

### Deployment Workflow

Build and test the Linux image locally, then export and upload that same version for the server to import and run. The default server is `TENCENT_LIGHTHOUSE_01` (`tencent-server`), with deployment files in `/opt/translator`. Use the existing SSH key and strict host verification from the central configuration guide. Access `cloud.env` only when explicitly requested.

The Compose service uses `translator:20261028-1`, targets `linux/amd64`, runs as a non-root user, and publishes `0.0.0.0:7861:7860`. Access the service through its public URL. The image includes the runtime and Linux dependencies; the server does not build the image or install Python packages. Keep the Windows `.venv` local.

### Build and Test Locally

From this project directory in PowerShell:

```powershell
docker build --platform linux/amd64 -t translator:20261028-1 .
@'
import os
import subprocess
from pathlib import Path
from dotenv import dotenv_values

config = dotenv_values(r"D:\personal\codex\.secrets\llm.env")
provider = config["LLM_DEFAULT"]
keys = ["LLM_DEFAULT"] + [f"{provider}_{name}" for name in ("API_KEY", "BASE_URL", "DEFAULT_MODEL")]
env = os.environ.copy()
args = ["docker", "run", "-d", "--name", "translator-local-check", "--platform", "linux/amd64",
        "-p", "127.0.0.1:7862:7860", "--mount",
        f"type=bind,source={Path.cwd() / 'translator_agent_prompts.md'},target=/app/translator_agent_prompts.md,readonly"]
for key in keys:
    env[key] = config[key]
    args += ["--env", key]
subprocess.run(args + ["translator:20261028-1"], env=env, check=True)
'@ | .\.venv\Scripts\python.exe -
```

Parse the central file with dotenv before forwarding environment variables: Docker CLI `--env-file` retains quote characters in values, while dotenv and Compose `env_file` interpret quoted values. The command above passes variable names to Docker and keeps credential values out of command arguments.

Check container health and a small translation at <http://127.0.0.1:7862> before deploying. This makes a billable model request. Remove the test container after testing:

```powershell
docker rm -f translator-local-check
docker save -o "$env:TEMP\translator-20261028-1.tar" translator:20261028-1
```

Use a new version tag for subsequent application or dependency changes, and update the Compose image tag accordingly. Retain the previous image and matching deployment files for rollback.

### Import and Run on the Server

Check resources and port 7861 before starting. Permit inbound TCP port 7861 from `0.0.0.0/0` through any active host firewall and the Tencent Cloud Lighthouse firewall; preserve unrelated firewall rules. Upload the image archive, `compose.yaml`, `translator_agent_prompts.md`, and this README to `/opt/translator` using the existing SSH identity. Preserve `/home/ubuntu/.config/llm.env`; never include credentials, SSH keys, or the Windows virtual environment in the image or deployment archive. The shared configuration must contain the selected provider's required settings and retain owner-only permissions.

From `/opt/translator` on the server:

```bash
docker load -i translator-20261028-1.tar
docker compose config --quiet
docker compose up -d --no-build --pull never translator
docker compose ps
```

Verify HTTP health and a small translation using the shared server configuration. Remove the uploaded image archive after a successful import and verification to reclaim disk space; retain the imported versioned image. Use `config --quiet` because expanded configuration can expose credentials. Review logs locally and redact sensitive information before sharing them. The service restarts unless explicitly stopped and rotates its logs.

### Access and Maintenance

Open <http://122.51.135.229:7861/> directly from a browser. The default deployment uses HTTP, allows all source IP addresses, and has no login verification. An SSH tunnel is unnecessary for public access. Keep the host and cloud firewall rules for TCP port 7861 consistent with this deployment.

To change the published port or interface, update `compose.yaml` and run `docker compose up -d --no-build --pull never translator`. This recreates the container using the existing image; a restart alone does not apply port mapping changes. Verify both the public URL and container health afterward.

Manage this Compose project from `/opt/translator`:

```bash
docker compose restart translator
docker compose down
```

Prompt updates require a restart; shared environment updates require container recreation as described above. For application updates, import the next tested image, update the Compose image tag, and run `docker compose up -d --no-build --pull never translator`. To roll back, restore the previous image tag and matching prompt, then run the same command.

## Files

| File | Purpose |
|---|---|
| `app.py` | Translation function and Web/CLI entry points |
| `translator_agent_prompts.md` | Original translation prompt, mounted read-only for updates followed by a restart |
| `requirements.txt` | Direct dependency versions |
| `Dockerfile` | Linux Python runtime, non-root user, and HTTP health check |
| `compose.yaml` | Separate service, protected runtime configuration, prompt mount, public port, and log rotation |
| `.dockerignore` | Build context allowlist |
