from uuid import uuid4

import factory

from holly.holly.models.mission_conversation import MissionConversation

from .missions import MissionFactory


class MissionConversationFactory(factory.django.DjangoModelFactory):
    """Factory for MissionConversation."""

    class Meta:
        model = MissionConversation

    mission = factory.SubFactory(MissionFactory)
    conversation_id = factory.LazyFunction(lambda: str(uuid4()))
    title = factory.Faker("sentence")
