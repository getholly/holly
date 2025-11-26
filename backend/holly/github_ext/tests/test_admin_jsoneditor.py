import pytest
from django.db.models import JSONField
from jsoneditor.forms import JSONEditor

from holly.github_ext.admin import RepositoryDetailAdmin

pytestmark = pytest.mark.django_db


def test_repository_detail_admin_uses_jsoneditor():
    assert RepositoryDetailAdmin.formfield_overrides[JSONField]["widget"] is JSONEditor
