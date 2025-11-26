"""
Cache module for storing and retrieving parsed repository AST data.
"""

import hashlib
import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, cast


class RepoCache:
    """
    Cache for repository AST data.

    This class manages caching of parsed repository data to avoid
    re-parsing the same files multiple times.
    """

    def __init__(self, cache_dir: str | None = None) -> None:
        """
        Initialize the repository cache.

        Args:
            cache_dir: Directory to store cache files. If None, uses ~/.repo_mapper_cache
        """
        if cache_dir is None:
            self.cache_dir = Path.home() / ".repo_mapper_cache"
        else:
            self.cache_dir = Path(cache_dir)

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache metadata
        self._metadata_path = self.cache_dir / "metadata.json"
        self._metadata: dict[str, Any] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load metadata from disk if it exists."""
        if self._metadata_path.exists():
            try:
                with open(self._metadata_path) as f:
                    self._metadata = json.load(f)
            except (OSError, json.JSONDecodeError):
                # If metadata is corrupted, start fresh
                self._metadata = {
                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "cache_entries": {},
                }
        else:
            # Initialize new metadata
            self._metadata = {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "cache_entries": {},
            }

    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        self._metadata["last_updated"] = datetime.now().isoformat()
        try:
            with open(self._metadata_path, "w") as f:
                json.dump(self._metadata, f, indent=2)
        except OSError as e:
            print(f"Warning: Could not save cache metadata: {e}")

    def _get_cache_key(self, repo_path: str, file_paths: set[str], file_contents: dict[str, str]) -> str:
        """
        Generate a cache key for a repository.

        Args:
            repo_path: Path to the repository
            file_paths: Set of file paths in the repository
            file_contents: Dictionary mapping file paths to their contents

        Returns:
            A unique hash string that identifies this repository state
        """
        # Create a hash based on file paths and their last modified times
        hasher = hashlib.sha256()

        # Add repo path
        hasher.update(repo_path.encode("utf-8"))

        # Sort paths for consistent hashing
        sorted_paths = sorted(file_paths)

        for path in sorted_paths:
            full_path = os.path.join(repo_path, path)
            if os.path.exists(full_path):
                # Use file content hash if provided
                if path in file_contents:
                    content_hash = hashlib.md5(file_contents[path].encode("utf-8")).hexdigest()
                    hasher.update(f"{path}:{content_hash}".encode())
                else:
                    # Otherwise use last modified time
                    stat = os.stat(full_path)
                    hasher.update(f"{path}:{stat.st_mtime}".encode())

            # Make sure we're using different hasher states for different contents
            hasher.update(b"---separator---")

        return hasher.hexdigest()

    def has_valid_cache(self, repo_path: str, max_age: int | None = None) -> bool:
        """
        Check if there is a valid cache entry for the repository.

        Args:
            repo_path: Path to the repository
            max_age: Maximum age of the cache in seconds (None for no limit)

        Returns:
            True if a valid cache entry exists, False otherwise
        """
        # We need file information to calculate the cache key
        # This is a placeholder that will always return False since we don't have
        # the complete file information here. The actual implementation will be in RepoMap.
        return False

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """
        Retrieve cached data for a repository.

        Args:
            cache_key: Cache key for the repository

        Returns:
            Cached repository data or None if not found
        """
        cache_path = self.cache_dir / f"{cache_key}.pickle"
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "rb") as f:
                # Use cast to specify the return type to avoid mypy error
                return cast(dict[str, Any], pickle.load(f))
        except (OSError, pickle.PickleError):
            # If there's an error loading the cache, return None
            return None

    def put(self, cache_key: str, data: dict[str, Any], repo_path: str) -> None:
        """
        Store repository data in the cache.

        Args:
            cache_key: Cache key for the repository
            data: Repository data to cache
            repo_path: Path to the repository (for metadata)
        """
        cache_path = self.cache_dir / f"{cache_key}.pickle"

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            # Update metadata
            self._metadata["cache_entries"][cache_key] = {
                "repo_path": repo_path,
                "created_at": datetime.now().isoformat(),
                "file_count": data.get("file_count", 0),
            }
            self._save_metadata()
        except OSError as e:
            print(f"Warning: Could not save cache: {e}")

    def invalidate(self, cache_key: str) -> bool:
        """
        Invalidate a cache entry.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            True if the cache was invalidated, False otherwise
        """
        cache_path = self.cache_dir / f"{cache_key}.pickle"
        if cache_path.exists():
            try:
                os.remove(cache_path)
                if cache_key in self._metadata["cache_entries"]:
                    del self._metadata["cache_entries"][cache_key]
                    self._save_metadata()
                return True
            except OSError:
                return False
        return False

    def clean(self, max_age: int | None = None) -> int:
        """
        Clean old cache entries.

        Args:
            max_age: Maximum age of cache entries in seconds

        Returns:
            Number of cache entries removed
        """
        if not max_age:
            return 0

        now = datetime.now()
        removed = 0

        # Make a copy of keys to avoid modifying during iteration
        cache_keys = list(self._metadata["cache_entries"].keys())

        for key in cache_keys:
            entry = self._metadata["cache_entries"][key]
            created_at = datetime.fromisoformat(entry["created_at"])
            age = (now - created_at).total_seconds()

            if age > max_age:
                cache_path = self.cache_dir / f"{key}.pickle"
                if cache_path.exists():
                    try:
                        os.remove(cache_path)
                        removed += 1
                        del self._metadata["cache_entries"][key]
                    except (OSError, KeyError):
                        pass

        if removed > 0:
            self._save_metadata()

        return removed
