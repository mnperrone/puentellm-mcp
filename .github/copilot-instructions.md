## PuenteLLM-MCP — Copilot instructions for coding agents

This file contains concise, actionable guidance to help an AI coding agent become productive in this repository.

- Big picture
  - The app is a desktop Python (Tk/CustomTkinter) GUI that connects a local or remote LLM to external capabilities via MCP (Model Context Protocol).
  - High-level components:
    - UI & orchestration: `chat_app.py`, `desktop_app.py`, `ui_helpers.py`, `dialogs.py`
    - LLM abstraction: `llm_bridge.py` + provider implementations in `llm_providers/` (use `get_llm_handler` in `llm_providers/__init__.py`).
    - LLM→MCP coordination: `llm_mcp_handler.py` (extracts MCP JSON from LLM output and calls MCP SDK).
    - MCP control: `mcp_manager.py` (start/stop servers, manage processes, `mcp_servers.json`).
    - MCP SDK bridge: `mcp_sdk_bridge.py` (connect to a server script and call tools via MCP client/session).
    - Persistent settings: `app_config.py` (stores config at `~/.puentellm-mcp/config.json`).

- Key workflows and commands
  - Run the desktop app: `python desktop_app.py` (starts the GUI; the app will start/stop LLM and MCP servers via UI).
  - Tests: see `tests/` — install `tests/requirements.txt` and run tests via the repository README; tests are executed with `python run_tests.py` from the `tests` directory.
  - Dependencies: README lists required Python packages and notes that Ollama must be installed and running for local LLM usage.

- Provider & handler contract (important)
  - All LLM handlers under `llm_providers/` follow a simple interface: implement `generate(prompt)` and `stream(messages)` (stream yields chunks with `message.content`). `llm_bridge.py` relies on these.
  - Handlers should raise or propagate `LLMConnectionError` on connection problems; `llm_bridge.py` and `chat_app.py` expect that class to be available (`llm_providers/llm_exception.py`).

- MCP command pattern (concrete example)
  - The LLM signals an MCP action by emitting a segment labelled `MCP_COMMAND_JSON:` followed by a JSON object. Example JSON (must contain `server` and `method`):
    {
      "server": "filesystem",
      "method": "read_file",
      "params": {"path": "/path/to/file"}
    }
  - `llm_mcp_handler.py` extracts that JSON, validates keys `server` and `method`, finds the server entry in `mcp_manager.servers_config["mcpServers"]`, and uses `mcp_sdk_bridge.MCPSDKBridge` to `connect(script_path)` then execute the tool.
  - Note: MCP server script path is taken from the `args` array in `mcp_servers.json` (look for `.py` or `.js`) — the SDK expects a `.py` or `.js` script.

- Platform quirks & conventions
  - MCP servers commonly launched via `npx` — on Windows the code substitutes `npx` → `npx.cmd` (see `mcp_manager.start_server`).
  - `MCPManager.get_default_config_path()` writes a default `mcp_servers.json` next to the code if none exists. Tests and the UI rely on this file format: top-level key `mcpServers`.
  - Config persistence: app settings saved in `~/.puentellm-mcp/config.json` (see `AppConfig`). Avoid editing the config file while the app runs.

- Useful file references (quick jump targets)
  - Orchestration & UI: `chat_app.py`, `desktop_app.py`, `ui_helpers.py`
  - LLM abstraction: `llm_bridge.py`, `llm_providers/` (handler implementations)
  - LLM→MCP logic: `llm_mcp_handler.py` (parsing MCP JSON and invoking SDK)
  - MCP management: `mcp_manager.py`, `mcp_servers.json`
  - SDK: `mcp_sdk_bridge.py` (async connect, `list_tools`, `call_tool`)
  - Config & persistence: `app_config.py`, `last_llm_model.txt`

- What to avoid / gotchas for automated edits
  - Do not change the LLM handler interface (methods `generate` / `stream`) — many modules depend on it.
  - When modifying MCP start logic, preserve Windows-specific `npx.cmd` handling and the `preexec_fn/creationflags` behavior.
  - Be conservative with UI threading: the app uses `window.after()` and background threads for streaming and MCP SDK calls. Prefer using the existing `window.after`/`threading.Thread` patterns.

- When adding a new LLM provider
  - Add a module under `llm_providers/` and register it in `llm_providers/__init__.py` via `get_llm_handler`.
  - Implement `generate` and `stream`. Tests and `LLMBridge` expect those methods.

If anything above is unclear or you want a different level of detail (e.g., example MCP JSON templates, typical test inputs, or a short checklist for adding providers), say which section to expand and I will iterate.