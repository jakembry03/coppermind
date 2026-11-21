from coppermind.tools.base import Tool
from pathlib import Path
import requests

BASE_URL = "https://krushcomics.com/api/v1/"

def get_thoughts(tag=None):
    params = {"tag": tag} if tag else {}
    resp = requests.get(
        f"{BASE_URL}/thoughts/",
        params=params,
        headers={"Accept": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()

def website_tools() -> list[Tool]:
    """The website group."""
    return [
        Tool(
            name="get_thoughts",
            description=(
                "Perform a GET request and retrieve a list of all thoughts from the website."
            ),
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            function=get_thoughts,
            group="website",
        )
    ]