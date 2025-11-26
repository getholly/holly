from django.contrib import admin
from django.db.models import JSONField
from jsoneditor.forms import JSONEditor

from .models import (
    LLM,
    Knowledge,
    Message,
    Mission,
    MissionConversation,
    Tools,
    UserLLMApiKey,
)
from .models.mission import MissionRepos


@admin.register(Knowledge)
class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "summary", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name",)
    date_hierarchy = "created_at"


@admin.register(LLM)
class LLMAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "full_name",
        "base_url",
        "top_p",
        "top_k",
        "min_p",
        "temperature",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("name",)
    date_hierarchy = "created_at"


@admin.register(UserLLMApiKey)
class UserLLMApiKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "llm", "created_at", "updated_at")
    search_fields = ("user__email", "llm__name")
    list_filter = ("llm", "user")
    date_hierarchy = "created_at"


@admin.register(Tools)
class ToolsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "config",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("name",)
    date_hierarchy = "created_at"
    formfield_overrides = {JSONField: {"widget": JSONEditor}}


@admin.register(MissionRepos)
class MissionReposAdmin(admin.ModelAdmin):
    list_display = ("id", "repository", "branch_name")
    list_filter = ("repository",)


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "description",
        "llm",
        "state",
        "created_at",
        "updated_at",
        "owner",
        "branch_name",
        "container_id",
        "requirements",
    )
    list_filter = ("created_at", "updated_at", "owner")
    raw_id_fields = (
        "collaborators",
        "repositories",
        "knowledge_items",
        "tools",
    )
    date_hierarchy = "created_at"
    formfield_overrides = {JSONField: {"widget": JSONEditor}}


class MessageInline(admin.TabularInline):
    model = Message
    extra = 1  # Number of empty forms to display
    fields = ("role", "content", "created_at")
    readonly_fields = ("created_at",)  # Make created_at read-only


@admin.register(MissionConversation)
class MissionConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "mission",
        "conversation_id",
        "title",
        "created_at",
        "updated_at",
        "is_summarized",
        "summary",
        "remaining_tasks",
    )
    list_filter = ("mission", "created_at", "updated_at", "is_summarized")
    date_hierarchy = "created_at"
    inlines = [MessageInline]  # Add the inline to display Message objects
    formfield_overrides = {JSONField: {"widget": JSONEditor}}


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "content", "created_at")
    list_filter = ("conversation", "created_at")
    date_hierarchy = "created_at"
