#!/bin/bash

uv sync
uv run manage.py migrate
uv run manage.py populate_llms --force
uv run manage.py populate_tools --force
uv run manage.py populate_knowledge --force
