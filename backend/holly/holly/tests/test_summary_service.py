import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from holly.holly.services.summary_service import agenerate_title_summary
from holly.holly.tests.factories.llm import LLMFactory


@pytest.mark.django_db
def test_generate_title_summary_uses_litellm():
    LLMFactory(name="Holly", full_name="test/model", base_url="http://api")
    mock_response = {"choices": [{"message": {"content": "short summary"}}]}
    with patch(
        "holly.holly.services.summary_service.litellm.acompletion",
        new=AsyncMock(return_value=mock_response),
    ) as mock_call:
        summary = asyncio.run(agenerate_title_summary("some long text"))
    assert summary == "short summary"
    mock_call.assert_called_once()
