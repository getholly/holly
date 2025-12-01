import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from holly.holly.services.summary_service import agenerate_title_summary
from holly.holly.tests.factories.llm import LLMFactory
from holly.holly.api.tests.factories.users import UserFactory


@pytest.mark.django_db
def test_generate_title_summary_uses_litellm():
    llm = LLMFactory(name="Holly", full_name="test/model", base_url="http://api")
    user = UserFactory()
    mock_response = {"choices": [{"message": {"content": "short summary"}}]}
    with patch(
        "holly.holly.services.summary_service.litellm.acompletion",
        new=AsyncMock(return_value=mock_response),
    ) as mock_call:
        summary, branch = asyncio.run(agenerate_title_summary("some long text", user, llm))
    assert summary == "short summary"
    assert branch == "holly/short-summary"
    mock_call.assert_called_once()
    kwargs = mock_call.call_args.kwargs
    assert kwargs["model"] == "test/model"
    assert kwargs["api_base"] == "http://api"

