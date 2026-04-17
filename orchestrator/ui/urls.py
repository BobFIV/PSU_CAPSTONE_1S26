from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/status/", api_views.api_status, name="api_status"),
    path("api/topology/", api_views.api_topology, name="api_topology"),
    path("api/node/info/", api_views.api_node_info, name="api_node_info"),
    path("api/gateway/command/", api_views.api_gateway_command, name="api_gateway_command"),
    path("api/gateway/data/", api_views.api_gateway_data, name="api_gateway_data"),
    path("api/provision/host/", api_views.api_provision_host, name="api_provision_host"),
    path("api/wireguard/peers/", api_views.api_wireguard_peers, name="api_wireguard_peers"),
    path("api/wireguard/server-config/", api_views.api_wireguard_server_config, name="api_wireguard_server_config"),
    path("api/wireguard/server-settings/", api_views.api_wireguard_server_settings, name="api_wireguard_server_settings"),
    path("api/wireguard/server-full-config/", api_views.api_wireguard_server_full_config, name="api_wireguard_server_full_config"),
]
