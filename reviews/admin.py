from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Direct data management for the admin.

    The moderation fields are read-only here: hiding and restoring go
    through the back office's model methods, so the audit fields always
    agree with ``status``.
    """

    list_display = ("product", "user", "rating", "status", "created_at", "edited_at")
    list_filter = ("status",)
    list_select_related = ("product", "user")
    search_fields = ("user__username", "product__name")
    readonly_fields = ("status", "hidden_by", "hidden_at", "hidden_reason")
