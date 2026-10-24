Core idea of the agent loop:

Send the conversation and the tool list to the model. If the model replies with text, you're done. If it replies asking for tools, run them, add the results to the conversation, and send it again. Repeat

while true:
    send conversation, toolist
    if response == text:
        reply to user with text

    if response == asks for tools:
        run tools
        add the results of tools to the conversation
        reply to the user

- The model decides when it is done. The model will reply with plain text signaling that it is done with tooling. 
- The model still has no memory. Tool requests and tool results are just more messages in the same list. On each loop iteration, the model sees everything, including what its tools returned, because you resend it all.
- The model only *asks*, the loop that I write is what actually calls the tools.

The agent is not smart enough to realize that my notes for The Batman, unless specifically stated are in the notes folder. Just asking it look at my notes is not enough. This might be where training comes in. 

The condition could be whether the response includes a tool call

---

MAX_ITERATIONS = 10

class AgentError, based on Exception
    (the loop gave up: e.g. the model never stopped asking for tools)

class Agent:

    __init__(self, registry, settings = None, system_prompt = None):
        store settings
        store registry
        store system_propmt (load the default if none was given)
        messages = empty list
        call clear()

    clear(self):
        messages = [system message]

    send(self, text) -> text:
        start = current length of messages
        try:
            append {role: "user", content: "text"}

            repeat MAX_ITERATIONS times:
                reply = llm.chat(messages, tools = tool_schemas(registry), settings = settings)
                append reply

                calls = reply's "tool_calls", or empty if missing
                if calls is empty:
                    return reply's "content" or "" if missing

                for each call in calls:
                    result = run_tool_call(call)
                    append {
                        role: "tool",
                        tool_call_id: call's "id",
                        content: result,
                    }
                
                # back to the top: the next llm.chat sees the results

            # only reached if the loop ran out of iterations
            raise AgentError("Copper gave up after MAX_ITERATIONS tool steps")
        
        on any exception:
            cut messages back to length start
            re-raise

    run_tool_call(self, call) -> text:
        name = call's "function" -> "name"
        raw_arguments = call's "function" -> "arguments"

        tool = look up name in registry
        if not found:
            return "Error: unknown tool " + name

        try:
            arguments = parse raw_arguments as JSON
        on JSON decode error:
            return "Error: tool arguments were not valid JSON"

        try:
            return tool's function called with arguments as keyword arguments
        on ToolError as error:
            return "Error: " + error's message
        on TypeError:
            return "Error: wrong arguments for " + name
    
    
    

