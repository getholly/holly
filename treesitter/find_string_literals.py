#!/usr/bin/env python3
"""
Find string literals in a repository.

This is a standalone version of the string literal search feature,
which doesn't depend on tree-sitter or other libraries.
"""

import os
import re


def find_string_literals(repo_path, search_string, exclude_patterns=None, case_sensitive=False):
    """
    Find string literals in Python files.

    Args:
        repo_path: Path to the repository to search
        search_string: The string literal to search for
        exclude_patterns: List of patterns to exclude
        case_sensitive: Whether the search should be case-sensitive

    Returns:
        List of dictionaries with information about occurrences
    """
    results = []
    exclude_patterns = exclude_patterns or []

    # Helper function to check if path should be excluded
    def should_exclude(path):
        for pattern in exclude_patterns:
            if pattern.startswith("*."):
                if path.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                if path.startswith(pattern[:-1]):
                    return True
            elif pattern in path:
                return True
        return False

    # Simple function to detect if a line is inside a function definition
    def detect_context(file_lines, line_idx):
        function_name = None
        class_name = None

        # Look backwards for function/class definition
        current_indent = len(file_lines[line_idx]) - len(file_lines[line_idx].lstrip())

        for i in range(line_idx - 1, -1, -1):
            line = file_lines[i]
            indent = len(line) - len(line.lstrip())
            line = line.strip()

            # If we're at a lower indent level and find a function or class
            if indent < current_indent:
                if line.startswith("def "):
                    match = re.match(r"def\s+([^\s(]+)", line)
                    if match:
                        function_name = match.group(1)
                elif line.startswith("class "):
                    match = re.match(r"class\s+([^\s(:]+)", line)
                    if match:
                        class_name = match.group(1)

                # If we've found both or have reached module level, break
                if (function_name and class_name) or indent == 0:
                    break

        return function_name, class_name

    # Find all Python files in the repository
    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(d)]

        for file in files:
            if file.endswith(".py") and not should_exclude(file):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)

                try:
                    # Read the file
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    file_lines = content.splitlines()

                    # Look for string literals in the file
                    # Regular expressions for different string types
                    string_patterns = [
                        r"\"(.*?)\"",  # Double quoted strings
                        r"\'(.*?)\'",  # Single quoted strings
                        r"\"\"\"(.*?)\"\"\"",  # Triple double quoted strings
                        r"'''(.*?)'''",  # Triple single quoted strings
                    ]

                    # Prepare search string for case comparison
                    search_str = search_string.lower() if not case_sensitive else search_string

                    # Process each line in the file
                    for line_idx, line in enumerate(file_lines):
                        # Keep track of all strings found in this line
                        found_strings = []

                        # Apply each string pattern
                        for pattern in string_patterns:
                            matches = re.finditer(pattern, line, re.DOTALL)
                            for match in matches:
                                # Extract the string content (without quotes)
                                string_content = match.group(1)

                                # Compare with search string (apply case sensitivity)
                                if case_sensitive:
                                    if search_string in string_content:
                                        found_strings.append(string_content)
                                elif search_str in string_content.lower():
                                    found_strings.append(string_content)

                        # If we found strings with the search pattern, record the result
                        if found_strings:
                            # Find the context (function and class)
                            function_name, class_name = detect_context(file_lines, line_idx)

                            results.append(
                                {
                                    "file_path": rel_path,
                                    "line_number": line_idx + 1,
                                    "context": line.strip(),
                                    "function_name": function_name,
                                    "class_name": class_name,
                                    "matched_strings": found_strings,
                                },
                            )
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    return results


def print_results(results, search_string):
    """Print results in a user-friendly format."""
    if not results:
        print(f"No occurrences found for string literal: '{search_string}'")
        return

    print(f"\nFound {len(results)} occurrences of '{search_string}':")
    print("=" * 80)

    for result in results:
        file_path = result["file_path"]
        line_number = result["line_number"]
        context = result["context"]

        location = f"{file_path}:{line_number}"
        if result["class_name"]:
            location += f" in class {result['class_name']}"
            if result["function_name"]:
                location += f", function {result['function_name']}"
        elif result["function_name"]:
            location += f" in function {result['function_name']}"

        print(f"{location}")
        print(f"  {context}")
        if "matched_strings" in result:
            for string in result["matched_strings"]:
                print(f"  Matched: '{string}'")
        print("-" * 80)


def main():
    """Main entry point for the script."""
    # Parse arguments
    import argparse

    parser = argparse.ArgumentParser(description="Find string literals in a repository")
    parser.add_argument("repo_path", help="Path to the repository to search")
    parser.add_argument("search_string", help="String literal to search for")
    parser.add_argument("-e", "--exclude", nargs="+", help="Patterns to exclude")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive search")

    args = parser.parse_args()

    print(f"Searching for string literal: '{args.search_string}'")
    print(f"Repository: {args.repo_path}")
    if args.exclude:
        print(f"Excluding: {', '.join(args.exclude)}")
    if args.ignore_case:
        print("Case-insensitive search enabled")

    results = find_string_literals(
        args.repo_path,
        args.search_string,
        args.exclude,
        case_sensitive=not args.ignore_case,
    )
    print_results(results, args.search_string)


if __name__ == "__main__":
    main()
