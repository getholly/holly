"""
Tests for the Typer CLI.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from src.repo_mapper.typer_cli.cli import app
from typer.testing import CliRunner


class TestTyperCli:
    """Tests for the Typer CLI."""

    @pytest.fixture
    def test_repo(self) -> str:
        """Create a temporary directory with test Python files."""
        temp_dir = tempfile.mkdtemp()

        with (Path(temp_dir) / "test_module.py").open("w") as f:
            f.write('''
        """Test module docstring."""

        import os
        import sys
        from typing import List, Dict, Optional

class TestClass:
    """Test class docstring."""

    def __init__(self, name: str) -> None:
        """Initialize with a name."""
        self.name = name

    def get_name(self) -> str:
        """Return the name."""
        return self.name

        def test_function(param1: int, param2: str = "default") -> bool:
            """Test function docstring."""
            return True

class ChildClass(TestClass):
    """Child class that extends TestClass."""

    def extra_method(self) -> None:
        """Extra method in child class."""
        print("Extra method")
''')
        # Create another module
        Path(temp_dir).joinpath("submodule").mkdir(exist_ok=True)
        with (Path(temp_dir) / "submodule" / "__init__.py").open("w") as f:
            f.write('"""Submodule package."""\n')

        with Path(temp_dir).joinpath("submodule", "helper.py").open("w") as f:
            f.write('''
        """Helper module."""

        from typing import Any

def helper_function(data: Any) -> str:
    """Process data and return a string."""
    return str(data)
''')

        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache_dir(self) -> str:
        """Create a temporary directory for cache files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Return a CliRunner instance."""
        return CliRunner()

    def test_cli_help(self, runner: CliRunner) -> None:
        """Test the CLI help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "repomap" in result.stdout

    def test_analyze_command_help(self, runner: CliRunner) -> None:
        """Test the analyze command help."""
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "Analyze a Python repository" in result.stdout

    @pytest.mark.skip(reason="Needs more mocking for tree-sitter")
    @mock.patch("src.repo_mapper.repo_map.RepoMap._setup_parser")
    def test_basic_analyze(
        self,
        mock_setup_parser: mock.MagicMock,
        runner: CliRunner,
        test_repo: str,
        cache_dir: str,
    ) -> None:
        """Test basic analyze command."""
        # Mock the tree-sitter parser setup
        mock_parser = mock.MagicMock()
        mock_setup_parser.return_value = mock_parser

        # Create a mock for the parse method
        mock_parse = mock.MagicMock()
        mock_parser.parse.return_value = mock_parse
        mock_parse.root_node = mock.MagicMock()

        # Run the analyze command with appropriate parameters
        result = runner.invoke(
            app,
            ["analyze", test_repo, "--cache-dir", cache_dir, "--no-color"],
        )

        # Check the result
        assert result.exit_code == 0
        assert "Analyzing repository" in result.stdout
        assert "Repository Statistics" in result.stdout
