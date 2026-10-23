# How Copper Works

## Big Picture
Copper's phase 1 has four modules, and each exactly one job. When a message is typed, it flows down through each module, and the reply flows back up.
1. cli.py reads what you typed and decides what to do with it (command (/quit, /help), question (What year did the United States become a country?) or flag (-p, --prompt))
2. conversation.py adds your message to the history list.
3. llm.py sends the *entire* history to the model server over HTTP and turns any failure into one error type.
4. Ollama runs the model on your machine (preferrably in GPU mode, will run in CPU mode if no Nvidia GPU is detected) and returns one reply message.
5. The reply travels back "up", conversation.py records it and cli.py prints back to the user. config.py sits beside them and is read by llm.py.

See Coppermind Study Guide Phase 1 for visual representation

### My Own Words:
The code starts at cli.py. It decides what the user's input means and how it is directed. It looks for flags (-p, --prompt, --version) or commands (/quit, /help) or text ("Hello, how are you?"). 

If there is a prompt flag, text is initialized as the user's prompt.strip(), then it returns the one_shot function of that prompt. one_shot takes a Conversation object as input and it tries to generate the reply by sending the text to the model and then print that reply.

If there is not a prompt flag, it sends the conversation to the repl()
repl() takes a Conversation object and sends it through a while loop. If the text sent in repl matches any of the commands it will do their actions, if not it sends the conversation to the model and stores the returned value in the reply variable. Then it will print the reply as long as there are no errors thrown.




