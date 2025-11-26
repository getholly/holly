"""Utility module for counting tokens in text files."""

from pathlib import Path

from llmrepo_lib.tokenizer import Tokenizer, count_tokens

from holly.github_ext.utils import is_text_file


def count_file_tokens(file_path: Path, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text file.

    Args:
        file_path (Path): The path to the file
        model (str, optional): The model to use for token counting. Defaults to "gpt-4".

    Returns:
        int: The number of tokens in the file, or 0 if the file is not a text file
    """
    if not is_text_file(file_path):
        return 0

    with file_path.open(encoding="utf-8") as f:
        content = f.read()
    return count_tokens(content, Tokenizer.TIKTOKEN, model)


def build_file_token_counts(repo_path: Path, model: str = "gpt-4") -> dict[str, int]:
    """
    Build a dictionary of file paths to token counts.

    Args:
        repo_path (Path): The path to the repository
        model (str, optional): The model to use for token counting. Defaults to "gpt-4".

    Returns:
        Dict[str, int]: A dictionary mapping file paths to token counts
    """
    token_counts = {}

    for file_path in repo_path.rglob("*"):
        if file_path.is_file() and ".git" not in str(file_path):
            rel_path = str(file_path.relative_to(repo_path))
            token_count = count_file_tokens(file_path, model)
            if token_count > 0:  # Only store counts for text files
                token_counts[rel_path] = token_count

    return token_counts
