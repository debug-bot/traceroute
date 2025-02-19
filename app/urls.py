from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name="main"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("network-tools/", views.network_tools_api, name="network_tools_api"),
    path("test-ssh/", views.test_ssh_connection, name="test_ssh_connection"),
    path("test-ssh/", views.test_ssh_connection, name="test_ssh_connection"),
    path("get-devices/", views.get_devices_by_cities, name="get_devices_by_cities"),
    path("history/", views.command_history_view, name="command_history"),
    path("temp/", views.temp, name="temp"),
]
