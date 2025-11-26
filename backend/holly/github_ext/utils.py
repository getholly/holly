import copy
from dataclasses import dataclass
from pathlib import Path
import magic



from loguru import logger

from holly.github_ext.constants import IGNORE_FILE_TYPE, IGNORE_FILE_TYPE_SEARCH, MAX_FILE_SIZE


def search_file(file: Path, search_term: str) -> bool:
    """
    Search for a term within the contents of a file.

    Args:
        file (Path): The file to search within.
        search_term (str): The term to search for.

    Returns:
        bool: True if the search term is found in the file contents, False otherwise.
    """

    if file.suffix in IGNORE_FILE_TYPE_SEARCH:
        return False

    try:
        with Path.open(file, encoding="utf-8") as f:
            content = f.read()
            if search_term.lower() in content.lower():
                return True
    except (UnicodeDecodeError, PermissionError):
        pass  # Ignore unreadable files

    return False


def file_tree_exclude(item: Path, file_types: set[str] | None) -> bool:
    if item.is_symlink() or not item.is_file():
        return True

    if file_types and item.suffix.lower() not in file_types:
        return True

    if item.suffix.lower() in IGNORE_FILE_TYPE:
        return True

    if not is_text_file(item):
        return True

    if item.stat().st_size > MAX_FILE_SIZE:  # noqa: SIM103
        return True

    return False


def is_text_file(file_path: Path) -> bool:
    """
    Check if a file is a text file by checking the MIME type.
    Dir will throw an error, so we need to catch it.

    Args:
        file_path:  The path to the file to check.

    Returns:
        bool:  True if the file is a text file, False otherwise

    """
    if file_path.is_dir():
        msg = f"{file_path} is a directory"
        raise IsADirectoryError(msg)

    # Check MIME type
    mime = magic.Magic(mime=True)
    try:
        file_type = mime.from_file(str(file_path))
    except magic.MagicException:
        return False

    return file_type.startswith("text")

@dataclass
class FileNode:
    name: str
    path: Path
    is_dir: bool
    children: list["FileNode"] | None = None

    def to_dict(self):
        return {
            "name": self.name,
            "path": str(self.path),  # Convert Path to string
            "is_dir": self.is_dir,
            "children": [child.to_dict() for child in self.children] if self.children else None,
        }

    @staticmethod
    def from_dict(data: dict):
        return FileNode(
            name=data["name"],
            path=Path(data["path"]),
            is_dir=data["is_dir"],
            children=[FileNode.from_dict(child) for child in data["children"]] if data["children"] else None,
        )


def build_file_tree(path: Path, file_types: set[str] | None = None, search_term: str | None = None) -> list[FileNode]:  # noqa: C901
    """
    Recursively build a file tree structure from the given git repo directory path.
    Allows filtering by file type and searching for a term within file contents.
    Excludes the .git directory.
    Excludes binary files and files larger than MAX_FILE_SIZE.
    Excludes symlinks.

    Args:
        path (Path): The root directory path to build the file tree from.
        file_types:  A set of file types to include in the tree.
        search_term (str, optional): A string to search within file contents.

    Returns:
        list[dict]: A filtered list of dictionaries representing the file tree structure.
                    Each dictionary contains:
                    - 'name': The name of the file or directory.
                    - 'path': The path of the file or directory relative to the root path.
                    - 'is_dir': A boolean indicating if it is a directory.
                    - 'children' (optional): A list of child nodes if it is a directory
    """

    def _build_file_tree_recursive(  # noqa: C901
        path: Path,
        file_types: set[str] | None = None,
        search_term: str | None = None,
        path_context: Path | None = None,
    ):
        if file_types:
            file_types = set(map(str.lower, file_types))
        if path_context is None:
            path_context = copy.deepcopy(path)
        tree = []
        if not path.exists():
            msg = f"Directory not found: {path}"
            raise FileNotFoundError(msg)

        for item in sorted(path.iterdir()):
            node = FileNode(
                name=item.name,
                path=item.relative_to(path_context),
                is_dir=item.is_dir(),
            )

            if node.is_dir:
                if item.name == ".git":
                    continue

                children = _build_file_tree_recursive(item, file_types, search_term, path_context)
                if children:  # Only include directories that have matching children
                    node.children = children
                    tree.append(node)

            else:
                if file_tree_exclude(item, file_types):
                    continue

                if search_term:
                    if search_file(item, search_term):
                        tree.append(node)
                else:
                    tree.append(node)
        return tree

    return _build_file_tree_recursive(path, file_types, search_term)


@dataclass
class FileContent:
    name: str
    path: Path
    content: str


def get_files_as_content(file_list: list[str], root_path: Path) -> dict[str, FileContent]:
    file_contents = {}
    for file in file_list:
        if file.startswith(("/", "..")) or file.find("/../") != -1:
            logger.error(f"Invalid file path: {file}")
            continue

        full_path = root_path / Path(file)
        content = full_path.read_text(errors="replace")
        file_contents[file] = FileContent(full_path.name, full_path, content)
    return file_contents


def get_existing_files_as_content(file_directory_tree: list[FileNode], root_path: Path) -> dict[str, FileContent]:
    """
    Get the content of existing files in the file tree.
    This function receives user input and should be considered unsafe. It should be heavily validated.

    Args:
        file_directory_tree: The file tree structure.
        root_path: The root path of the file tree.

    Returns:
        dict[str, FileContent]: A dict of FileContent objects representing the existing files in the tree.

    """
    file_contents = {}

    def traverse_tree(tree: list[FileNode], current_path: Path) -> None:
        for item in tree:
            full_path = current_path / item.path
            if full_path.exists():
                if not full_path.is_dir():
                    if file_tree_exclude(full_path, None):
                        continue
                    content = full_path.read_text(errors="replace")
                    file_contents[str(item.path)] = FileContent(item.name, full_path, content)
                else:
                    traverse_tree(item.children, root_path)

    traverse_tree(file_directory_tree, root_path)

    return file_contents
