#!/usr/bin/env python3
"""
Command-line interface for the repo_mapper.
"""

import argparse
import json
import sys

from ..repo_cache import RepoCache
from ..repo_map import RepoMap


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Map Python repositories using tree-sitter",
    )

    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to the repository to analyze",
    )

    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="Path to the cache directory (default: ~/.repo_mapper_cache)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output JSON file (default: stdout)",
    )

    parser.add_argument(
        "--exclude",
        type=str,
        nargs="+",
        default=None,
        help="Patterns to exclude from analysis",
    )

    parser.add_argument(
        "--max-cache-age",
        type=int,
        default=None,
        help="Maximum age of cache entries in seconds",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild even if cache is valid",
    )

    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="Clean old cache entries",
    )

    return parser.parse_args()


def main() -> int:
    """Run the command-line interface."""
    args = parse_args()

    try:
        # Create the cache
        cache = RepoCache(cache_dir=args.cache_dir)

        # Clean cache if requested
        if args.clean_cache and args.max_cache_age:
            removed = cache.clean(args.max_cache_age)
            print(f"Cleaned {removed} old cache entries")

        # Create the repo map
        repo_map = RepoMap(
            repo_path=args.repo_path,
            cache=cache,
            exclude_patterns=args.exclude,
            max_cache_age=args.max_cache_age,
        )

        # Build the map
        print(f"Analyzing repository: {args.repo_path}")
        if repo_map.has_valid_cache() and not args.force:
            print("Using cached data")
        else:
            print("Building repository map...")

        result = repo_map.build(force=args.force)

        # Output the result
        if args.output:
            repo_map.to_json(args.output)
            print(f"Repository map written to {args.output}")
        else:
            # Format JSON output for stdout
            json_output = json.dumps(result, indent=2)
            print(json_output)

        print(f"Found {result['file_count']} Python files")

        # Show some stats
        class_count = 0
        function_count = 0

        for module in result["modules"]:
            class_count += len(module.get("classes", []))
            function_count += len(module.get("functions", []))

            # Count methods too
            for cls in module.get("classes", []):
                function_count += len(cls.get("methods", []))

        print(f"Found {class_count} classes and {function_count} functions/methods")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
