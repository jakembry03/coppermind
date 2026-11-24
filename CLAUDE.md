# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Copper (package `coppermind`) is a personal AI agent that runs against a local, self-hosted model (Ollama by default). It is a learning project: the owner is building it to understand how agents work from the inside. Keep code readable and explicit over clever. The owner keeps study notes in `docs/dev_notes/`. `docs/example-*.json` are sample raw responses from the model server.

## Commands

Setup (Windows, which is the primary dev machine):

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

- Run the agent interactively: `copper` (REPL commands: `/clear`, `/quit`, `/exit`)
- One-shot: `copper -p "what's on my grocery list?"`
- Tests: `pytest` · single test: `pytest tests/test_tools.py::test_read_file_returns_contents`
- Lint: `ruff check .` (line length 100, target py311)
- Manual checks against a real model server: `python scripts/try_llm.py`, `python scripts/try_agent.py "question"` (prints the full message trace), `python scripts/try_tools.py`

Tests never hit the network: they monkeypatch `llm.httpx.post`, `llm.chat`, or `cli.Agent`. Tests that touch memory must monkeypatch `config.MEMORY_FILE` to a temp path (see `tests/test_agent.py`) so they never write to the real file. The `try_*` scripts are the only things that need Ollama running.

## Configuration

`config.load_settings()` reads environment variables into a frozen `Settings` dataclass:

| Var | Default |
|---|---|
| `COPPER_BASE_URL` | `http://localhost:11434/v1` |
| `COPPER_MODEL` | `qwen3:4b-instruct` |
| `COPPER_TIMEOUT` | `120` |

Two paths are fixed constants in `config.py`, not settings:
- `NOTES_DIR` is always `<repo>/sandbox/notes`. It is found from `config.py`'s own location (`parents[2]`), so it only points at the repo with an editable install.
- `MEMORY_FILE` is `~/.copper/memory.md`, outside the repo so personal facts never get committed.

## Architecture

Request flow: `cli.py` → `Agent.send()` (`agent.py`) → `llm.chat()` (`llm.py`) → OpenAI-compatible `/chat/completions` endpoint.

- **`llm.py`** is the only module that talks to the model server (via `httpx`). It returns the reply `message` dict unchanged so callers can append it straight onto the history. Every transport or parse failure becomes `LLMError`.
- **`agent.py`** holds the tool loop. It sends the history plus tool schemas, and if the reply has `tool_calls` it runs each one, appends a `{"role": "tool", "tool_call_id": ..., "content": ...}` message, and loops again. It stops when the model replies with plain text, or raises `AgentError` after `MAX_ITERATIONS` (10). If anything fails partway through a turn, every message from that turn is rolled back so the history never holds a half-finished exchange.
- **System prompt** is `prompts/system.md` (shipped in the package and read with `importlib.resources`) with `~/.copper/memory.md` appended under a "What you know about Jake" heading. `Agent.send()` rebuilds it before every message, so facts saved with `save_memory` are seen on the next message. Passing `system_prompt=` to `Agent` fixes the prompt instead, which tests rely on. `load_memory`/`save_memory` live in `tools/core.py`. They return `""` when no memory file exists yet, and create the file on the first save.
- **`conversation.py`** (`Conversation`) is the older chat-only version without tools. The CLI no longer uses it, but it still has tests, and `agent.py` imports `load_system_prompt` from it.
- **`cli.py`** is deliberately thin: it parses arguments, builds `Settings` and the registry, and runs the REPL or one-shot mode. No agent logic belongs here.

### Tools (`src/coppermind/tools/`)

- A `Tool` (`base.py`) is a frozen dataclass: `name`, `description`, JSON-schema `parameters`, `function` (returns `str`), `group`, and `writes` (marks tools that change something; it is set but not yet enforced by any approval step).
- Each group module exposes a factory (`core_tools()`, `file_tools(notes_root)`). File tools bind `notes_root` through lambdas, so the model only ever supplies relative paths.
- `build_registry()` in `tools/__init__.py` collects all factories into a `name → Tool` dict and refuses duplicate names. **To add a tool group, you must register its factory there.** The agent also only exposes groups listed in `Agent.active_groups` (currently `{"core", "files"}`), and `run_tool_call` rejects calls to tools from groups that aren't active.
- Every file tool must resolve model-supplied paths through `safe_path(root, path)`. It blocks paths that escape the notes root and hidden (dot-prefixed) files.
- **The one deliberate exception:** `list_files`/`list_folders` take an optional `path` that must be *absolute* and may point anywhere on disk (owner's decision). See `list_target()`. They skip hidden entries without walking into hidden folders, skip symlinks that point outside the listed folder, and stop at `MAX_LIST_ENTRIES` (500).
- Copy and move tools follow `cp`/`mv` rules through `final_destination()`. An existing destination folder means "put it inside". Anything else is the new path, with missing parents created. They never overwrite (they raise `ToolError` if the final path exists), and folders can't be copied or moved into themselves.
- Tool results describe paths the way the model gave them: relative in, relative out; absolute in, absolute out (`show_path()`). Write tools return a character count, not the content.
- Tools signal a refusal by raising `ToolError`. `Agent.run_tool_call` never lets a tool crash the loop, and everything comes back to the model as an `"Error: ..."` string:
  - Wrong arguments from the model are caught *before* the call with `inspect.signature(...).bind`.
  - `ToolError` and `OSError` from the tool become their message.
  - Any other `Exception` becomes `"<tool> failed unexpectedly (Type: msg)"`, and `logger.exception` prints the full traceback to stderr.
  - `KeyboardInterrupt` is deliberately *not* caught, so Ctrl+C still interrupts and `send()` rolls back the turn.
- The lambda's parameter names must match the keys in the JSON schema, because arguments are passed as `**kwargs`.

### Known in-progress state (as of 2026-11-23)

- `tools/website.py` (`get_thoughts`) is unfinished and deliberately left for after the cleanup. It imports `requests`, which is not a declared dependency (the project uses `httpx`), and it isn't registered in `build_registry`. It also builds a `//thoughts/` URL, returns parsed JSON instead of `str`, and its schema lacks the `tag` parameter.
- Two tests list the expected tool names by hand (`tests/test_cli.py::test_main_gives_the_agent_every_tool`, `tests/test_tools.py::test_registry_keys_match_tool_names`). Update both whenever you add or rename a tool.
- The folder-copy tool is registered as `copy_folders` (plural), while its function is `copy_folder`.
- `prompts/system.md` lists Copper's tools in prose. Keep it in sync when tools change.

## Sandbox

`sandbox/notes/` is the default notes root that the agent reads and writes during manual testing. Its contents are test data, not project code.
