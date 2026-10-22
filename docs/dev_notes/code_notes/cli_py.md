**repl() is separate from main(), and it takes the conversation as a parameter:**
This is called dependency injection, and it's what makes the loop testable: tests hand repl() a fake conversation that never touches the network.
main() is the only place that builds the real one.

**Each slash command is handled and then 'continue's:**
Commands never get sent to the model. Unknown slash commands get a hint instead of being sent as a message, so a typo like /qiut doesn't become a question to Copper.

**Two different Ctrl + C behaviors:**
At the prompt, Ctrl + C exits Copper. While Copper is thinking, it cancels just that reply and returns you to the prompt, which is handy when a local
model is taking too long. Thanks to the cleanup in send(), the history stays consistent.

**Errors print and the loop continues:**
If you quit Ollama mid-conversation, Copper tells you, and once you restart Ollama you can keep going with your history intact.

