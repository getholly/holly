"""
Tests for the RepoCache class.
"""

import json
import os
import pickle
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from src.repo_mapper.repo_cache import RepoCache


class TestRepoCache:
    """Tests for the RepoCache class."""

    @pytest.fixture
    def cache_dir(self) -> str:
        """Create a temporary directory for cache files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_init_creates_cache_dir(self, cache_dir: str) -> None:
        """Test that the cache directory is created on initialization."""
        # Remove the directory created by the fixture
        shutil.rmtree(cache_dir)
        assert not os.path.exists(cache_dir)

        # Creating the cache should recreate the directory
        RepoCache(cache_dir=cache_dir)
        assert os.path.exists(cache_dir)

    def test_metadata_creation(self, cache_dir: str) -> None:
        """Test that metadata is created correctly."""
        cache = RepoCache(cache_dir=cache_dir)
        metadata_path = Path(cache_dir) / "metadata.json"

        # Save metadata to ensure it's written
        cache._save_metadata()

        # Check that metadata file exists
        assert metadata_path.exists()

        # Check metadata structure
        with open(metadata_path) as f:
            metadata = json.load(f)

        assert "version" in metadata
        assert "created_at" in metadata
        assert "last_updated" in metadata
        assert "cache_entries" in metadata
        assert isinstance(metadata["cache_entries"], dict)

    def test_cache_key_generation(self, cache_dir: str) -> None:
        """Test cache key generation."""
        cache = RepoCache(cache_dir=cache_dir)

        # Create temporary files for the test
        test_repo_dir = tempfile.mkdtemp()
        try:
            # Create test files
            with open(os.path.join(test_repo_dir, "file1.py"), "w") as f:
                f.write("print('hello')")
            with open(os.path.join(test_repo_dir, "file2.py"), "w") as f:
                f.write("print('world')")

            # Test with real files
            repo_path = test_repo_dir
            file_paths = {"file1.py", "file2.py"}
            file_contents = {
                "file1.py": "print('hello')",
                "file2.py": "print('world')",
            }

            key1 = cache._get_cache_key(repo_path, file_paths, file_contents)

            # Should be a hex string
            assert all(c in "0123456789abcdef" for c in key1)

            # Same inputs should produce same key
            key2 = cache._get_cache_key(repo_path, file_paths, file_contents)
            assert key1 == key2

            # Different inputs should produce different keys
            with open(os.path.join(test_repo_dir, "file1.py"), "w") as f:
                f.write("print('changed')")
            file_contents["file1.py"] = "print('changed')"

            key3 = cache._get_cache_key(repo_path, file_paths, file_contents)
            assert key1 != key3
        finally:
            shutil.rmtree(test_repo_dir)

    def test_put_and_get(self, cache_dir: str) -> None:
        """Test storing and retrieving data from cache."""
        cache = RepoCache(cache_dir=cache_dir)

        # Test data
        cache_key = "test_key"
        repo_path = "/test/repo"
        data = {
            "repo_path": repo_path,
            "file_count": 2,
            "modules": [
                {"name": "module1", "file_path": "file1.py"},
                {"name": "module2", "file_path": "file2.py"},
            ],
        }

        # Store data
        cache.put(cache_key, data, repo_path)

        # Retrieve data
        retrieved_data = cache.get(cache_key)

        # Verify data
        assert retrieved_data is not None
        assert retrieved_data["file_count"] == 2
        assert len(retrieved_data["modules"]) == 2
        assert retrieved_data["modules"][0]["name"] == "module1"

        # Check that metadata was updated
        metadata_path = Path(cache_dir) / "metadata.json"
        with open(metadata_path) as f:
            metadata = json.load(f)

        assert cache_key in metadata["cache_entries"]
        assert metadata["cache_entries"][cache_key]["repo_path"] == repo_path

    def test_invalidate(self, cache_dir: str) -> None:
        """Test invalidating cache entries."""
        cache = RepoCache(cache_dir=cache_dir)

        # Test data
        cache_key = "test_key"
        repo_path = "/test/repo"
        data = {"test": "data"}

        # Store data
        cache.put(cache_key, data, repo_path)

        # Verify it exists
        assert cache.get(cache_key) is not None

        # Invalidate
        result = cache.invalidate(cache_key)
        assert result is True

        # Verify it's gone
        assert cache.get(cache_key) is None

        # Check metadata was updated
        metadata_path = Path(cache_dir) / "metadata.json"
        with open(metadata_path) as f:
            metadata = json.load(f)

        assert cache_key not in metadata["cache_entries"]

    def test_clean(self, cache_dir: str) -> None:
        """Test cleaning old cache entries."""
        cache = RepoCache(cache_dir=cache_dir)

        # Create test files
        cache_key1 = "recent_key"
        cache_key2 = "old_key"
        repo_path = "/test/repo"
        data = {"test": "data"}

        # Create cache files directly
        cache_path1 = Path(cache_dir) / f"{cache_key1}.pickle"
        cache_path2 = Path(cache_dir) / f"{cache_key2}.pickle"

        with open(cache_path1, "wb") as f:
            pickle.dump(data, f)

        with open(cache_path2, "wb") as f:
            pickle.dump(data, f)

        # Create metadata manually
        metadata_path = Path(cache_dir) / "metadata.json"

        now = datetime.now()
        recent_time = now.isoformat()
        old_time = (now - timedelta(days=10)).isoformat()

        metadata = {
            "version": "1.0.0",
            "created_at": now.isoformat(),
            "last_updated": now.isoformat(),
            "cache_entries": {
                cache_key1: {
                    "repo_path": repo_path,
                    "created_at": recent_time,
                    "file_count": 1,
                },
                cache_key2: {
                    "repo_path": repo_path,
                    "created_at": old_time,
                    "file_count": 1,
                },
            },
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        # Reload cache to use the new metadata
        cache = RepoCache(cache_dir=cache_dir)

        # Clean entries older than 5 days
        max_age = 5 * 24 * 60 * 60  # 5 days in seconds
        removed = cache.clean(max_age)

        # Should have removed 1 entry
        assert removed == 1

        # Verify recent file still exists but old one is gone
        assert os.path.exists(cache_path1)
        assert not os.path.exists(cache_path2)

        # Check metadata was updated
        with open(metadata_path) as f:
            updated_metadata = json.load(f)

        assert cache_key1 in updated_metadata["cache_entries"]
        assert cache_key2 not in updated_metadata["cache_entries"]
