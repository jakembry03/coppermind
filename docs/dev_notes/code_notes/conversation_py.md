importlib.resources.files("coppermind"):
Finds the system prompt relative to the installed package, not your current directory. If you wrote open("prompts/system.md"), it would only work
when you're standing in src/coppermind/. Run 'copper' from $env:TEMP and it would crash. This is the right way to ship data files inside a package.

except BaseException: ... raise:
Is a "clean up, then let the error continue" pattern. If the model call fails, we remove the user message we just added, then re-raise so the CLI
can report the error. Without the cleanup, a failed call leaves two user messages in a row, and your retry gets sent alongside the orphaned one. BaseException (rather than Exception) also catches Ctrl + C (KeyboardInterrupt). That's normally something to avoid, but it's correct here because we always re-raise.

from coppermind import llm then llm.chat(...) rather than from coppermind.llm import chat.
This matters for testing: tests replace llm.chat on the module, and this code looks it up on the module at call time, so it sees the fake. If you imported the function directly, conversation.py would hold its own reference to the real one and the patch wouldn't take effect.

reply.get("content") or "". Later when the model calls a tool, content can be None. This keeps send() always returning a string.

The constructor accepts optional settings and system_prompt. That's so tests can pass their ow and never depend on your real config or files.

