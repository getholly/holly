from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from holly.analytics.models import LLMQuery, Repository, RepoView

QUERY_PREVIEW_LENGTH = 50


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "repo_name",
        "private",
        "timestamp",
        "repo_link",
    )
    list_filter = ("timestamp", "private")
    search_fields = ("username", "repo_name")
    date_hierarchy = "timestamp"
    readonly_fields = ("timestamp",)

    @admin.display(description=_("View on GitHub"))
    def repo_link(self, obj):
        return format_html(
            '<a href="https://github.com/{}/{}" target="_blank">{}/{}</a>',
            obj.username,
            obj.repo_name,
            obj.username,
            obj.repo_name,
        )


@admin.register(RepoView)
class RepoViewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "repo",
        "timestamp",
    )
    list_filter = ("timestamp", "repo")
    search_fields = ("repo__username", "repo__repo_name", "user__email")
    date_hierarchy = "timestamp"
    readonly_fields = ("timestamp",)

    def has_add_permission(self, request):
        # Disable manual addition of analytics
        return False


@admin.register(LLMQuery)
class LLMQueryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "repo",
        "query_preview",
        "model_name",
        "timestamp",
    )
    list_filter = ("timestamp", "model_name", "repo")
    search_fields = ("repo__username", "repo__repo_name", "user__email", "query_text")
    date_hierarchy = "timestamp"
    readonly_fields = ("timestamp",)
    fieldsets = (
        (None, {"fields": ("user", "repo", "query_text")}),
        (_("Technical Details"), {"fields": ("model_name", "timestamp")}),
    )

    @admin.display(description=_("Query"))
    def query_preview(self, obj):
        return obj.query_text[:QUERY_PREVIEW_LENGTH] + ("..." if len(obj.query_text) > QUERY_PREVIEW_LENGTH else "")

    def has_add_permission(self, request):
        # Disable manual addition of analytics
        return False
