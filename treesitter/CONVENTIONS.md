For python we use uv for package management, with the following commands:

uv add <package> -> will add python package to pyproject.toml
uv sync -> will update and ensure your .venv folder contains updated packages
uv run <cmd> -> will enable and run the provided command in the uv defined virtualenv
source .venv/bin/activate -> will startup the virtualenv

The .cache folder contains tree-sitter language files.
