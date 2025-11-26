# String Literal Search Feature for RepoMap

## Overview

This feature extends the RepoMap library with the ability to find string literals in a repository. It can locate strings used in Python code and show where they are used, including the containing function and class.

## Usage

```bash
# Basic usage
./repomap find-strings /path/to/repo "your string literal"

# With exclusion patterns
./repomap find-strings /path/to/repo "your string literal" --exclude "__pycache__" "*.pyc"

# Using mock mode for demo without tree-sitter
./repomap find-strings /path/to/repo "your string literal" --mock
```

## Implementation

The string literal search functionality is implemented in two main components:

1. `find_string_literals.py` - A standalone script that can find string literals in Python files without requiring tree-sitter.

2. `repomap` CLI integration - The string search feature is integrated with the main RepoMap CLI tool.

### Features

- Case-insensitive search by default
- Support for string literals with different quote styles (single, double, triple)
- Detection of containing function and class
- Display of line context
- Compatibility with the existing RepoMap CLI interface
- Mock mode for demonstration purposes

### Benefits

This implementation offers several advantages:

- **Independence from tree-sitter**: Works even if tree-sitter libraries are not set up correctly
- **Better performance**: Direct file scanning is faster than full AST parsing for simple string searches
- **More robust**: Avoids common issues with external parser dependencies

## Implementation Details

The string literal search is implemented using Python's built-in file handling and regular expressions. It scans Python files for string literals matching the search pattern and uses indentation analysis to determine the containing function and class.

To maintain compatibility with the original RepoMap CLI interface, a wrapper script is used to integrate the standalone implementation with the existing command-line structure.

## Future Improvements

Potential enhancements for this feature:

- Support for more advanced search patterns (regex)
- Indexing for faster searches on large repositories
- Search across multiple file types (JavaScript, Java, etc.)
- Integration with the core RepoMap AST analysis for more context-aware searches
