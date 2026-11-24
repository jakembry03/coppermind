"""
The agent loop: Copper calls the model, runs any tools it asks for, and repeats.

The model decides when it's finished by answering with text instead of tool
calls. Every tool request and result is a message in the history, so the model
sees what its tool returned on the next call.
"""

import inspect
import json
import logging

from coppermind import llm
from coppermind.config import Settings
from coppermind.conversation import load_system_prompt
from coppermind.llm import Message
from coppermind.tools import tool_schemas
from coppermind.tools.base import Tool, ToolError
from coppermind.tools.core import load_memory

MAX_ITERATIONS = 10

# With no logging configured, Python still prints ERROR messages (and their
# tracebacks) to stderr, so a crashing tool is visible in the terminal.
logger = logging.getLogger(__name__)


def build_system_prompt() -> str:
    """The system prompt plus everything saved in long-term memory."""
    return load_system_prompt() + "\n## What you know about Jake:\n" + load_memory()


class AgentError(Exception):
    """The loop gave up: e.g. the model never stopped asking for tools"""

class Agent:

    def __init__(self, registry: dict[str, Tool], settings: Settings | None = None, system_prompt: str | None = None):
        self.settings = settings
        self.registry = registry
        self.active_groups: set[str] = {"core", "files"}
        self.schemas = tool_schemas(registry, self.active_groups)
        # A fixed prompt (used by tests) is kept as-is. Otherwise the prompt is rebuilt
        # before every message, so facts saved with save_memory show up straight away.
        self.fixed_system_prompt = system_prompt
        self.messages: list[Message] = []
        self.clear()

    def current_system_prompt(self) -> str:
        if self.fixed_system_prompt is not None:
            return self.fixed_system_prompt
        return build_system_prompt()

    def clear(self):
        """Forget the conversation, keeping only the system prompt"""
        self.messages = [{"role": "system", "content": self.current_system_prompt()}]

    def send(self, message: str) -> str:
        # Re-read memory so anything saved earlier in the conversation is included.
        self.messages[0] = {"role": "system", "content": self.current_system_prompt()}
        start = len(self.messages)
        try:
            self.messages.append({"role": "user", "content": message})

            for _ in range(MAX_ITERATIONS):
                reply = llm.chat(self.messages, tools=self.schemas, settings=self.settings)
                assistant_message = reply.message
                self.messages.append(assistant_message)

                calls = assistant_message.get("tool_calls")
                if not calls:
                    return assistant_message.get("content") or ""

                for call in calls:
                    result = self.run_tool_call(call)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "content": result,
                    })

            raise AgentError(f"Copper gave up after {MAX_ITERATIONS} tool steps")
        except BaseException:
            del self.messages[start:]
            raise

    def run_tool_call(self, call) -> str:
        name = call.get("function").get("name")
        raw_arguments = call.get("function").get("arguments")

        tool = self.registry.get(name)
        if tool is None:
            return f"Error: Unknown tool: {name}"

        if tool.group not in self.active_groups:
            return f"Error: {name} is in the '{tool.group}' group, which isn't loaded."

        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                return "Error: tool arguments were not valid JSON"
        else:
            arguments = raw_arguments

        if not isinstance(arguments, dict):
            return "Error: tool arguments must be a JSON object."

        # Check the arguments before running, so a TypeError *inside* a tool
        # isn't mistaken for "the model sent the wrong arguments".
        try:
            inspect.signature(tool.function).bind(**arguments)
        except TypeError:
            return f"Error: wrong arguments for {name}"

        try:
            return tool.function(**arguments)
        except ToolError as error:
            return f"Error: {error}"
        except OSError as error:
            return f"Error: {error}"
        except Exception as error:
            # A bug or something no one planned for. The model gets a short message
            # so the conversation carries on; the full traceback goes to stderr for you.
            # Exception (not BaseException) lets Ctrl+C still interrupt a slow tool.
            logger.exception("Tool %s crashed", name)
            return f"Error: {name} failed unexpectedly ({type(error).__name__}: {error})"

