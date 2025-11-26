import pytest
from tree_sitter_languages import get_parser
from unittest.mock import patch

from src.repo_mapper.repo_map import RepoMap


@pytest.fixture
def repo_map(tmp_path):
    """Return a RepoMap instance with the real Python parser."""
    parser = get_parser("python")
    with patch("src.repo_mapper.repo_map.RepoMap._setup_parser", return_value=parser):
        yield RepoMap(str(tmp_path))


def parse_code(code: str):
    parser = get_parser("python")
    return parser.parse(code.encode("utf-8")).root_node.children[0]


def test_matches_exclude_pattern(repo_map: RepoMap) -> None:
    repo_map.exclude_patterns = ["*.pyc", "secret*", "ignored"]
    assert repo_map._matches_exclude_pattern("file.pyc") is True
    assert repo_map._matches_exclude_pattern("secret_folder/file.py") is True
    assert repo_map._matches_exclude_pattern("visible/file.py") is False


def test_extract_parameter_names(repo_map: RepoMap) -> None:
    code = "def foo(a, b=2, c: int):\n    pass"
    func_node = parse_code(code)
    names = repo_map._extract_parameter_names(func_node, code)
    assert names == ["a", "b", "c"]


def test_extract_return_type(repo_map: RepoMap) -> None:
    code = "def foo() -> str:\n    return 'x'"
    func_node = parse_code(code)
    ret = repo_map._extract_return_type(func_node, code)
    assert ret == "str"


def test_extract_base_classes(repo_map: RepoMap) -> None:
    code = "class Child(Base1, Base2):\n    pass"
    class_node = parse_code(code)
    bases = repo_map._extract_base_classes(class_node, code)
    assert bases == ["Base1", "Base2"]


def test_extract_imports(repo_map: RepoMap) -> None:
    code = "import os\nfrom sys import path\n"
    root_node = get_parser("python").parse(code.encode("utf-8")).root_node
    imports = repo_map._extract_imports(root_node, code)
    assert imports == ["import os", "from sys import path"]
