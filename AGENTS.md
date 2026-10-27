# Agent Guide

## Project Structure

- Name all project directories, including placeholder directories, using `YYYYMMDD_<name>`
- Each Python project must maintain its own `.venv/` directory and `requirements.txt` file
- Each project must include a `README.md` describing its purpose, setup, and startup steps

## Large Language Models

- For scenarios involving large language models, use `LLM_DEFAULT` from `D:\personal\codex\.secrets\llm.env` as the default provider selector

## Documentation

- Write all README files in English
- At every directory level, index README files must describe only the immediate subdirectories, using links and brief descriptions
- Keep project features, setup, and startup instructions in each project's own README
- When project functionality, setup, or startup steps change, update the project's README and relevant parent-directory README entries

## Project Archive

- When moving a project from `doing/` to `archive/`, remove temporary files and test files
- Update the project listings in `doing/README.md` and `archive/README.md`
- Keep archiving limited to moving the project directory, removing temporary and test files, and updating README listings
- Preserve the existing virtual environment and dependencies during archiving; rebuild them only when a confirmed path issue requires it
- Verify the destination and README links; run functional checks only when code changes or an observed issue requires them

## Cloud Server

- Provider: Tencent Cloud Lighthouse
- Resources: 2 vCPUs, 2 GB RAM, 40 GB system disk
- Operating system: Ubuntu Server 22.04 LTS 64-bit
- IPv4: 122.51.135.229
- IPv6: Disabled
- Connection method
  - Username and password
    - Username: ubuntu
    - Password: Read `TENCENT_LIGHTHOUSE_01_PASSWORD` from `D:\personal\codex\.secrets\cloud.env`
  - Terminal connection (SSH): Not configured
