# About the Project

Copper is a personal AI agent built for the local machine and to run on self-hosted models. The goal of Copper was threefold:

    1. Learning experience of how AI Agents are built
    2. To utilize Artificial Intelligence while keeping data private.
    3. To begin to remove the "black box" effect of AI tools.

The idea of Copper came from three places. The first two are from YouTube. I had watched two YouTube videos, one from PewDiePie and him showcasing his Odysseus AI tool, and one from commonLuke where he showed that he built an AI from scratch. Both of these YouTuber's not being people with large programming backgrounds accomplishing tasks like this really inspired me to do the same. The third inspiration was Claude Code. I love using Claude Code, it makes coding much easier, allows for higher level thinking and larger abstraction, and introduces more room for "creativity" with code as the programmer does not need to focus on the minor details as much. The problem with Claude Code that I had was the "black box" effect. Simply meaning that I have no idea how it works. I don't have a clue of the internals on how Claude is able to write code into my files much less how these large AI models work. I felt guilty using this tool to output thousands of lines of code for me when not only do I not understand all of the code, I dont even understand the tool. It bothered me so I decided I was going to learn. 

## Built With

    - Python
    - Ollama (qwen3:4b-instruct, qwen3:8b)
    
## Getting Started

# Prerequisites
All Copper needs to run besides the app harness is an AI model. In its current state it is looking for an Ollama model, though that can be changed in src/coppermind/config.py.

# Installation
First thing you will want to do is clone the github repo onto your local machine. You can do this through the following command:

    git clone git@github.com:jakembry03/coppermind.git

From here to install the app onto your local machine for use you will want to create a Virtaul Environemnt in Python, activate that Virtual Environment and then install the app and its developers dependencies.

    python -m venv .venv
    source .venv/bin/activate OR .venv/scripts/activate.ps1
    pip install -e ".[dev]"

The above installation commands will allow you to run