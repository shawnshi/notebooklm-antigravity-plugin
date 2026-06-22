---
name: notebooklm-core
description: Antigravity-native skill for Google NotebookLM. Automates research, notebook management, and multimodal content generation (podcasts, videos, slide decks).
---

# NotebookLM Core Automation

This skill provides a native Antigravity interface to Google's NotebookLM, allowing you to orchestrate complex research pipelines, import sources, and generate various multimodal artifacts.

## <RULE: SECURITY_GATE>
**CRITICAL SECURITY ENFORCEMENT**: You MUST NEVER execute `auth_bridge.py login` or extract browser cookies without explicit user consent. If authentication is missing, you must halt execution and use the `/grill-me` or standard chat response to ask the user to manually run the login command.

## Architecture & Coordination

All commands execute via isolated Python scripts located in `scripts/`.
The Python environment for this skill is managed in `scripts/.venv/`.

**Mandatory Orchestration Rules**:
1. For quick tasks (create notebook, list, status): Execute the script synchronously.
2. For long tasks (audio, video, deep research): You MUST use the `daemon_watchdog.py` background task rather than looping or polling.

## <RULE: VECTOR_LAKE_SYNC> (Two-Way Mapping)
When you create a Notebook using `notebook_bridge.py create`, you MUST:
1. Ensure the Concept does not already exist via the `check_duplicate_entity` skill.
2. Create or map a node in the local Vector Lake graph using the `memory_update` skill, attaching the Notebook ID as metadata.
3. Any textual artifacts generated from NotebookLM (like Study Guides or Summaries) must be synced into the local graph.

## <RULE: ARTIFACT_ROUTING> (Media Handling)
When downloading Audio or Video outputs from `generate_bridge.py`, you MUST NOT simply leave the raw `.wav`/`.mp4` in the `scratch/` directory.
You MUST create an Antigravity Artifact `.md` file in the `brain/<conversation-id>` directory that embeds the absolute path of the downloaded media using markdown syntax: `![Podcast Audio](file:///absolute/path/to/audio.wav)`, so it can be natively played in the UI.

## Available Adapter Scripts

Located in `config/plugins/notebooklm/skills/notebooklm-core/scripts/`:

### 1. `auth_bridge.py`
```bash
.\.venv\Scripts\python.exe auth_bridge.py check
.\.venv\Scripts\python.exe auth_bridge.py login
```

### 2. `notebook_bridge.py`
```bash
.\.venv\Scripts\python.exe notebook_bridge.py create "My Research"
.\.venv\Scripts\python.exe notebook_bridge.py add-source <nb_id> <url>
.\.venv\Scripts\python.exe notebook_bridge.py research <nb_id> <query> <mode>
```

### 3. `generate_bridge.py`
```bash
.\.venv\Scripts\python.exe generate_bridge.py audio <nb_id> [instructions]
.\.venv\Scripts\python.exe generate_bridge.py slide-deck <nb_id>
.\.venv\Scripts\python.exe generate_bridge.py status <nb_id>
.\.venv\Scripts\python.exe generate_bridge.py download <nb_id> <task_id> <type> <output_path>
```

### 4. `daemon_watchdog.py` (Event-Driven Waiter)
Use this script via Antigravity `run_command` in the background to automatically wake you up when a long-running generation finishes.
```bash
.\.venv\Scripts\python.exe daemon_watchdog.py <nb_id> <task_id>
```
