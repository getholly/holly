# ruff: noqa
from enum import Enum

import tiktoken
import transformers
from loguru import logger

from llmrepo_lib import token_counter


class Tokenizer(str, Enum):
    TIKTOKEN_CL100K = "tiktoken-cl100k"  # GPT-4, GPT-3.5
    TIKTOKEN_P50K = "tiktoken-p50k"  # GPT-3
    LLAMA = "llama"  # Llama models
    TIKTOKEN = "tiktoken"


def get_tokenizer(tokenizer: str):
    """Get the appropriate tokenizer instance"""
    if tokenizer == Tokenizer.TIKTOKEN_CL100K:
        return tiktoken.get_encoding("cl100k_base")
    if tokenizer == Tokenizer.TIKTOKEN_P50K:
        return tiktoken.get_encoding("p50k_base")
    if tokenizer == Tokenizer.LLAMA:
        return transformers.AutoTokenizer.from_pretrained(
            "meta-llama/Llama-2-7b-hf",
            trust_remote_code=True,
        )
    raise ValueError(f"Unsupported tokenizer: {tokenizer}")


def count_tokens(text: str, tokenizer_name: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using the specified tokenizer

    Args:
        text: The text to count tokens in
        tokenizer_name: The tokenizer to use

    Returns:
        Number of tokens
    """
    if tokenizer_name == Tokenizer.TIKTOKEN:
        logger.info(f"Using tiktoken: {model}")
        return token_counter.count_string_tokens(text, model)

    logger.info(f"Counting tokens using {tokenizer_name}")
    tokenizer = get_tokenizer(tokenizer_name)

    if isinstance(tokenizer, transformers.PreTrainedTokenizer):
        return len(tokenizer.encode(text))
    # tiktoken encodings
    return len(tokenizer.encode(text))
