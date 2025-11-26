import pytest
from asgiref.sync import async_to_sync

from holly.holly.api.tests.factories.users import UserFactory
from holly.holly.api.views.conversations import get_model_config
from holly.holly.models import UserLLMApiKey
from holly.holly.tests.factories.llm import LLMFactory


@pytest.mark.django_db
def test_api_key_persisted_and_retrieved():
    user = UserFactory()
    llm = LLMFactory()
    key_value = "secret123"
    record = UserLLMApiKey.objects.create(user=user, llm=llm, api_key=key_value)

    fetched = UserLLMApiKey.objects.get(pk=record.pk)
    assert fetched.api_key == key_value


@pytest.mark.django_db
def test_get_model_config_returns_user_key():
    user = UserFactory()
    llm = LLMFactory()
    UserLLMApiKey.objects.create(user=user, llm=llm, api_key="abc")

    config = async_to_sync(get_model_config)(user, llm.id)
    assert config.api_key == "abc"


@pytest.mark.django_db
def test_get_model_config_without_key_returns_empty():
    user = UserFactory()
    llm = LLMFactory()

    config = async_to_sync(get_model_config)(user, llm.id)
    assert config.api_key == ""
