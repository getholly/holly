#!/usr/bin/env python3
"""
Script to run mypy type checking on the repository.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run mypy type checking")
    parser.add_argument(
        "--path",
        type=str,
        default="examples/python",
        help="Path to check (default: examples/python)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="mypy.ini",
        help="Path to mypy config file (default: mypy.ini)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output",
    )
    return parser.parse_args()


def run_mypy(path: str, config_file: str, verbose: bool) -> int:
    """Run mypy on the specified path.

    Args:
        path: Directory or file to type check
        config_file: Path to mypy config file
        verbose: Whether to show verbose output

    Returns:
        Exit code from mypy
    """
    cmd = ["mypy"]

    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            cmd.extend(["--config-file", str(config_path)])
        else:
            print(f"Warning: Config file {config_file} not found")

    if verbose:
        cmd.append("--verbose")

    cmd.append(path)

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=not verbose, check=False)

    if result.returncode == 0:
        print("✅ Mypy check passed")
    else:
        if not verbose:
            print(result.stdout.decode())
            print(result.stderr.decode())
        print("❌ Mypy check failed")

    return result.returncode


def main() -> int:
    """Main function."""
    args = parse_args()
    return run_mypy(args.path, args.config, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
