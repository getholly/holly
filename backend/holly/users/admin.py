from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "last_login",
        "is_superuser",
        "is_staff",
        "is_active",
        "date_joined",
        "name",
        "stripe_customer_id",
    )
    list_filter = (
        "last_login",
        "is_superuser",
        "is_staff",
        "is_active",
        "date_joined",
    )
    raw_id_fields = ("groups", "user_permissions")
    search_fields = ("name",)
