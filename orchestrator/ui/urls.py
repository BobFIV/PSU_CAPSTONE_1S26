from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/status/", api_views.api_status, name="api_status"),
    path("api/gateway/command/", api_views.api_gateway_command, name="api_gateway_command"),
    path("api/gateway/data/", api_views.api_gateway_data, name="api_gateway_data"),
]
