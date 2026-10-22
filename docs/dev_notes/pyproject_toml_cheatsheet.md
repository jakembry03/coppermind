[build-system]
Tells pip which tool builds your package. Hatchling is a simple, modern, build backend. 
Pip downloads it automatically during install; you never call it directly.

[project]
The package metadata. dependencies is empty for now. In M1 you'll add httpx here, which is what makes pip install it for anyone installing Coppermind

[project.opional-dependecies]
Extras you only need for development. Writing .[dev] at install time pulls these in. A real user installing Copper doesn't need pytest.

[project.scripts]
This line is how 'copper' becomes a command. 
It reads as "create a command called 'copper' that imports coppermind.cli and calls its main function"
At install time, pip writes a tiny generated script into your environment's bin/ folder that does exactly that, then exits with whatever main() returns.

[tool.hatch.build.targets.wheel]
Tells hatchling explicitly where the package lives. It can usually guess, but explicit beats guessing.

[tool.ruff] and [tool.pytest.ini_options]
Tool settings. Many Python tools read their config from pyproject.toml, so one file holds everything

