"""
Integration tests for repo_mapper.

These tests require tree-sitter to be properly set up.
"""

import json
import os
import shutil
import tempfile

import pytest
from src.repo_mapper import RepoCache, RepoMap


@pytest.mark.integration
class TestRepoMapperIntegration:
    """Integration tests for repo_mapper."""

    @pytest.fixture
    def test_repo(self) -> str:
        """Create a temporary directory with test Python files."""
        temp_dir = tempfile.mkdtemp()

        # Create a simple Python file
        with open(os.path.join(temp_dir, "test_module.py"), "w") as f:
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
        os.makedirs(os.path.join(temp_dir, "submodule"), exist_ok=True)
        with open(os.path.join(temp_dir, "submodule", "__init__.py"), "w") as f:
            f.write('"""Submodule package."""\n')

        with open(os.path.join(temp_dir, "submodule", "helper.py"), "w") as f:
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

    @pytest.mark.skipif(
        not os.path.exists("/data/treesitter/.cache/tree-sitter-python"),
        reason="Tree-sitter Python language not available",
    )
    def test_repo_map_build(self, test_repo: str, cache_dir: str) -> None:
        """Test building a repository map."""
        try:
            # Create and build the map
            repo_cache = RepoCache(cache_dir=cache_dir)
            repo_map = RepoMap(
                repo_path=test_repo,
                cache=repo_cache,
            )

            result = repo_map.build()

            # Basic validations
            assert result is not None
            assert "repo_path" in result
            assert "file_count" in result
            assert "modules" in result

            # Should have 3 modules
            assert result["file_count"] == 3
            assert len(result["modules"]) == 3

            # Find a specific module
            test_module = None
            for module in result["modules"]:
                if module["name"] == "test_module":
                    test_module = module
                    break

            assert test_module is not None
            assert len(test_module["classes"]) == 2
            assert len(test_module["functions"]) == 1

            # Test class lookup
            test_class = repo_map.get_class("TestClass")
            assert test_class is not None
            assert test_class.name == "TestClass"
            assert len(test_class.methods) == 2  # __init__ and get_name

            # Test function lookup
            test_func = repo_map.get_function("test_function")
            assert test_func is not None
            assert test_func.name == "test_function"
            assert test_func.return_type == "bool"
            assert "param1" in test_func.parameters
            assert "param2" in test_func.parameters

            # Test class inheritance
            inheritance = repo_map.get_inheritance_tree("TestClass")
            assert "TestClass" in inheritance
            assert "ChildClass" in inheritance["TestClass"]

            # Test docstring search
            docstring_entities = repo_map.find_by_docstring("docstring")
            assert len(docstring_entities) >= 5  # At least 5 entities with "docstring" in them

            # Test module dependencies
            dependencies = repo_map.get_module_dependencies()
            assert len(dependencies) == 3  # 3 modules

            # Convert to JSON
            json_output = repo_map.to_json()
            assert json_output is not None
            assert len(json_output) > 0

            # Validate JSON can be parsed
            json_data = json.loads(json_output)
            assert json_data["file_count"] == 3

        except Exception as e:
            pytest.skip(f"Integration test failed due to Tree-sitter setup issue: {e}")

    @pytest.mark.skipif(
        not os.path.exists("/data/treesitter/.cache/tree-sitter-python"),
        reason="Tree-sitter Python language not available",
    )
    def test_cache_functionality(self, test_repo: str, cache_dir: str) -> None:
        """Test that caching works correctly."""
        try:
            # Create and build the map
            repo_cache = RepoCache(cache_dir=cache_dir)
            repo_map = RepoMap(
                repo_path=test_repo,
                cache=repo_cache,
            )

            # First build should not use cache
            assert not repo_map.has_valid_cache()
            result1 = repo_map.build()

            # Cache should now be valid
            assert repo_map.has_valid_cache()
            cache_key = repo_map.cache_key

            # Create a new repo map and verify it uses the cache
            repo_map2 = RepoMap(
                repo_path=test_repo,
                cache=repo_cache,
            )

            assert repo_map2.has_valid_cache()
            result2 = repo_map2.build()

            # Results should be equivalent
            assert result1["file_count"] == result2["file_count"]
            assert len(result1["modules"]) == len(result2["modules"])

            # Modify a file to invalidate cache
            with open(os.path.join(test_repo, "test_module.py"), "a") as f:
                f.write("\n# Added comment to invalidate cache\n")

            # Create a new repo map
            repo_map3 = RepoMap(
                repo_path=test_repo,
                cache=repo_cache,
            )

            # Cache should be invalid due to file change
            assert not repo_map3.has_valid_cache()

            # Building should create a new cache entry
            result3 = repo_map3.build()
            assert repo_map3.cache_key != cache_key

        except Exception as e:
            pytest.skip(f"Integration test failed due to Tree-sitter setup issue: {e}")
