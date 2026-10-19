from django.contrib import admin

from .models import Review, ReviewRestriction


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Direct data management for the admin.

    The moderation fields are read-only here: hiding and restoring go
    through the back office's model methods, so the audit fields always
    agree with ``status``. Deleting here is Django's ordinary delete — it
    never creates a restriction, unlike an author deleting a hidden review.
    """

    list_display = ("product", "user", "rating", "status", "created_at", "edited_at")
    list_filter = ("status",)
    list_select_related = ("product", "user")
    search_fields = ("user__username", "product__name")
    readonly_fields = ("status", "hidden_by", "hidden_at", "hidden_reason")


@admin.register(ReviewRestriction)
class ReviewRestrictionAdmin(admin.ModelAdmin):
    """Restrictions, for viewing and permanent deletion only.

    A restriction only ever comes from an author deleting a hidden review,
    so it can't be added here, and its record of the hide can't be edited.
    Deleting one here lifts it, like the back office's Clear restriction.
    """

    list_display = (
        "user",
        "product",
        "hidden_reason",
        "hidden_by",
        "hidden_at",
        "created_at",
    )
    list_select_related = ("user", "product", "hidden_by")
    search_fields = ("user__username", "product__name")
    readonly_fields = (
        "user",
        "product",
        "hidden_reason",
        "hidden_by",
        "hidden_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False
