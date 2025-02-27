from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name="main"),
    path("dashboard2/", views.dashboard2, name="dashboard2"),
    path("network-tools/", views.network_tools_api, name="network_tools_api"),
    path("test-ssh/", views.test_ssh_connection, name="test_ssh_connection"),
    path("test-ssh/", views.test_ssh_connection, name="test_ssh_connection"),
    path("get-devices/", views.get_devices_by_cities, name="get_devices_by_cities"),
    path("get-devices-by-datacenters/", views.get_devices_by_datacenters, name="get_devices_by_datacenters"),
    path("history1/", views.command_history_view, name="command_history"),
    path("temp/", views.temp, name="temp"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("devices/", views.devices, name="devices"),
    path("monitoring/", views.monitoring, name="monitoring"),
    path("history/", views.history, name="history"),
    # for get_device_stats?device_id
    path("get_device_stats/<int:device_id>/", views.get_device_stats, name="get_device_stats"),
]
