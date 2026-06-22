# Antigravity NotebookLM Plugin

An enterprise-grade, event-driven integration of [Google's NotebookLM](https://notebooklm.google.com/) into the Antigravity multi-agent ecosystem. This plugin abstracts the complex web-scraping and browser orchestration of `notebooklm-py` into a strictly governed, asynchronous, and JSON-safe Agent Skill.

## 🌟 Core Architecture & Features

This plugin is designed around the **"Zero-SDK & Event-Driven"** philosophy of Antigravity:

*   **🛡️ Toxic I/O Isolation (JSON Bridge):** The plugin does not expose the raw CLI to the Agent. Instead, it uses a Python Bridge layer (`auth_bridge.py`, `notebook_bridge.py`, `generate_bridge.py`) that uses Regular Expressions to forcefully extract valid JSON payloads, completely discarding any random Playwright engine warnings or Chromium download logs that would otherwise crash the Agent's parser.
*   **⏳ Event-Driven Watchdog:** NotebookLM generations (like Podcasts) take 5~15 minutes. To prevent the Agent from wasting Tokens in a polling loop, the plugin implements a `daemon_watchdog.py`. The Agent spawns this daemon in the background (`run_command` in non-blocking mode) and immediately goes to sleep. Once the cloud generation finishes, the Watchdog emits a `[WAKEUP]` signal, and Antigravity's native task manager instantly resurrects the Agent.
*   **🔗 Vector Lake Two-Way Sync:** Enforces strict Governance Rules in `SKILL.md`. Every Notebook created in the cloud must be mapped as an Entity in Antigravity's local `Vector Lake` graph, eliminating knowledge silos.
*   **🎧 Rich Media Artifact Routing:** Raw `.wav` and `.mp4` downloads are automatically wrapped into `.md` Artifacts with absolute-path embeds, allowing the user to seamlessly play NotebookLM Podcasts directly within the Antigravity chat interface.

## 📂 Directory Structure

```text
config/plugins/notebooklm/
├── plugin.json                 # Plugin metadata
├── README.md                   # This file
├── agents/
│   └── notebooklm_researcher/  # Dedicated subagent for long-running Deep Research
│       └── agent.json          # System Prompt strictly enforcing Event-Driven limits
└── skills/
    └── notebooklm-core/
        ├── SKILL.md            # Execution Contract & Security Governance Gates
        └── scripts/            # The "Air-gapped" Python execution layer
            ├── .venv/          # Isolated Playwright & notebooklm-py environment
            ├── auth_bridge.py      
            ├── notebook_bridge.py  
            ├── generate_bridge.py  
            └── daemon_watchdog.py  
```

## 🚀 Setup & Authentication

Because NotebookLM relies on Google's internal APIs, it requires valid browser cookies. **The Agent is strictly forbidden from stealing cookies without explicit `/grill-me` consent.**

To initialize the plugin on a new host machine:

1. **Enter the Virtual Environment:**
   ```powershell
   cd ~/.gemini/config/plugins/notebooklm/skills/notebooklm-core/scripts
   .\.venv\Scripts\Activate.ps1
   ```
2. **Launch Interactive Login:**
   ```powershell
   notebooklm login
   ```
   *A Chromium browser will pop up. Login to your Google account. The credentials will be saved locally.*

3. **Verify Auth Health (Agent-Side):**
   The Agent can verify the login status at any time without blocking the UI:
   ```bash
   python auth_bridge.py check
   ```

## 🤖 Using the Plugin

Simply ask Antigravity:
> *"Help me create a new NotebookLM project about Quantum Physics, upload this wiki link, and generate a 2-person podcast."*

The Agent will automatically:
1. Validate Auth via Bridge.
2. Create the Notebook & Link the Source.
3. Trigger the Podcast generation.
4. Spawn `daemon_watchdog.py` and hibernate.
5. Wake up 10 minutes later, download the Audio, and serve it to you via a playable Markdown Artifact.
