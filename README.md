# About the Project

Copper is a personal AI agent built for the local machine and to run on self-hosted models. The goal of Copper was threefold:

1. Learning experience of how AI Agents are built.
2. To utilize Artificial Intelligence while keeping data private.
3. To begin to remove the "black box" effect of AI tools.

The idea of Copper came from three places. The first two are from YouTube. I had watched two YouTube videos, one from PewDiePie and him showcasing his Odysseus AI tool, and one from commonLuke where he showed that he built an AI from scratch. Both of these YouTubers not being people with large programming backgrounds accomplishing tasks like this really inspired me to do the same. The third inspiration was Claude Code. I love using Claude Code, it makes coding much easier, allows for higher level thinking and larger abstraction, and introduces more room for "creativity" with code as the programmer does not need to focus on the minor details as much. The problem with Claude Code that I had was the "black box" effect. Simply meaning that I have no idea how it works. I don't have a clue of the internals on how Claude is able to write code into my files much less how these large AI models work. I felt guilty using this tool to output thousands of lines of code for me when not only do I not understand all of the code, I don't even understand the tool. It bothered me so I decided I was going to learn.

## Built With

- Python 3.11+
- [httpx](https://www.python-httpx.org/) for talking to the model server
- Ollama (tested with `qwen3:4b-instruct` and `qwen3:8b`)

## Getting Started

### Prerequisites

- Python 3.11 or newer.
- A model server that speaks the OpenAI-compatible `/chat/completions` API. Copper expects
  [Ollama](https://ollama.com/) by default, but llama.cpp's server and LM Studio speak the same
  API. The model has to support tool calling.

With Ollama, pull the default model before the first run:

    ollama pull qwen3:4b-instruct

### Installation

Clone the repo onto your local machine:

    git clone git@github.com:jakembry03/coppermind.git
    cd coppermind

Create a virtual environment, activate it, then install Copper along with its developer
dependencies (pytest and ruff):

    python -m venv .venv
    source .venv/bin/activate        # macOS / Linux
    .venv\Scripts\Activate.ps1       # Windows PowerShell
    pip install -e ".[dev]"

The install adds a `copper` command to the virtual environment.

## Usage

Start an interactive conversation:

    copper

Inside the conversation:

| Command | What it does |
|---|---|
| `/clear` | Forget the conversation so far and start fresh |
| `/quit`, `/exit` | Leave Copper (Ctrl+C at the prompt also works) |

Or send a single message, print the reply, and exit:

    copper -p "what's on my grocery list?"

`copper --version` prints the installed version.

## Configuration

Copper reads its settings from environment variables, so switching models or servers needs no
code changes:

| Variable | Default | Meaning |
|---|---|---|
| `COPPER_BASE_URL` | `http://localhost:11434/v1` | The model server's OpenAI-compatible base URL |
| `COPPER_MODEL` | `qwen3:4b-instruct` | The model name to request |
| `COPPER_TIMEOUT` | `120` | Seconds to wait for each model reply |

The notes folder isn't configurable: it is always `sandbox/notes` inside this repo, whichever
directory you run `copper` from. That relies on the editable install (`pip install -e`).

For example, in PowerShell:

    $env:COPPER_MODEL = "qwen3:8b"
    copper

## What Copper Can Do

Copper is an agent: on each turn it sends the conversation and a list of tools to the model. If
the model asks to use a tool, Copper runs it, sends back the result, and asks again. This repeats
until the model answers in plain text, up to 10 tool rounds per message.

| Group | Tools |
|---|---|
| core | `get_current_datetime`, `save_memory` |
| files | `read_file`, `list_files`, `list_folders`, `write_to_file`, `append_to_file`, `create_file`, `delete_file`, `copy_file`, `move_file`, `create_folder`, `copy_folders`, `move_folder` |

- **File tools** only work inside the notes folder (`sandbox/notes`). Paths that would escape
  it, and hidden (dot-prefixed) files, are refused.
- **Listing** is the exception: `list_files` and `list_folders` list the notes folder by default,
  but accept an absolute path to any folder on the computer. Hidden folders are skipped, and a
  listing stops after 500 entries.
- **Copy and move** work like `cp` and `mv`. If the destination is an existing folder, the source
  goes inside it. Otherwise the destination becomes the new path, and missing folders are
  created. They never overwrite anything, and a folder can't be copied or moved into itself.
- **Memory:** `save_memory` appends a fact to `~/.copper/memory.md` in your home folder, outside
  the repo. Copper re-reads it before every message, so a saved fact is available immediately
  and in future sessions.
- **The system prompt** lives in `src/coppermind/prompts/system.md`.

Tools that change files have no confirmation step yet, so the model can overwrite (with
`write_to_file`) or delete files inside the notes folder.

## Project Layout

    src/coppermind/
        cli.py           the `copper` command: argument parsing and the chat loop
        agent.py         the agent loop: call the model, run tools, repeat
        llm.py           the only module that talks to the model server
        config.py        settings from COPPER_* environment variables
        conversation.py  the original chat-only version, before tools
        tools/           tool definitions (base.py, core.py, files.py)
        prompts/         the system prompt
    scripts/             manual checks that need a running model server
    tests/               automated tests, which never touch the network
    sandbox/notes/       sample notes used as the default notes folder
    docs/                study notes and example raw responses from the model server

## Development

Run the tests and the linter:

    pytest
    ruff check .

Run a single test:

    pytest tests/test_tools.py::test_read_file_returns_contents

The tests never call a real model. To check things against a running server, use the scripts
in `scripts/`:

    python scripts/try_llm.py                         # one plain chat message
    python scripts/try_agent.py "what's in my notes?"  # one agent turn plus the full message trace
    python scripts/try_tools.py                       # run list_files on the sandbox notes
