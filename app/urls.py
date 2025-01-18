from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name="main"),
    path("network-tools/", views.network_tools_api, name="network_tools_api"),
]
