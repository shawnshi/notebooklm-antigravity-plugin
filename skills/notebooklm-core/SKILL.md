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
2. For long tasks (audio, video, deep research): You MUST use the `wait` commands via `run_command` in the background, which will natively suspend and wake you up when complete.

## <RULE: VECTOR_LAKE_SYNC> (Two-Way Mapping)
When you create a Notebook using `notebook_bridge.py create`, you MUST:
1. Ensure the Concept does not already exist via the `call_mcp_tool` for `check_duplicate_entity`.
2. Create or map a node in the local Vector Lake graph using the `call_mcp_tool` for `update_operational_memory`, attaching the Notebook ID as metadata.
3. Any textual artifacts generated from NotebookLM (like Study Guides or Summaries) MUST be synced into the local graph by delegating to the `vector-lake-ingestor` subagent via `invoke_subagent`. (DO NOT execute heavy sync synchronously).

## <RULE: ARTIFACT_ROUTING> (Media Handling)
When downloading Audio or Video outputs from `generate_bridge.py`, you MUST NOT simply leave the raw `.wav`/`.mp4` in the `scratch/` directory.
You MUST create an Antigravity Artifact `.md` file in the `brain/<conversation-id>` directory that embeds the absolute path of the downloaded media using markdown syntax: `![Podcast Audio](file:///absolute/path/to/audio.wav)`, so it can be natively played in the UI.

## Available Adapter Scripts

Located in `config/plugins/notebooklm/skills/notebooklm-core/scripts/`.
**CRITICAL**: You MUST execute these using the `run_command` tool. 
- Set the `Cwd` parameter to `C:\Users\shich\.gemini\config\plugins\notebooklm\skills\notebooklm-core\scripts`.
- Prefix ALL commands with `$env:PYTHONIOENCODING="utf-8";` to prevent Windows encoding crashes.

### 1. `auth_bridge.py`
```bash
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe auth_bridge.py check
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe auth_bridge.py login
```

### 2. `notebook_bridge.py`
```bash
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe notebook_bridge.py create "My Research"
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe notebook_bridge.py list
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe notebook_bridge.py add-source <nb_id> <url>
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe notebook_bridge.py list-source <nb_id>
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe notebook_bridge.py delete-source <nb_id> <source_id>
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe notebook_bridge.py ask <nb_id> "Your question here"
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe notebook_bridge.py research <nb_id> <query> <mode>
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe notebook_bridge.py wait-research <nb_id>
```

### 3. `generate_bridge.py`
Supports all 9 official artifacts: `audio`, `video`, `slide-deck`, `quiz`, `mind-map`, `report`, `flashcards`, `infographic`, `data-table` (plus `cinematic-video`).
```bash
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe generate_bridge.py audio <nb_id> [instructions]
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe generate_bridge.py slide-deck <nb_id>
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe generate_bridge.py report <nb_id>
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe generate_bridge.py status <nb_id>
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe generate_bridge.py wait <nb_id> <artifact_id>
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe generate_bridge.py download <nb_id> <task_id> <type> <output_path>
```
