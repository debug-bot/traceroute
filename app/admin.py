from django.contrib import admin
from django.shortcuts import render
from .models import (
    Alert,
    AlertRule,
    Configuration,
    Latency,
    Router,
    SSHSettings,
    DataCenter,
    Category,
    Command,
    PopularCommand,
    CommandHistory,
)
from django.conf import settings
from django.contrib import admin
from django.core.management import call_command
from django.utils.safestring import mark_safe
import io
from contextlib import redirect_stdout
from django.urls import path


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

    ordering = ("-timestamp",)

    # Pagination in the admin list view
    list_per_page = 20


@admin.register(Router)
class RouterAdmin(admin.ModelAdmin):
    # Fields to display in the admin list view
    list_display = (
        "ssh_settings",
        "type",
        "name",
        "asn",
        "ip",
        "version",
        "datacenter",
        "status",
        "only_monitor",
        "last_pings",
        "updated_at",
        "cpu_usage",
        "mem_usage",
        "storage_usage",
        "uptime_percentage",
        "total_pings",
        "successful_pings",
        "consecutive_failures",
    )

    # Add filters for these fields
    list_filter = ("type", "version", "datacenter", "status", "only_monitor")

    # Add a search bar for these fields
    search_fields = ("name", "ip", "datacenter")

    # Group related fields in the detail view
    fieldsets = (
        ("Router SSH Settings", {"fields": ("ssh_settings",)}),
        ("Router Details", {"fields": ("type", "name", "asn", "ip", "version", "only_monitor",)}),
        ("Location Information", {"fields": ("datacenter",)}),
        # ("Status Information", {"fields": ("status",  "last_pings", "total_pings", "successful_pings", "consecutive_failures")}),
        # ("Resource Usage", {"fields": ("cpu_usage", "mem_usage", "storage_usage")}),
    )

    # Enable ordering by fields
    ordering = ("type",)

    # Pagination in the admin list view
    list_per_page = 20


@admin.register(SSHSettings)
class SSHSettingsAdmin(admin.ModelAdmin):
    list_display = ("settings_name", "port", "username", "password")


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "type", "syslog_strings", "last_triggered")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "subject",
        "message",
        "hostname",
        "router_display",
        "source",
        "created_at",
    )
    list_filter = ("type", "hostname", "router", "source")

    ordering = ("-created_at",)
    list_per_page = 20

    def router_display(self, obj):
        return (
            obj.router
            if obj.router
            else "Router with this HOSTNAME not added in database"
        )

    router_display.short_description = "Router"


@admin.register(Latency)
class LatencyAdmin(admin.ModelAdmin):
    list_display = ("router", "latency", "created_at")
    list_filter = ("router__name", "router__ip", "created_at")
    search_fields = ("router__name", "router__ip")

    ordering = (
        "latency",
        "-created_at",
    )

    # Pagination in the admin list view
    list_per_page = 20


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ("router", "version", "file", "created_at")

    # 1) Use a custom change list template
    change_list_template = "admin/configuration_change_list.html"

    def get_urls(self):
        """
        Add a custom URL for our 'Update Device Configs' action.
        """
        urls = super().get_urls()
        my_urls = [
            path(
                "update-configs-now/",
                self.admin_site.admin_view(self.update_configs_now),
                name="update_configs_now",
            ),
        ]
        return my_urls + urls

    def update_configs_now(self, request):
        """
        Runs 'update_device_configs' mgmt command, captures output, and shows it in a custom template.
        """
        buf = io.StringIO()
        with redirect_stdout(buf):
            call_command("update_device_configs")
        output = buf.getvalue()

        # Render a simple template that shows the command output
        return render(
            request,
            "admin/update_configs_result.html",
            {
                "title": "Update Device Configs Output",
                "output": output,  # We'll display with newlines
            },
        )


@admin.register(DataCenter)
class DataCenterAdmin(admin.ModelAdmin):
    list_display = ("city", "state", "country")
    search_fields = ("city", "state", "country")
    list_filter = ("country", "state")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # also add no of commands in the category
    list_display = ("name", "summary", "order", "command_count")
    search_fields = ("name", "summary")
    ordering = ("order",)

    def command_count(self, obj):
        return obj.command_set.count()

    command_count.short_description = "No. of Commands"


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "command",
        "purpose",
        "category_name",
    )
    search_fields = ("label", "command", "purpose")
    list_filter = ("category__name",)
    ordering = ("label",)

    def category_name(self, obj):
        return obj.category.name if obj.category else "No Category"

    category_name.short_description = "Category"


@admin.register(PopularCommand)
class PopularCommandAdmin(admin.ModelAdmin):
    list_display = ("command", "timestamp")
    search_fields = ("command__label", "command__command")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)
