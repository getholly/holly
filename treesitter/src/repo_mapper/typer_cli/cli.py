#!/usr/bin/env python3
"""
Typer-based CLI for RepoMap.

This module provides a command-line interface for the RepoMap library
using Typer for improved CLI experience.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from unittest import mock

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from ..repo_cache import RepoCache
from ..repo_map import RepoMap

# Create Typer app
app = typer.Typer(
    name="repomap",
    help="RepoMap - Python Repository Analyzer",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


@app.command()
def analyze(
    repo_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Path to the repository to analyze",
    ),
    cache_dir: Path | None = typer.Option(
        ".cache/repomap",
        "--cache-dir",
        "-c",
        help="Path to the cache directory (default: .cache/repomap)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to output JSON file",
    ),
    exclude: list[str] | None = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Patterns to exclude from analysis",
    ),
    max_cache_age: int | None = typer.Option(
        None,
        "--max-cache-age",
        "-a",
        help="Maximum age of cache entries in seconds",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force rebuild even if cache is valid",
    ),
    clean_cache: bool = typer.Option(
        False,
        "--clean-cache",
        help="Clean old cache entries",
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed statistics",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
    use_mock: bool = typer.Option(
        False,
        "--mock",
        "-m",
        help="Use mock data instead of tree-sitter (for demo purposes)",
    ),
) -> int:
    """
    Analyze a Python repository and generate a structural map.

    This command parses Python source files in the repository,
    extracts information about modules, classes, and functions,
    and generates a structured representation of the codebase.
    """
    try:
        # Set up Rich with or without color
        console = Console(no_color=no_color)

        # Resolve paths
        repo_path = repo_path.resolve()
        if cache_dir:
            cache_dir = cache_dir.resolve()

        # Create cache directory if it doesn't exist
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

        # Create the cache
        cache = RepoCache(cache_dir=str(cache_dir) if cache_dir else None)

        # Clean cache if requested
        if clean_cache and max_cache_age:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Cleaning cache...", justify="right"),
                console=console,
            ) as progress:
                task = progress.add_task("Cleaning", total=None)
                removed = cache.clean(max_cache_age)
                progress.update(task, completed=True)

            console.print(f"[green]Cleaned {removed} old cache entries[/green]")

        # Create the repo map
        console.print(f"[bold]Analyzing repository:[/bold] {repo_path}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Processing...", justify="right"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Building repository map", total=None)

            # Create the repo map
            start_time = time.time()

            if use_mock:
                # Use mock data for demo purposes
                progress.update(task, description="Using mock implementation")

                # Create a simple mock result
                result = {
                    "repo_path": str(repo_path),
                    "file_count": 5,
                    "modules": [
                        {
                            "name": "main_module",
                            "file_path": "main_module.py",
                            "type": "module",
                            "classes": [
                                {
                                    "name": "MainClass",
                                    "file_path": "main_module.py",
                                    "start_line": 10,
                                    "end_line": 50,
                                    "docstring": "Main class for the application.",
                                    "base_classes": ["BaseClass"],
                                    "methods": [
                                        {
                                            "name": "process_data",
                                            "file_path": "main_module.py",
                                            "start_line": 15,
                                            "end_line": 25,
                                            "docstring": "Process input data.",
                                            "parameters": ["self", "data", "options"],
                                            "return_type": "Dict[str, Any]",
                                        },
                                        {
                                            "name": "validate",
                                            "file_path": "main_module.py",
                                            "start_line": 30,
                                            "end_line": 40,
                                            "docstring": "Validate input data.",
                                            "parameters": ["self", "data"],
                                            "return_type": "bool",
                                        },
                                    ],
                                },
                            ],
                            "functions": [
                                {
                                    "name": "run_application",
                                    "file_path": "main_module.py",
                                    "start_line": 55,
                                    "end_line": 70,
                                    "docstring": "Run the main application.",
                                    "parameters": ["config_path", "debug"],
                                    "return_type": "int",
                                },
                            ],
                            "imports": [
                                "import os",
                                "import sys",
                                "from typing import Dict, Any, List, Optional",
                            ],
                        },
                        {
                            "name": "utils",
                            "file_path": "utils.py",
                            "type": "module",
                            "classes": [],
                            "functions": [
                                {
                                    "name": "format_output",
                                    "file_path": "utils.py",
                                    "start_line": 10,
                                    "end_line": 20,
                                    "docstring": "Format output data.",
                                    "parameters": ["data", "format_type"],
                                    "return_type": "str",
                                },
                            ],
                            "imports": [
                                "import json",
                                "import yaml",
                            ],
                        },
                    ],
                }

                # Create a mock repo_map for statistics
                mock_repo_map = mock.MagicMock()
                mock_modules = {}

                for module_data in result["modules"]:
                    mock_module = mock.MagicMock()
                    mock_module.classes = [mock.MagicMock() for _ in module_data["classes"]]
                    mock_module.functions = [mock.MagicMock() for _ in module_data["functions"]]

                    # Add methods to classes
                    for i, cls in enumerate(module_data["classes"]):
                        mock_module.classes[i].methods = [mock.MagicMock() for _ in cls["methods"]]
                        mock_module.classes[i].name = cls["name"]

                    mock_modules[module_data["file_path"]] = mock_module

                mock_repo_map.modules = mock_modules

                # Calculate processing time
                elapsed_time = time.time() - start_time

                # Mark task as complete
                progress.update(task, completed=True)

                # Output the result if specified
                if output:
                    with open(output, "w") as f:
                        json.dump(result, f, indent=2)
                    console.print(f"[green]Repository map written to[/green] {output}")

                # Show statistics
                show_statistics(mock_repo_map, result, elapsed_time, detailed, console)

                return 0

            # Use actual tree-sitter implementation
            try:
                repo_map = RepoMap(
                    repo_path=str(repo_path),
                    cache=cache,
                    exclude_patterns=exclude,
                    max_cache_age=max_cache_age,
                )

                # Check cache status
                if repo_map.has_valid_cache() and not force:
                    progress.update(task, description="Using cached data")
                else:
                    progress.update(task, description="Building repository map")

                # Build the map
                result = repo_map.build(force=force)

                # Calculate processing time
                elapsed_time = time.time() - start_time

                # Mark task as complete
                progress.update(task, completed=True)

                # Output the result
                if output:
                    repo_map.to_json(str(output))
                    console.print(f"[green]Repository map written to[/green] {output}")

                # Show statistics
                show_statistics(repo_map, result, elapsed_time, detailed, console)

                return 0
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                console.print("\n[yellow]Tip:[/yellow] Use --mock flag to run with mock data for demonstration.")
                return 1

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


@app.command()
def find_strings(
    repo_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Path to the repository to analyze",
    ),
    search_string: str = typer.Argument(
        ...,
        help="String literal to search for",
    ),
    cache_dir: Path | None = typer.Option(
        ".cache/repomap",
        "--cache-dir",
        "-c",
        help="Path to the cache directory (default: .cache/repomap)",
    ),
    exclude: list[str] | None = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Patterns to exclude from analysis",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
    use_mock: bool = typer.Option(
        False,
        "--mock",
        "-m",
        help="Use mock data instead of tree-sitter (for demo purposes)",
    ),
) -> int:
    """
    Find all occurrences of a string literal in the repository.

    This command searches for the exact string within quotes (single, double, or triple)
    and shows where it's used, including the containing function and class.
    """
    try:
        # Set up Rich with or without color
        console = Console(no_color=no_color)

        # Resolve paths
        repo_path = repo_path.resolve()
        if cache_dir:
            cache_dir = cache_dir.resolve()
            os.makedirs(cache_dir, exist_ok=True)

        # Create the cache
        cache = RepoCache(cache_dir=str(cache_dir) if cache_dir else None)

        # Create the repo map
        console.print(f"[bold]Searching for string literal:[/bold] '{search_string}'")
        console.print(f"[bold]Repository:[/bold] {repo_path}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Searching...", justify="right"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing repository", total=None)

            # Create the repo map and search for string literals
            start_time = time.time()

            # Check if we should use mock mode
            if use_mock:
                # Use mock data for demo purposes
                progress.update(task, description="Using mock implementation")

                # Create a simple mock result with example occurrences
                results = [
                    {
                        "file_path": "examples/python/apps.py",
                        "line_number": 15,
                        "context": 'print("hello, world!")',
                        "function_name": "main",
                        "class_name": None,
                    },
                    {
                        "file_path": "examples/python/greet.py",
                        "line_number": 8,
                        "context": 'return f"hello, {name}!"',
                        "function_name": "greet",
                        "class_name": None,
                    },
                ]

                # Calculate processing time
                elapsed_time = time.time() - start_time

                # Mark task as complete
                progress.update(task, completed=True)
            else:
                # Find string literals
                try:
                    repo_map = RepoMap(
                        repo_path=str(repo_path),
                        cache=cache,
                        exclude_patterns=exclude,
                    )

                    # Find string literals
                    results = repo_map.find_string_literals(search_string)

                    # Calculate processing time
                    elapsed_time = time.time() - start_time

                    # Mark task as complete
                    progress.update(task, completed=True)
                except Exception as e:
                    console.print(f"[bold red]Error:[/bold red] {e}")
                    console.print("\n[yellow]Tip:[/yellow] Use --mock flag to run with mock data for demonstration.")
                    return 1

            # Show results
            if not results:
                console.print(f"[yellow]No occurrences found for string literal:[/yellow] '{search_string}'")
                return 0

            # Create a table for the results
            table = Table(title=f"Found {len(results)} occurrences of '{search_string}'")
            table.add_column("File", style="cyan")
            table.add_column("Line", style="green", justify="right")
            table.add_column("Class", style="magenta")
            table.add_column("Function", style="blue")
            table.add_column("Context", style="yellow")

            for result in results:
                file_path = result["file_path"]
                line_number = str(result["line_number"])
                class_name = result["class_name"] or ""
                function_name = result["function_name"] or ""
                context = result["context"]

                # Truncate context if too long
                if len(context) > 70:
                    context = context[:67] + "..."

                table.add_row(file_path, line_number, class_name, function_name, context)

            console.print(table)
            console.print(f"Search completed in [green]{elapsed_time:.2f}[/green] seconds")

            return 0

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1


def show_statistics(
    repo_map: Any,
    result: dict[str, Any],
    elapsed_time: float,
    detailed: bool,
    console: Console,
) -> None:
    """Show statistics about the repository."""
    # Basic stats
    file_count = result.get("file_count", 0)

    # Count classes and functions
    class_count = 0
    function_count = 0
    method_count = 0

    for module in result.get("modules", []):
        class_count += len(module.get("classes", []))
        function_count += len(module.get("functions", []))

        # Count methods
        for cls in module.get("classes", []):
            method_count += len(cls.get("methods", []))

    # Create statistics table
    table = Table(title="Repository Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green", justify="right")

    table.add_row("Python Files", str(file_count))
    table.add_row("Classes", str(class_count))
    table.add_row("Functions", str(function_count))
    table.add_row("Methods", str(method_count))
    table.add_row("Total Functions/Methods", str(function_count + method_count))
    table.add_row("Processing Time", f"{elapsed_time:.2f} seconds")

    console.print(table)

    # Show more detailed statistics if requested
    if detailed:
        show_detailed_statistics(repo_map, console)


def show_detailed_statistics(repo_map: Any, console: Console) -> None:
    """Show detailed statistics about the repository."""
    # Find large classes
    large_classes = []
    for module_path, module in repo_map.modules.items():
        for cls in module.classes:
            large_classes.append(
                (
                    cls.name,
                    module_path,
                    len(cls.methods),
                ),
            )

    # Sort by method count
    large_classes.sort(key=lambda x: x[2], reverse=True)

    # Show large classes
    if large_classes:
        class_table = Table(title="Top 5 Largest Classes")
        class_table.add_column("Class", style="cyan")
        class_table.add_column("Module", style="blue")
        class_table.add_column("Methods", style="green", justify="right")

        for class_name, module_path, method_count in large_classes[:5]:
            class_table.add_row(class_name, module_path, str(method_count))

        console.print(class_table)


@app.command()
def find_calls(
    repo_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Path to the repository to analyze",
    ),
    function_name: str = typer.Argument(
        ...,
        help="Function name to find calls to",
    ),
    cache_dir: Path | None = typer.Option(
        ".cache/repomap",
        "--cache-dir",
        "-c",
        help="Path to the cache directory (default: .cache/repomap)",
    ),
    exclude: list[str] | None = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Patterns to exclude from analysis",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
    use_mock: bool = typer.Option(
        False,
        "--mock",
        "-m",
        help="Use mock data instead of tree-sitter (for demo purposes)",
    ),
) -> int:
    """
    Find all places where a specific function is called in the repository.

    This command helps you track function usage across the codebase by showing
    every location where a function is called, along with the caller context.
    """
    try:
        # Set up Rich with or without color
        console = Console(no_color=no_color)

        # Resolve paths
        repo_path = repo_path.resolve()
        if cache_dir:
            cache_dir = cache_dir.resolve()
            os.makedirs(cache_dir, exist_ok=True)

        # Create the cache
        cache = RepoCache(cache_dir=str(cache_dir) if cache_dir else None)

        # Create the repo map
        console.print(f"[bold]Searching for calls to function:[/bold] '{function_name}'")
        console.print(f"[bold]Repository:[/bold] {repo_path}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Searching...", justify="right"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing repository", total=None)

            # Create the repo map and search for function calls
            start_time = time.time()

            # Check if we should use mock mode
            if use_mock:
                # Use mock data for demo purposes
                progress.update(task, description="Using mock implementation")

                # Create a simple mock result with example occurrences
                results = [
                    {
                        "file_path": "examples/python/main.py",
                        "line_number": 15,
                        "context": f"result = {function_name}(params)",
                        "caller_function": "process_data",
                        "caller_class": None,
                    },
                    {
                        "file_path": "examples/python/utils.py",
                        "line_number": 8,
                        "context": f"return {function_name}(value)",
                        "caller_function": "transform",
                        "caller_class": "DataProcessor",
                    },
                ]

                # Calculate processing time
                elapsed_time = time.time() - start_time

                # Mark task as complete
                progress.update(task, completed=True)
            else:
                # Find function calls
                try:
                    repo_map = RepoMap(
                        repo_path=str(repo_path),
                        cache=cache,
                        exclude_patterns=exclude,
                    )

                    # Find function calls
                    results = repo_map.find_function_calls(function_name)

                    # Calculate processing time
                    elapsed_time = time.time() - start_time

                    # Mark task as complete
                    progress.update(task, completed=True)
                except Exception as e:
                    console.print(f"[bold red]Error:[/bold red] {e}")
                    console.print("[yellow]Tip:[/yellow] Use --mock flag to run with mock data for demonstration.")
                    return 1

            # Show results
            if not results:
                console.print(f"[yellow]No calls found for function:[/yellow] '{function_name}'")
                return 0

            # Create a table for the results
            table = Table(title=f"Found {len(results)} calls to '{function_name}'")
            table.add_column("File", style="cyan")
            table.add_column("Line", style="green", justify="right")
            table.add_column("Class", style="magenta")
            table.add_column("Function", style="blue")
            table.add_column("Context", style="yellow")

            for result in results:
                file_path = result["file_path"]
                line_number = str(result["line_number"])
                class_name = result["caller_class"] or ""
                function_name = result["caller_function"] or ""
                context = result["context"]

                # Truncate context if too long
                if len(context) > 70:
                    context = context[:67] + "..."

                table.add_row(file_path, line_number, class_name, function_name, context)

            console.print(table)
            console.print(f"Search completed in [green]{elapsed_time:.2f}[/green] seconds")

            return 0

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.exception(f"error:{e}")
        return 1


def main() -> int:
    """Main entry point for the CLI."""
    result = app()
    return 0 if result is None else result


if __name__ == "__main__":
    sys.exit(main())
