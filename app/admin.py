from django.contrib import admin
from .models import Router, SSHSettings, DataCenter, Category, Command

@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
    # Fields to display in the admin list view
    list_display = ("ssh_settings", "type", "name", "asn", "ip", "version", "city", "state", "country")

    # Add filters for these fields
    list_filter = ("type", "version", "city", "state", "country")

    # Add a search bar for these fields
    search_fields = ("name", "ip", "city", "state", "country")

    # Group related fields in the detail view
    fieldsets = (
        ("Router SSH Settings", {"fields": ("ssh_settings",)}),
        ("Router Details", {"fields": ("type", "name", "asn", "ip", "version")}),
        ("Location Information", {"fields": ("city", "state", "country")}),
    )

    # Enable ordering by fields
    ordering = ("name", "type")

    # Pagination in the admin list view
    list_per_page = 20

@admin.register(SSHSettings)
class SSHSettingsAdmin(admin.ModelAdmin):
    list_display = ("settings_name", "port", "username", "password")


@admin.register(DataCenter)
class DataCenterAdmin(admin.ModelAdmin):
    list_display = ("city", "state", "country")
    search_fields = ("city", "state", "country")
    list_filter = ("country", "state")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ("label", "command", "purpose", "category")
    search_fields = ("label", "command", "purpose")
    list_filter = ("category",)
