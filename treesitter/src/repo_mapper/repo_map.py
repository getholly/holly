"""
Repository mapping module that analyzes Python code with tree-sitter.
"""

import hashlib
import json
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar, cast

import tree_sitter
from loguru import logger
from tree_sitter_languages import get_language, get_parser

# Import RepoCache explicitly to fix the type error
from .repo_cache import RepoCache

T = TypeVar("T")


@dataclass
class CodeEntity:
    """Base class for code entities found in the repository."""

    name: str
    file_path: str
    start_line: int
    end_line: int
    docstring: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "docstring": self.docstring,
        }


@dataclass
class Function(CodeEntity):
    """Represents a function in the codebase."""

    parameters: list[str] = field(default_factory=list)
    return_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update(
            {
                "type": "function",
                "parameters": self.parameters,
                "return_type": self.return_type,
            },
        )
        return result


@dataclass
class Class(CodeEntity):
    """Represents a class in the codebase."""

    base_classes: list[str] = field(default_factory=list)
    methods: list[Function] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update(
            {
                "type": "class",
                "base_classes": self.base_classes,
                "methods": [method.to_dict() for method in self.methods],
            },
        )
        return result


@dataclass
class Module:
    """Represents a Python module in the codebase."""

    name: str
    file_path: str
    classes: list[Class] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "type": "module",
            "classes": [cls.to_dict() for cls in self.classes],
            "functions": [func.to_dict() for func in self.functions],
            "imports": self.imports,
        }


class RepoMap:
    """
    Class for mapping and analyzing Python repositories.

    This class uses tree-sitter to parse Python code and build a representation
    of the repository structure, including modules, classes, and functions.
    """

    def __init__(
        self,
        repo_path: str,
        cache: RepoCache | None = None,
        exclude_patterns: list[str] | None = None,
        max_cache_age: int | None = None,
    ) -> None:
        """
        Initialize the repository mapper.

        Args:
            repo_path: Path to the repository root
            cache: RepoCache instance for caching parsed data
            exclude_patterns: List of patterns to exclude from analysis
            max_cache_age: Maximum age of cache in seconds
        """
        self.repo_path = Path(repo_path).resolve()
        self.exclude_patterns = exclude_patterns or ["__pycache__", "*.pyc", ".*"]
        self.cache = cache or RepoCache()
        self.max_cache_age = max_cache_age

        # Initialize tree-sitter
        self.parser = self._setup_parser()

        # Repository data
        self.modules: dict[str, Module] = {}
        self.file_contents: dict[str, str] = {}
        self.file_paths: set[str] = set()

        # Cache key for this repository
        self.cache_key: str | None = None

        # Flag to indicate if the map has been built
        self._is_built = False

    def _setup_parser(self) -> tree_sitter.Parser:
        """
        Set up the tree-sitter parser for Python.

        Returns:
            Configured tree-sitter Parser instance
        """
        # Create and configure the parser
        parser = tree_sitter.Parser()

        try:
            import tree_sitter_python as tspython

            PY_LANGUAGE = tree_sitter.Language(tspython.language())
            parser = tree_sitter.Parser(PY_LANGUAGE)
            return parser

            # get the parsers
            PY_LANGUAGE = get_language("python")
            parser = get_parser("python")

            # Try to load from current working directory first
            cwd = os.getcwd()
            language_lib_path = os.path.join(cwd, ".cache/treesitter-langs")

            # Check if the Python language file exists
            py_lang_file = os.path.join(language_lib_path, "python.so")
            if os.path.exists(py_lang_file):
                PY_LANGUAGE = tree_sitter.Language(language_lib_path, "python")
                parser.set_language(PY_LANGUAGE)
                return parser

            # Fall back to repository parent location
            language_lib_path = os.path.join(str(self.repo_path.parent), ".cache/treesitter-langs")
            py_lang_file = os.path.join(language_lib_path, "python.so")
            if os.path.exists(py_lang_file):
                PY_LANGUAGE = tree_sitter.Language(language_lib_path, "python")
                parser.set_language(PY_LANGUAGE)
                return parser

            # If no language file found, suggest how to set it up
            raise FileNotFoundError(
                f"Could not find tree-sitter Python language file at {py_lang_file}.\n"
                f"Make sure to set up tree-sitter correctly by running:\n"
                f"git clone --depth=1 https://github.com/tree-sitter/tree-sitter-python .cache/tree-sitter-python\n"
                f"tree-sitter build-lib -o .cache/treesitter-langs\n"
                f"Alternatively, use the --mock flag for demonstration purposes.",
            )

        except Exception as e:
            # For any errors, suggest using the mock mode
            logger.exception(f"Warning: Failed to set up tree-sitter parser: {e}")
            logger.error("Tip: Use the --mock flag to run with mock data for demonstration purposes.")
            raise

        return parser

    def _matches_exclude_pattern(self, path: str) -> bool:
        """
        Check if a path matches any exclude pattern.

        Args:
            path: Path to check

        Returns:
            True if the path should be excluded, False otherwise
        """
        for pattern in self.exclude_patterns:
            if pattern.startswith("*."):
                # File extension pattern
                if path.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                # Directory prefix pattern
                if path.startswith(pattern[:-1]):
                    return True
            elif pattern in path:
                # Simple substring match
                return True
        return False

    def _find_python_files(self) -> Iterator[Path]:
        """
        Find all Python files in the repository.

        Yields:
            Path objects for each Python file
        """
        for root, dirs, files in os.walk(str(self.repo_path)):
            # Modify dirs in-place to exclude directories
            dirs[:] = [d for d in dirs if not self._matches_exclude_pattern(d)]

            for file in files:
                if file.endswith(".py") and not self._matches_exclude_pattern(file):
                    yield Path(root) / file

    def _extract_docstring(self, node: tree_sitter.Node, file_content: str) -> str | None:
        """
        Extract docstring from a function or class node.

        Args:
            node: tree-sitter node for function or class
            file_content: Content of the file

        Returns:
            Docstring text or None if no docstring was found
        """
        # Check for docstring (typically the first child in body that's a string)
        body = None
        for child in node.children:
            if child.type == "block":
                body = child
                break

        if not body:
            return None

        # Look for an expression statement containing a string
        for child in body.children:
            if child.type == "expression_statement":
                string_node = None
                for expr_child in child.children:
                    if expr_child.type in ("string", "string_literal"):
                        string_node = expr_child
                        break

                if string_node:
                    # Extract the content between quotes
                    docstring_text = file_content[string_node.start_byte : string_node.end_byte]
                    # Remove quotes and normalize
                    docstring_text = docstring_text.strip("'\"")
                    return docstring_text

        return None

    def _extract_parameter_names(self, func_node: tree_sitter.Node, file_content: str) -> list[str]:
        """
        Extract parameter names from a function definition.

        Args:
            func_node: tree-sitter node for the function
            file_content: Content of the file

        Returns:
            List of parameter names
        """
        params = []

        # Find the parameter list
        for child in func_node.children:
            if child.type == "parameters":
                # Process each parameter
                for param_child in child.children:
                    if param_child.type in ("identifier", "default_parameter", "typed_parameter"):
                        # For simple identifiers
                        if param_child.type == "identifier":
                            param_name = file_content[param_child.start_byte : param_child.end_byte].strip()
                            params.append(param_name)
                        # For more complex parameters (default or typed)
                        else:
                            # Find the identifier child
                            for param_part in param_child.children:
                                if param_part.type == "identifier":
                                    param_name = file_content[param_part.start_byte : param_part.end_byte].strip()
                                    params.append(param_name)
                                    break

        return params

    def _extract_return_type(self, func_node: tree_sitter.Node, file_content: str) -> str | None:
        """
        Extract return type annotation from a function definition.

        Args:
            func_node: tree-sitter node for the function
            file_content: Content of the file

        Returns:
            Return type as a string or None if not annotated
        """
        # Look for the return type annotation
        for child in func_node.children:
            if child.type == "type":
                return file_content[child.start_byte : child.end_byte].strip()

        return None

    def _extract_base_classes(self, class_node: tree_sitter.Node, file_content: str) -> list[str]:
        """
        Extract base classes from a class definition.

        Args:
            class_node: tree-sitter node for the class
            file_content: Content of the file

        Returns:
            List of base class names
        """
        bases = []

        # Find the argument list (holds base classes)
        for child in class_node.children:
            if child.type == "argument_list":
                # Process each argument as a base class
                for base_child in child.children:
                    if base_child.type == "identifier":
                        base_name = file_content[base_child.start_byte : base_child.end_byte].strip()
                        bases.append(base_name)

        return bases

    def _extract_imports(self, root_node: tree_sitter.Node, file_content: str) -> list[str]:
        """
        Extract import statements from a module.

        Args:
            root_node: tree-sitter root node for the module
            file_content: Content of the file

        Returns:
            List of import statements
        """
        imports = []

        # Query for import statements
        cursor = root_node.walk()

        def visit_node(node: tree_sitter.Node) -> None:
            if node.type in ("import_statement", "import_from_statement"):
                import_text = file_content[node.start_byte : node.end_byte].strip()
                imports.append(import_text)

        # Traverse the tree
        visit_node(root_node)
        for child in root_node.children:
            visit_node(child)

        return imports

    def _parse_file(self, file_path: Path) -> Module | None:
        """
        Parse a Python file and extract its structure.

        Args:
            file_path: Path to the Python file

        Returns:
            Module object representing the file or None if parsing failed
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                file_content = f.read()

            # Save content for cache key generation
            rel_path = str(file_path.relative_to(self.repo_path))
            self.file_contents[rel_path] = file_content
            self.file_paths.add(rel_path)

            # Parse the file
            tree = self.parser.parse(bytes(file_content, "utf-8"))

            # Create a module object
            module_name = file_path.stem
            module = Module(
                name=module_name,
                file_path=str(file_path.relative_to(self.repo_path)),
                classes=[],
                functions=[],
                imports=[],
            )

            # Extract imports
            module.imports = self._extract_imports(tree.root_node, file_content)

            # Process nodes
            cursor = tree.root_node.walk()

            # Process top-level definitions
            for child in tree.root_node.children:
                # Process class definitions
                if child.type == "class_definition":
                    # Get class name
                    class_name = None
                    for name_child in child.children:
                        if name_child.type == "identifier":
                            class_name = file_content[name_child.start_byte : name_child.end_byte]
                            break

                    if class_name:
                        # Create class object
                        cls = Class(
                            name=class_name,
                            file_path=str(file_path.relative_to(self.repo_path)),
                            start_line=child.start_point[0] + 1,
                            end_line=child.end_point[0] + 1,
                            docstring=self._extract_docstring(child, file_content),
                            base_classes=self._extract_base_classes(child, file_content),
                            methods=[],
                        )

                        # Look for methods
                        for class_child in child.children:
                            if class_child.type == "block":
                                for method_node in class_child.children:
                                    if method_node.type == "function_definition":
                                        # Get method name
                                        method_name = None
                                        for method_name_child in method_node.children:
                                            if method_name_child.type == "identifier":
                                                method_name = file_content[
                                                    method_name_child.start_byte : method_name_child.end_byte
                                                ]
                                                break

                                        if method_name:
                                            # Create function object
                                            method = Function(
                                                name=method_name,
                                                file_path=str(file_path.relative_to(self.repo_path)),
                                                start_line=method_node.start_point[0] + 1,
                                                end_line=method_node.end_point[0] + 1,
                                                docstring=self._extract_docstring(method_node, file_content),
                                                parameters=self._extract_parameter_names(method_node, file_content),
                                                return_type=self._extract_return_type(method_node, file_content),
                                            )
                                            cls.methods.append(method)

                        module.classes.append(cls)

                # Process function definitions
                elif child.type == "function_definition":
                    # Get function name
                    func_name = None
                    for name_child in child.children:
                        if name_child.type == "identifier":
                            func_name = file_content[name_child.start_byte : name_child.end_byte]
                            break

                    if func_name:
                        # Create function object
                        func = Function(
                            name=func_name,
                            file_path=str(file_path.relative_to(self.repo_path)),
                            start_line=child.start_point[0] + 1,
                            end_line=child.end_point[0] + 1,
                            docstring=self._extract_docstring(child, file_content),
                            parameters=self._extract_parameter_names(child, file_content),
                            return_type=self._extract_return_type(child, file_content),
                        )
                        module.functions.append(func)

            return module

        except Exception as e:
            logger.exception(f"Error parsing {file_path}: {e}")
            return None

    def _generate_cache_key(self) -> str:
        """
        Generate a cache key for the current repository state.

        Returns:
            Cache key string
        """
        if not self.file_paths:
            # If we haven't found files yet, do a quick scan
            for file_path in self._find_python_files():
                rel_path = str(file_path.relative_to(self.repo_path))
                self.file_paths.add(rel_path)
                # We don't need to load file contents yet, just tracking paths

        # Generate key
        hasher = hashlib.sha256()

        # Add repo path
        hasher.update(str(self.repo_path).encode("utf-8"))

        # Sort paths for consistent hashing
        sorted_paths = sorted(self.file_paths)

        for rel_path in sorted_paths:
            full_path = self.repo_path / rel_path
            if full_path.exists():
                # Use file content hash if available
                if rel_path in self.file_contents:
                    content_hash = hashlib.md5(self.file_contents[rel_path].encode("utf-8")).hexdigest()
                    hasher.update(f"{rel_path}:{content_hash}".encode())
                else:
                    # Otherwise use last modified time
                    mtime = full_path.stat().st_mtime
                    hasher.update(f"{rel_path}:{mtime}".encode())

        return hasher.hexdigest()

    def has_valid_cache(self) -> bool:
        """
        Check if there is a valid cache for this repository.

        Returns:
            True if valid cache exists, False otherwise
        """
        # Generate cache key if needed
        if not self.cache_key:
            self.cache_key = self._generate_cache_key()

        # Check if cache exists
        if self.cache.get(self.cache_key) is not None:
            return True

        return False

    def build(self, force: bool = False) -> dict[str, Any]:
        """
        Build the repository map.

        Args:
            force: Force rebuild even if cache is valid

        Returns:
            Dictionary containing the repository map data
        """
        # Generate cache key
        if not self.cache_key:
            self.cache_key = self._generate_cache_key()

        # Check cache first
        if not force and self.has_valid_cache():
            cache_data = self.cache.get(self.cache_key)
            if cache_data:
                self.modules = {}
                # Reconstruct modules from cache
                for module_data in cache_data.get("modules", []):
                    module = Module(
                        name=module_data["name"],
                        file_path=module_data["file_path"],
                        imports=module_data.get("imports", []),
                    )

                    # Reconstruct classes
                    for class_data in module_data.get("classes", []):
                        cls = Class(
                            name=class_data["name"],
                            file_path=class_data["file_path"],
                            start_line=class_data["start_line"],
                            end_line=class_data["end_line"],
                            docstring=class_data.get("docstring"),
                            base_classes=class_data.get("base_classes", []),
                        )

                        # Reconstruct methods
                        for method_data in class_data.get("methods", []):
                            method = Function(
                                name=method_data["name"],
                                file_path=method_data["file_path"],
                                start_line=method_data["start_line"],
                                end_line=method_data["end_line"],
                                docstring=method_data.get("docstring"),
                                parameters=method_data.get("parameters", []),
                                return_type=method_data.get("return_type"),
                            )
                            cls.methods.append(method)

                        module.classes.append(cls)

                    # Reconstruct functions
                    for func_data in module_data.get("functions", []):
                        func = Function(
                            name=func_data["name"],
                            file_path=func_data["file_path"],
                            start_line=func_data["start_line"],
                            end_line=func_data["end_line"],
                            docstring=func_data.get("docstring"),
                            parameters=func_data.get("parameters", []),
                            return_type=func_data.get("return_type"),
                        )
                        module.functions.append(func)

                    self.modules[module.file_path] = module

                self._is_built = True
                return cache_data

        # No valid cache or force rebuild
        self.modules = {}

        # Parse all Python files
        for file_path in self._find_python_files():
            maybe_module = self._parse_file(file_path)
            if maybe_module is not None:
                self.modules[maybe_module.file_path] = maybe_module

        # Create result data
        result = {
            "repo_path": str(self.repo_path),
            "file_count": len(self.modules),
            "modules": [module.to_dict() for module in self.modules.values()],
        }

        # Save to cache
        if self.cache_key:
            self.cache.put(self.cache_key, result, str(self.repo_path))

        self._is_built = True
        return result

    def get_class(self, class_name: str) -> Class | None:
        """
        Get a class by name.

        Args:
            class_name: Name of the class to find

        Returns:
            Class object or None if not found
        """
        if not self._is_built:
            self.build()

        for module in self.modules.values():
            for cls in module.classes:
                if cls.name == class_name:
                    return cls

        return None

    def get_function(self, function_name: str) -> Function | None:
        """
        Get a function by name.

        Args:
            function_name: Name of the function to find

        Returns:
            Function object or None if not found
        """
        if not self._is_built:
            self.build()

        for module in self.modules.values():
            for func in module.functions:
                if func.name == function_name:
                    return func

            # Also check methods
            for cls in module.classes:
                for method in cls.methods:
                    if method.name == function_name:
                        return method

        return None

    def get_module(self, module_path: str) -> Module | None:
        """
        Get a module by path.

        Args:
            module_path: Path to the module (relative to repo root)

        Returns:
            Module object or None if not found
        """
        if not self._is_built:
            self.build()

        if module_path in self.modules:
            return self.modules[module_path]

        # Try to normalize path
        normalized_path = str(Path(module_path))
        for path, module in self.modules.items():
            if normalized_path == str(Path(path)):
                return module

        return None

    def find_classes(self, pattern: str) -> list[Class]:
        """
        Find classes matching a pattern.

        Args:
            pattern: Regex pattern to match class names

        Returns:
            List of matching Class objects
        """
        if not self._is_built:
            self.build()

        regex = re.compile(pattern)
        results = []

        for module in self.modules.values():
            for cls in module.classes:
                if regex.search(cls.name):
                    results.append(cls)

        return results

    def find_functions(self, pattern: str) -> list[Function]:
        """
        Find functions matching a pattern.

        Args:
            pattern: Regex pattern to match function names

        Returns:
            List of matching Function objects
        """
        if not self._is_built:
            self.build()

        regex = re.compile(pattern)
        results = []

        for module in self.modules.values():
            for func in module.functions:
                if regex.search(func.name):
                    results.append(func)

            # Also search methods
            for cls in module.classes:
                for method in cls.methods:
                    if regex.search(method.name):
                        results.append(method)

        return results

    def find_by_docstring(self, pattern: str) -> list[CodeEntity]:
        """
        Find code entities with docstrings matching a pattern.

        Args:
            pattern: Regex pattern to match in docstrings

        Returns:
            List of matching CodeEntity objects
        """
        if not self._is_built:
            self.build()

        regex = re.compile(pattern)
        results: list[CodeEntity] = []

        for module in self.modules.values():
            for func in module.functions:
                if func.docstring and regex.search(func.docstring):
                    results.append(func)

            for cls in module.classes:
                if cls.docstring and regex.search(cls.docstring):
                    # Cast to CodeEntity to appease mypy
                    results.append(cast(CodeEntity, cls))

                for method in cls.methods:
                    if method.docstring and regex.search(method.docstring):
                        results.append(method)

        return results

    def get_inheritance_tree(self, class_name: str) -> dict[str, list[str]]:
        """
        Get the inheritance tree for a class.

        Args:
            class_name: Name of the class

        Returns:
            Dictionary mapping class names to their direct subclasses
        """
        if not self._is_built:
            self.build()

        # Build inheritance mapping
        inheritance_map: dict[str, list[str]] = {}

        # First, collect all classes
        for module in self.modules.values():
            for cls in module.classes:
                inheritance_map[cls.name] = []

        # Then, build the inheritance relationships
        for module in self.modules.values():
            for cls in module.classes:
                for base_cls in cls.base_classes:
                    if base_cls in inheritance_map:
                        inheritance_map[base_cls].append(cls.name)

        # Filter to include only the requested class and its descendants
        result = {}

        def add_class_and_descendants(cls: str) -> None:
            if cls in inheritance_map:
                result[cls] = inheritance_map[cls]
                for subcls in inheritance_map[cls]:
                    add_class_and_descendants(subcls)

        add_class_and_descendants(class_name)

        return result

    def get_module_dependencies(self) -> dict[str, list[str]]:
        """
        Get module dependencies based on imports.

        Returns:
            Dictionary mapping module paths to lists of imported modules
        """
        if not self._is_built:
            self.build()

        dependencies: dict[str, list[str]] = {}

        for module_path, module in self.modules.items():
            deps = []
            for import_stmt in module.imports:
                # Extract module name from import statement
                # This is a simple approximation; a proper parser would be better
                parts = import_stmt.split()
                if parts and parts[0] == "import":
                    for part in parts[1:]:
                        if part != "as" and not part.startswith("."):
                            module_name = part.split(".")[0].strip(",")
                            deps.append(module_name)
                elif parts and parts[0] == "from" and len(parts) > 1:
                    module_name = parts[1].split(".")[0]
                    if not module_name.startswith("."):
                        deps.append(module_name)

            dependencies[module_path] = deps

        return dependencies

    def find_function_calls(self, function_name: str) -> list[dict[str, Any]]:
        """
        Find all occurrences where a specific function is called in the repository.

        Args:
            function_name: The name of the function to search for calls to

        Returns:
            List of dictionaries with information about where the function is called:
            - file_path: Path to the file containing the call
            - caller_function: Name of the function containing the call (if applicable)
            - caller_class: Name of the class containing the call (if applicable)
            - line_number: Line number where the call appears
            - context: The line of code containing the call
        """
        if not self._is_built:
            self.build()

        results = []

        # Search through all modules
        for file_path, module in self.modules.items():
            try:
                # Read the file content
                with open(os.path.join(str(self.repo_path), file_path), encoding="utf-8") as f:
                    content = f.read()

                # Parse the file with tree-sitter
                tree = self.parser.parse(bytes(content, "utf-8"))

                # Find all function call nodes
                cursor = tree.root_node.walk()

                def find_calls(node, parent_func=None, parent_class=None):
                    # Process current node if it's a function call
                    if node.type == "call":
                        for child in node.children:
                            if (
                                child.type == "identifier"
                                and content[child.start_byte : child.end_byte] == function_name
                            ):
                                line_number = node.start_point[0] + 1
                                context = content.split("\n")[node.start_point[0]].strip()

                                results.append(
                                    {
                                        "file_path": file_path,
                                        "caller_function": parent_func,
                                        "caller_class": parent_class,
                                        "line_number": line_number,
                                        "context": context,
                                    },
                                )

                    # Track current function/class context
                    current_func = parent_func
                    current_class = parent_class

                    if node.type == "function_definition":
                        for child in node.children:
                            if child.type == "identifier":
                                current_func = content[child.start_byte : child.end_byte]
                                break

                    elif node.type == "class_definition":
                        for child in node.children:
                            if child.type == "identifier":
                                current_class = content[child.start_byte : child.end_byte]
                                break

                    # Process children recursively
                    for child in node.children:
                        find_calls(child, current_func, current_class)

                # Start recursive search from root
                find_calls(tree.root_node)

            except Exception as e:
                logger.exception(f"Error processing {file_path}: {e}")

        return results

    def find_string_literals(self, search_string: str) -> list[dict[str, Any]]:
        """
        Find occurrences of a string literal in the repository.

        Args:
            search_string: The string literal to search for

        Returns:
            List of dictionaries with information about where the string literal is used:
            - file_path: Path to the file containing the string
            - function_name: Name of the function containing the string (if applicable)
            - class_name: Name of the class containing the string (if applicable)
            - line_number: Line number where the string appears
            - context: The line of code containing the string
        """
        if not self._is_built:
            self.build()

        results = []

        # Search through all modules
        for file_path, module in self.modules.items():
            try:
                # Read the file content
                with open(os.path.join(str(self.repo_path), file_path), encoding="utf-8") as f:
                    content = f.read()

                # Find all instances of the string literal
                lines = content.split("\n")
                for line_idx, line in enumerate(lines):
                    # Check if the line contains the string literal with quotes
                    double_quote = f'"{search_string}"'
                    single_quote = f"'{search_string}'"

                    if double_quote in line or single_quote in line:
                        line_number = line_idx + 1
                        result = {
                            "file_path": file_path,
                            "line_number": line_number,
                            "context": line.strip(),
                            "function_name": None,
                            "class_name": None,
                        }

                        # Find containing function or method
                        for func in module.functions:
                            if func.start_line <= line_number <= func.end_line:
                                result["function_name"] = func.name
                                break

                        # Find containing class and method
                        for cls in module.classes:
                            if cls.start_line <= line_number <= cls.end_line:
                                result["class_name"] = cls.name
                                # Check methods
                                for method in cls.methods:
                                    if method.start_line <= line_number <= method.end_line:
                                        result["function_name"] = method.name
                                        break
                        results.append(result)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return results

    def to_json(self, output_path: str | None = None) -> str:
        """
        Convert the repository map to JSON.

        Args:
            output_path: Path to write JSON output (optional)

        Returns:
            JSON string representation of the repository map
        """
        if not self._is_built:
            self.build()

        data = {
            "repo_path": str(self.repo_path),
            "file_count": len(self.modules),
            "modules": [module.to_dict() for module in self.modules.values()],
        }

        json_str = json.dumps(data, indent=2)

        if output_path:
            with open(output_path, "w") as f:
                f.write(json_str)

        return json_str
