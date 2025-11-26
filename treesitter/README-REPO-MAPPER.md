# RepoMap - Python Repository Analyzer

RepoMap is a Python library that uses tree-sitter to analyze Python code repositories. It parses the code, builds an AST (Abstract Syntax Tree), and creates a structured representation of your codebase, including modules, classes, functions, and their relationships.

## Features

- Parse Python code using tree-sitter for accurate syntax analysis
- Extract detailed information about classes, methods, functions, and docstrings
- Track inheritance relationships between classes
- Analyze module dependencies
- Cache parsed repository data for improved performance
- Command-line interface for easy analysis

## Installation

### Prerequisites

You need to have tree-sitter installed and set up for Python:

```bash
git clone --depth=1 https://github.com/tree-sitter/tree-sitter-python .cache/tree-sitter-python
tree-sitter build-lib -o .cache/treesitter-langs
```

### Package Dependencies

The library depends on:

- tree-sitter
- mypy (for type checking)
- pytest (for testing)

## Python API

```python
from repo_mapper import RepoMap, RepoCache

# Create a repository map
repo_map = RepoMap(repo_path="/path/to/your/repo")

# Build the map
result = repo_map.build()

# Find classes and functions
classes = repo_map.find_classes(pattern="Test.*")
functions = repo_map.find_functions(pattern="test_.*")

# Get inheritance relationships
inheritance = repo_map.get_inheritance_tree("BaseClass")

# Export to JSON
repo_map.to_json(output_path="repo_map.json")
```

### Caching

RepoMap includes a caching system that stores parsed repository data to avoid re-parsing unchanged files:

```python
# Customize cache location
cache = RepoCache(cache_dir="/path/to/cache")
repo_map = RepoMap(repo_path="/path/to/repo", cache=cache)

# Force rebuild even if cache is valid
repo_map.build(force=True)

# Set maximum cache age
repo_map = RepoMap(repo_path="/path/to/repo", max_cache_age=604800)  # 1 week in seconds
```

## Command-Line Interface

Use the included shell script to analyze repositories:

```bash
# Basic usage
./repo-map /path/to/your/repo

# Output to file
./repo-map /path/to/your/repo --output repo_map.json

# Exclude patterns
./repo-map /path/to/your/repo --exclude "__pycache__" "*.pyc" ".git"

# Clean old cache entries
./repo-map /path/to/your/repo --clean-cache --max-cache-age 604800
```

## Data Structures

The library provides several data classes for representing code entities:

- `CodeEntity`: Base class for code entities
- `Function`: Represents a function or method
- `Class`: Represents a class with methods and inheritance information
- `Module`: Represents a Python module (file) with its classes and functions

## Advanced Features

### Code Search

```python
# Find docstrings matching a pattern
entities = repo_map.find_by_docstring(pattern="TODO")

# Get module dependencies
dependencies = repo_map.get_module_dependencies()
```

## Type Checking

RepoMap is fully typed and can be checked with mypy:

```bash
./run_mypy.sh --path src/repo_mapper
```

## Testing

Run the unit tests with:

```bash
uv run python -m pytest tests/repo_mapper
```

## Project Structure

- `src/repo_mapper/repo_map.py`: Main RepoMap implementation
- `src/repo_mapper/repo_cache.py`: Caching functionality
- `src/repo_mapper/cli/`: Command-line interface
- `tests/repo_mapper/`: Unit and integration tests

## Future Improvements

Potential enhancements for the project:

- Support for additional languages beyond Python
- More advanced code analysis features
- Integration with code quality tools
- Visualization of code relationships
- Performance optimizations for very large repositories

## Typer CLI

We've created an enhanced command-line interface using Typer and Rich for a more user-friendly experience:

```bash
# Basic usage
./repomap analyze /path/to/your/repo

# Show detailed statistics
./repomap analyze /path/to/your/repo --detailed

# Specify cache directory
./repomap analyze /path/to/your/repo --cache-dir .cache/myrepo

# Output to file
./repomap analyze /path/to/your/repo --output repo_map.json

# Exclude patterns
./repomap analyze /path/to/your/repo --exclude "__pycache__" "*.pyc" ".git"

# Clean old cache entries
./repomap analyze /path/to/your/repo --clean-cache --max-cache-age 604800

# Get help
./repomap --help
./repomap analyze --help
```

The Typer CLI provides:

- Colorful output with Rich
- Progress indicators
- Tabular statistics
- Detailed analysis options
- Comprehensive help documentation

## Using the CLI

We've built a modern CLI tool using Typer and Rich that provides a user-friendly interface with colorful output and detailed statistics:

```bash
# Basic usage
./repomap examples/python

# For demos without tree-sitter setup
./repomap --mock examples/python

# Get detailed statistics
./repomap --mock --detailed examples/python

# Save output to a file
./repomap --mock --output analysis.json examples/python

# Get help
./repomap --help
```

The CLI provides:

- Colorful and well-formatted terminal output using Rich
- Live progress indicators
- Mock mode for demonstrations when tree-sitter isn't set up
- Detailed statistics about your codebase
- JSON export for further analysis
