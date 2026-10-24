"""
The agent loop: Copper calls the model, runs any tools it asks for, and repeats.

The model decides when it's finished by answering with text instead of tool
calls. Every tool request and result is a message in the history, so the model
sees what its tool returned on the next call.
"""

from coppermind.tools import Tool, ToolError, tool_schemas
from coppermind.conversation import load_system_prompt
from coppermind.config import Settings
from coppermind import llm
from coppermind.llm import Message
import json

MAX_ITERATIONS = 10

class AgentError(Exception):
    """The loop gave up: e.g. the model never stopped asking for tools"""

class Agent:

    def __init__(self, registry: dict[str, Tool], settings: Settings | None = None, system_prompt: str | None = None):
        self.settings = settings
        self.registry = registry
        self.schemas = tool_schemas(registry)
        self.system_prompt = system_prompt if system_prompt is not None else load_system_prompt()
        self.messages: list[Message] = []
        self.clear()

    def clear(self):
        """Forget the conversation, keeping only the system prompt"""
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def send(self, message: str) -> str:
        start = len(self.messages)
        try:
            self.messages.append({"role": "user", "content": message})

            for _ in range(MAX_ITERATIONS):
                reply = llm.chat(self.messages, tools=self.schemas, settings=self.settings)
                self.messages.append(reply)

                calls = reply.get("tool_calls")
                if not calls:
                    return reply.get("content") or "" 

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

        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                return "Error: tool arguments were not valid JSON"
        else:
            arguments = raw_arguments

        if not isinstance(arguments, dict):
            return "Error: tool arguments must be a JSON object."

        try:
            return tool.function(**arguments)
        except ToolError as error:
            return f"Error: {error}"
        except TypeError:
            return f"Error: wrong arguments for {name}"
        
        
