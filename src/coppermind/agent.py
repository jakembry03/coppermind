from coppermind.tools import read_file, list_files, Tool
from coppermind.conversation import load_system_prompt
from coppermind.config import Settings, load_settings
from coppermind import llm
from coppermind.llm import Message

MAX_ITERATIONS = 10

class AgentError(Exception):
    """The loop gave up: e.g. the model never stopped asking for tools"""

class Agent:

    def __init__(self, registry, settings: Settings | None = None, system_prompt: str | None = None):
        self.settings = settings
        self.registry = registry
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
                reply = llm.chat(self.messages, tools=self.registry, settings=self.settings)
                self.messages.append(reply)

                calls = reply["tool_calls"]
                if not calls:
                    return reply["content"] or "" if not reply["content"]

                for call in calls:
                    result = run_tool_call(call)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    })

            raise AgentError(f"Copper gave up after {MAX_ITERATIONS} tool steps")
        except Exception as error:
            raise AgentError(f"Error: {error}") from error

    def run_tool_call(self, call) -> str:
        
        
