from django.contrib import admin
from .models import Router


@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
    # Fields to display in the admin list view
    list_display = ("type", "name", "asn", "ip", "version", "city", "state", "country")

    # Add filters for these fields
    list_filter = ("type", "version", "city", "state", "country")

    # Add a search bar for these fields
    search_fields = ("name", "ip", "city", "state", "country")

    # Group related fields in the detail view
    fieldsets = (
        ("Router Details", {"fields": ("type", "name", "asn", "ip", "version")}),
        ("Location Information", {"fields": ("city", "state", "country")}),
    )

    # Enable ordering by fields
    ordering = ("name", "type")

    # Pagination in the admin list view
    list_per_page = 20
