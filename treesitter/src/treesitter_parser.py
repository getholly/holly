#!/usr/bin/env python3
"""
A script that uses Tree-sitter to parse code files in a directory
and cache the parsed trees for quick reuse.
"""

import argparse
import hashlib
import pickle
import sys

# from typing import dict, list, optional, tuple
from datetime import datetime
from pathlib import Path

try:
    from tree_sitter import Language, Parser
except ImportError:
    print("Error: tree_sitter package is not installed.")
    print("Please install it with: pip install tree-sitter")
    sys.exit(1)

# Dictionary mapping file extensions to tree-sitter language names
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".c": "c",
    ".cpp": "cpp",
    ".rs": "rust",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".java": "java",
    ".html": "html",
    ".css": "css",
    ".svelte": "svelte",
    # Add more mappings as needed
}

# Path to store the language libraries
LANGUAGE_DIR = Path.home() / ".cache" / "treesitter-langs"


class TreeSitterParser:
    def __init__(self, cache_path: str = None):
        """
        Initialize the TreeSitterParser.

        Args:
            cache_path: Path to store the cache file. Defaults to ~/.cache/treesitter-cache.pkl
        """
        # Initialize parser
        self.parser = Parser()

        # Initialize language objects
        self.languages: dict[str, Language] = {}

        # Set cache path
        if cache_path is None:
            cache_dir = Path.home() / ".cache"
            cache_dir.mkdir(exist_ok=True)
            self.cache_path = cache_dir / "treesitter-cache.pkl"
        else:
            self.cache_path = Path(cache_path)

        # Initialize cache
        self.cache: dict[str, tuple[str, datetime, bytes]] = {}
        self.load_cache()

    def ensure_language(self, lang_name: str) -> bool:
        """
        Ensure a language is loaded.

        Args:
            lang_name: The name of the language to load

        Returns:
            True if language was loaded successfully, False otherwise
        """
        if lang_name in self.languages:
            return True

        try:
            # Create language directory if it doesn't exist
            LANGUAGE_DIR.mkdir(parents=True, exist_ok=True)

            # If you've already built the language files:
            lang_path = LANGUAGE_DIR / f"{lang_name}.so"

            if not lang_path.exists():
                print(f"Language library for {lang_name} not found at {lang_path}")
                print("To build language libraries, install the tree-sitter-cli and run:")
                print(f"tree-sitter build-lib -o {LANGUAGE_DIR}")
                return False

            # Load the language
            Language.build_library(
                # Store the library in the `build` directory
                str(lang_path),
                # Include one or more languages
                [f"tree-sitter-{lang_name}"],
            )

            self.languages[lang_name] = Language(str(lang_path), lang_name)
            self.parser.set_language(self.languages[lang_name])
            return True

        except Exception as e:
            print(f"Error loading language {lang_name}: {e}")
            return False

    def parse_file(self, file_path: str) -> bytes | None:
        """
        Parse a file and return the tree.

        Args:
            file_path: Path to the file to parse

        Returns:
            Serialized tree if successful, None otherwise
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            print(f"File not found: {file_path}")
            return None

        # Get file extension and determine language
        extension = path.suffix.lower()
        if extension not in LANGUAGE_MAP:
            print(f"Unsupported file type: {extension}")
            return None

        lang_name = LANGUAGE_MAP[extension]
        if not self.ensure_language(lang_name):
            return None

        # Check if file is in cache and up to date
        file_hash = self.get_file_hash(file_path)
        mtime = datetime.fromtimestamp(path.stat().st_mtime)

        if file_path in self.cache:
            cached_hash, cached_mtime, tree_bytes = self.cache[file_path]
            if cached_hash == file_hash and cached_mtime == mtime:
                print(f"Using cached tree for {file_path}")
                return tree_bytes

        # Parse the file
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            tree = self.parser.parse(content)
            tree_bytes = pickle.dumps(tree)

            # Update cache
            self.cache[file_path] = (file_hash, mtime, tree_bytes)
            return tree_bytes

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def parse_directory(self, directory: str, recursive: bool = True) -> int:
        """
        Parse all supported files in a directory.

        Args:
            directory: Path to the directory to parse
            recursive: Whether to parse subdirectories

        Returns:
            Number of files successfully parsed
        """
        parsed_count = 0
        dir_path = Path(directory)

        if not dir_path.exists() or not dir_path.is_dir():
            print(f"Directory not found: {directory}")
            return 0

        # Get all files in the directory
        files = []
        if recursive:
            for ext in LANGUAGE_MAP:
                files.extend(dir_path.glob(f"**/*{ext}"))
        else:
            for ext in LANGUAGE_MAP:
                files.extend(dir_path.glob(f"*{ext}"))

        # Process each file
        for file_path in files:
            print(f"Parsing {file_path}")
            tree_bytes = self.parse_file(str(file_path))
            if tree_bytes is not None:
                parsed_count += 1

        return parsed_count

    def load_cache(self) -> None:
        """Load the cache from disk if it exists."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "rb") as f:
                    self.cache = pickle.load(f)
                print(f"Loaded cache with {len(self.cache)} entries from {self.cache_path}")
            except Exception as e:
                print(f"Error loading cache: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def save_cache(self) -> None:
        """Save the cache to disk."""
        try:
            with open(self.cache_path, "wb") as f:
                pickle.dump(self.cache, f)
            print(f"Saved cache with {len(self.cache)} entries to {self.cache_path}")
        except Exception as e:
            print(f"Error saving cache: {e}")

    def get_file_hash(self, file_path: str) -> str:
        """
        Get the hash of a file's contents.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash of the file contents
        """
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            print(f"Error hashing file {file_path}: {e}")
            return ""


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Parse code files with Tree-sitter and cache the results.",
    )
    parser.add_argument(
        "directory",
        help="Directory to parse",
    )
    parser.add_argument(
        "--cache",
        help="Path to cache file",
        default=None,
    )
    parser.add_argument(
        "--no-recursive",
        help="Do not parse subdirectories",
        action="store_false",
        dest="recursive",
    )
    args = parser.parse_args()

    ts_parser = TreeSitterParser(args.cache)

    parsed_count = ts_parser.parse_directory(args.directory, args.recursive)
    print(f"Successfully parsed {parsed_count} files")

    ts_parser.save_cache()


if __name__ == "__main__":
    main()
