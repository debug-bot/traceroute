from django.contrib import admin
from .models import Router, SSHSettings, DataCenter, Category, Command, PopularCommand, CommandHistory
from django.conf import settings
from django.contrib import admin

admin.site.site_header = f"{settings.PROJECT_NAME} Administration"
admin.site.site_title = f"{settings.PROJECT_NAME} Admin Dashboard"
admin.site.index_title = f"Welcome to the {settings.PROJECT_NAME} Management System"

@admin.register(CommandHistory)
class CommandHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "timestamp", "command_summary")
    list_filter = ("user", "timestamp")
    search_fields = ("user__username", "command")
    readonly_fields = ("timestamp",)

    def command_summary(self, obj):
        """Return a truncated version of the command for display."""
        if obj.command:
            return (obj.command[:50] + "...") if len(obj.command) > 50 else obj.command
        return ""

    command_summary.short_description = "Command Summary"


@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
    # Fields to display in the admin list view
    list_display = ("ssh_settings", "type", "name", "asn", "ip", "version", "datacenter")

    # Add filters for these fields
    list_filter = ("type", "version", "datacenter")

    # Add a search bar for these fields
    search_fields = ("name", "ip", "datacenter")

    # Group related fields in the detail view
    fieldsets = (
        ("Router SSH Settings", {"fields": ("ssh_settings",)}),
        ("Router Details", {"fields": ("type", "name", "asn", "ip", "version")}),
        ("Location Information", {"fields": ("datacenter",)}),
    )

    # Enable ordering by fields
    ordering = ("type",)

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


@admin.register(PopularCommand)
class PopularCommandAdmin(admin.ModelAdmin):
    list_display = ("command", "timestamp")
    search_fields = ("command__label", "command__command")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)
