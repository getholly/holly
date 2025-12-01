"""Utilities for generating short conversation titles using an LLM."""

from __future__ import annotations

import re

import litellm
from django.contrib.auth import get_user_model
from loguru import logger

from holly.holly.models import UserLLMApiKey
from holly.holly.models.llms import LLM

User = get_user_model()


def sanitize_git_branch_name(name: str) -> str:
    # 1. Convert whitespace to dash
    name = re.sub(r"\s+", "-", name)

    # 2. Remove invalid characters
    # Git disallows: space, ~ ^ : ? * [ \ and control characters (ASCII < 32)
    name = re.sub(r"[~^:?*\[\]\\]", "", name)
    name = re.sub(r"[\x00-\x1F\x7F]", "", name)

    # 3. Remove leading/trailing dots or slashes
    name = name.strip("./")

    # 4. Collapse multiple dashes
    name = re.sub(r"-{2,}", "-", name)

    # 5. Prevent branch from being empty
    return name or "default-branch"



async def agenerate_title_summary(text: str, user: User, llm: LLM) -> tuple[str, str]:
    """Return a 5 to 10 word summary of ``text`` using the provided LLM.

    Args:
        text: The text to summarize
        user: The user requesting the summary (required for API key)
        llm: LLM to use.

    Returns:
        A 5 to 10 word summary of ``text``
        A Valid branch name
    """
    api_key = ""
    try:
        try:
            key = await UserLLMApiKey.objects.aget(user=user, llm=llm)
            api_key = key.api_key
        except UserLLMApiKey.DoesNotExist:
            pass
    except Exception as ex:
        logger.error(f"Error fetching API key: {ex}")

    prompt = f"Summarize the following text in 5 to 10 words, do not include any pre or post amble: {text}"
    
    # Fix double path issue if present in base_url
    base_url = llm.base_url
    if base_url and "/chat/completions" in base_url:
        base_url = base_url.split("/chat/completions")[0]
    
    try:
        response = await litellm.acompletion(
            model=llm.full_name,
            api_base=base_url,
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            temperature=llm.temperature or 0.0,
            max_tokens=4096,
        )
        title = response["choices"][0]["message"]["content"].strip()
        branch_name = f"holly/{sanitize_git_branch_name(title)}"
        return title, branch_name
    except RuntimeError as ex:
        # Handle event loop closed error by falling back to sync version
        if "Event loop is closed" in str(ex) or "no running event loop" in str(ex):
            logger.warning(f"Event loop closed, falling back to sync title generation: {ex}")
            return generate_title_summary(text, user, llm)
        logger.error(f"LLM summary generation failed: {ex}")
        fallback_title = text[:50]
        return fallback_title, f"holly/{sanitize_git_branch_name(fallback_title)}"
    except Exception as ex:  # noqa: BLE001
        logger.error(f"LLM summary generation failed: {ex}")
        fallback_title = text[:50]
        return fallback_title, f"holly/{sanitize_git_branch_name(fallback_title)}"


def generate_title_summary(text: str, user: User, llm: LLM) -> tuple[str, str]:
    """Return a 5 to 10 word summary of ``text`` using the provided LLM.

    Args:
        text: The text to summarize
        user: The user requesting the summary (required for API key)
        llm: LLM to use.

    Returns:
        A 5 to 10 word summary of ``text``
        A Valid branch name
    """
    api_key = "sk-secret"
    try:
        try:
            key = UserLLMApiKey.objects.get(user=user, llm=llm)
            api_key = key.api_key
        except UserLLMApiKey.DoesNotExist:
            pass
    except Exception as ex:
        logger.error(f"Error fetching API key: {ex}")

    prompt = f"/no_think Summarize the following text in 5 to 10 words, do not include any pre or post amble: {text}"
    
    # Fix double path issue if present in base_url
    base_url = llm.base_url
    if base_url and "/chat/completions" in base_url:
        base_url = base_url.split("/chat/completions")[0]

    try:
        response = litellm.completion(
            model=llm.full_name,
            api_base=base_url,
            api_key=api_key,
            messages=[{"role": "user", "content": prompt}],
            temperature=llm.temperature or 0.0,
            max_tokens=4096,
        )
        title = response["choices"][0]["message"]["content"].strip()
        branch_name = f"holly/{sanitize_git_branch_name(title)}"
        return title, branch_name
    except Exception as ex:  # noqa: BLE001
        logger.error(f"LLM summary generation failed: {ex}")
        fallback_title = text[:50]
        return fallback_title, f"holly/{sanitize_git_branch_name(fallback_title)}"
