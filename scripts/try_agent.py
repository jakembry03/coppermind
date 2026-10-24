"""Manual check: send one question through the agent and show every message it produced."""

import json
import sys
from pathlib import Path

from coppermind.agent import Agent, AgentError
from coppermind.llm import LLMError
from coppermind.tools import build_registry

question = sys.argv[1] if len(sys.argv) > 1 else "Whats' in my grocrey list?"

registry = build_registry(Path("sandbox/notes"))
agent = Agent(registry)

try:
    answer = agent.send(question)
except (LLMError, AgentError) as error:
    print(f"Error: {error}")
    sys.exit(1)

print("===Answer===")
print(answer)
print()
print(f"===Trace=== ({len(agent.messages)} messages) ===")
for number, message in enumerate(agent.messages):
    role = message["role"]
    if message.get("tool_calls"):
        for call in message["tool_calls"]:
            function = call["function"]
            print(f"{number}. {role} -> {function['name']}({function['arguments']})")
    elif role == "system":
        print(f"{number}. system (prompt, {len(message['content'])} chars)")
    else:
        print(f"{number}. {role}: {json.dumps(message.get('content'))[:80]}")
