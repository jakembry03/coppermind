"""Manual check: send one message to the real model server and print the reply"""

from coppermind.llm import LLMError, chat

try:
    reply = chat(
        [
            {
                "role": "user",
                "content": "Finish the quote: 'Life before death, strength before weakness...",
            }
        ]
    )
    print(reply["content"])
except LLMError as error:
    print(f"Error {error}")
