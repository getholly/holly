import pytest
from django.db.models import JSONField
from jsoneditor.forms import JSONEditor

from holly.holly.admin import MissionAdmin, MissionConversationAdmin, ToolsAdmin

pytestmark = pytest.mark.django_db


def test_tools_admin_uses_jsoneditor():
    assert ToolsAdmin.formfield_overrides[JSONField]["widget"] is JSONEditor


def test_mission_admin_uses_jsoneditor():
    assert MissionAdmin.formfield_overrides[JSONField]["widget"] is JSONEditor


def test_mission_conversation_admin_uses_jsoneditor():
    assert MissionConversationAdmin.formfield_overrides[JSONField]["widget"] is JSONEditor
