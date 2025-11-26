from typing import ClassVar

from django.contrib import admin
from django.db.models import JSONField
from jsoneditor.forms import JSONEditor

from .models import GitHubAppInstallation, RepositoryDetail


@admin.register(RepositoryDetail)
class RepositoryDetailAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "repo",
        "commit_hash",
        "stargazers_count",
        "watchers_count",
        "forks_count",
        "open_issues_count",
        "subscribers_count",
        "size",
        "private",
        "file_count",
        "updated_at",
    )
    list_filter = ("private", "updated_at")
    search_fields = ("username", "repo", "description")
    date_hierarchy = "updated_at"
    formfield_overrides: ClassVar = {JSONField: {"widget": JSONEditor}}


@admin.register(GitHubAppInstallation)
class GitHubAppInstallationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "social_account",
        "installation_id",
        "account_name",
        "account_type",
        "installed_at",
    )
    search_fields = ("account_name", "installation_id")
    raw_id_fields = ("social_account",)
    list_filter = ("social_account", "installed_at")
