# RepoMap - Python Repository Analyzer

RepoMap is a Python library for analyzing Python code repositories using tree-sitter. It builds a detailed map of the repository structure, including modules, classes, functions, and their relationships.

## Features

- Parse Python code using tree-sitter for accurate syntax analysis
- Extract detailed information about classes, methods, functions, and their docstrings
- Track inheritance relationships between classes
- Analyze module dependencies
- Cache parsed repository data for improved performance
- Command-line interface for easy analysis

## Installation

Clone the repository and install:

```bash
git clone https://github.com/yourusername/repo-mapper.git
cd repo-mapper
pip install -e .
```

Ensure that tree-sitter is properly set up:

```bash
git clone --depth=1 https://github.com/tree-sitter/tree-sitter-python .cache/tree-sitter-python
tree-sitter build-lib -o .cache/treesitter-langs
```

## Usage

### Python API

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

### Command-line Interface

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

## Advanced Features

### Caching

RepoMap includes a caching system that stores parsed repository data to avoid re-parsing unchanged files. This significantly speeds up repeated analyses of the same repository.

```python
# Customize cache location
cache = RepoCache(cache_dir="/path/to/cache")
repo_map = RepoMap(repo_path="/path/to/repo", cache=cache)

# Force rebuild even if cache is valid
repo_map.build(force=True)

# Set maximum cache age
repo_map = RepoMap(repo_path="/path/to/repo", max_cache_age=604800)  # 1 week in seconds
```

### Code Search

```python
# Find docstrings matching a pattern
entities = repo_map.find_by_docstring(pattern="TODO")

# Get module dependencies
dependencies = repo_map.get_module_dependencies()
```

## License

MIT License
