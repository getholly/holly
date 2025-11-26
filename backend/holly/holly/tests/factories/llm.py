import factory

from holly.holly.models.llms import LLM


class LLMFactory(factory.django.DjangoModelFactory):
    """Factory for the LLM model."""

    class Meta:
        model = LLM

    name = factory.Sequence(lambda n: f"LLM {n}")
    system_prompt = "Test prompt"
