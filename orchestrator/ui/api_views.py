import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from . import services
from .setup import cse_url
from .wireguard_state import (
    get_full_server_config,
    get_server_config,
    get_server_settings,
    list_peers,
    save_peer,
    save_server_settings,
    write_full_server_config,
    write_server_config,
)


@require_http_methods(["GET"])
def api_status(request):
    return JsonResponse({
        "registration_status": services.final_registration_status,
        "cse_url": cse_url,
    })


@require_http_methods(["GET"])
def api_topology(request):
    services.sync_topology_from_cse()
    return JsonResponse({
        "success": True,
        "topology": services.get_topology_snapshot(),
    })


@require_http_methods(["GET"])
def api_node_info(request):
    """
    GET /api/node/info/?type=<node_type>&name=<resource_name>
    Queries the IN-CSE directly for the resource properties.
    node_type: 'in', 'mn', 'ae'
    name: resource name (e.g. 'gatewayAgent', 'cse-mn1')
    """
    node_type = request.GET.get("type", "")
    name = request.GET.get("name", "")

    if not node_type:
        return JsonResponse({"success": False, "message": "Missing type parameter"})

    result = services.query_node_properties(node_type, name)
    return JsonResponse(result)


@require_http_methods(["POST"])
@csrf_exempt
def api_gateway_command(request):
    """
    POST /api/gateway/command/
    body:
    {
      "command": "execute",
      "aeName": "sample-ae",
      "parentNodeId": "mn-id-mn1",
      "cseID": "/id-mn1",
      "deployType": "Deploy Sample AE"
    }
    """
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    content = body.get("command", "execute")
    ae_name = body.get("aeName", "")
    parent_node_id = body.get("parentNodeId", "")
    parent_cse_id = body.get("cseID", "")
    deploy_type = body.get("deployType", "Deploy AE")

    ok, status_code, cse_response = services.send_command_to_gateway(content)

    out = {
        "success": ok,
        "message": "Command sent" if ok else "Failed to create contentInstance",
    }

    if ok:
        record = services.add_ae_to_topology(
            name=ae_name,
            parent_node_id=parent_node_id,
            parent_cse_id=parent_cse_id,
            deploy_type=deploy_type,
            source="api",
        )
        out["ae"] = record
        out["topology"] = services.get_topology_snapshot()
        if record is None:
            out["message"] = "Command sent, but no CSE exists yet to attach the AE"
    else:
        out["status_code"] = status_code
        out["cse_response"] = cse_response[:500] if cse_response else ""

    return JsonResponse(out)


@require_http_methods(["POST"])
@csrf_exempt
def api_gateway_data(request):
    """
    POST /api/gateway/data/
    body:
    {
      "cseName": "acme-mn1",
      "localPort": "8081",
      "cseID": "/id-mn1",
      "deployType": "Deploy CSE ACME"
    }
    """
    try:
        body = json.loads(request.body) if request.body else {}
        cse_name = body.get("cseName", "")
        local_port = body.get("localPort", "")
        cse_id = body.get("cseID", "")
        deploy_type = body.get("deployType", "Deploy CSE")
        docker_name = body.get("dockerName", "")
        vpn_type = body.get("vpnType", "")
        wg_interface = body.get("wgInterface", "")
        wg_address = body.get("wgAddress", "")
        wg_server_public_key = body.get("wgServerPublicKey", "")
        wg_endpoint = body.get("wgEndpoint", "")
        wg_allowed_ips = body.get("wgAllowedIPs", "")
        wg_persistent_keepalive = body.get("wgPersistentKeepalive", "")
        wg_listen_port = body.get("wgListenPort", "")
        fields = {
            "vpnType": vpn_type,
            "wgInterface": wg_interface,
            "wgAddress": wg_address,
            "wgServerPublicKey": wg_server_public_key,
            "wgEndpoint": wg_endpoint,
            "wgAllowedIPs": wg_allowed_ips,
            "wgPersistentKeepalive": str(wg_persistent_keepalive).strip(),
            "wgListenPort": str(wg_listen_port).strip(),
            "cseName": cse_name,
            "localPort": local_port,
            "cseID": cse_id,
            "dockerName": docker_name,
        }
        lines = [
            f"{key}={value.strip()}"
            for key, value in fields.items()
            if value and value.strip()
        ]
        if not lines:
            return JsonResponse({
                "success": False,
                "message": "No valid fields provided."
            })
        content = "\n".join(lines) + "\n"
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON body"
        })

    ok_data, status_data, cse_data = services.send_data_to_gateway(content)
    ok_cmd, status_cmd, cse_cmd = services.send_command_to_gateway("execute")

    success = ok_data and ok_cmd
    cse_record = None

    if success:
        message = "Data and execute command sent"
        cse_record = services.upsert_cse_topology(
            name=cse_name,
            cse_id=cse_id,
            port=local_port,
            deploy_type=deploy_type,
            source="api",
        )
    elif ok_data and not ok_cmd:
        message = "Data sent; failed to create execute in cmd"
    elif not ok_data and ok_cmd:
        message = "Execute sent; failed to create data contentInstance"
    else:
        message = "Failed to create contentInstances (data and cmd)"

    out = {
        "success": success,
        "message": message,
        "cse": cse_record,
        "topology": services.get_topology_snapshot(),
    }

    if not ok_data:
        out["data_status_code"] = status_data
        out["data_cse_response"] = (cse_data or "")[:500]
    if not ok_cmd:
        out["cmd_status_code"] = status_cmd
        out["cmd_cse_response"] = (cse_cmd or "")[:500]
    return JsonResponse(out)


@require_http_methods(["GET", "POST"])
@csrf_exempt
def api_wireguard_peers(request):
    """GET/POST /api/wireguard/peers/ - store or list gateway public keys."""
    if request.method == "GET":
        return JsonResponse({"success": True, "peers": list_peers()})

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

    peer_name = (body.get("peerName") or "").strip()
    public_key = (body.get("publicKey") or "").strip()
    metadata = body.get("metadata") or {}

    if not peer_name or not public_key:
        return JsonResponse(
            {"success": False, "message": "peerName and publicKey are required"},
            status=400,
        )

    peer_record = save_peer(peer_name, public_key, metadata)
    return JsonResponse({"success": True, "peer": peer_record})


@require_http_methods(["GET", "POST"])
@csrf_exempt
def api_wireguard_server_config(request):
    """GET current generated server-side peer config or POST to regenerate it."""
    if request.method == "POST":
        config_text = write_server_config()
    else:
        config_text = get_server_config()["config_text"]

    config_info = get_server_config()
    return JsonResponse(
        {
            "success": True,
            "config": config_text,
            "path": config_info["path"],
        }
    )


@require_http_methods(["GET", "POST"])
@csrf_exempt
def api_wireguard_server_settings(request):
    """GET/POST server-side WireGuard interface settings used to build the full server config."""
    if request.method == "GET":
        return JsonResponse({"success": True, "settings": get_server_settings()})

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

    settings = save_server_settings(body)
    return JsonResponse({"success": True, "settings": settings})


@require_http_methods(["GET", "POST"])
@csrf_exempt
def api_wireguard_server_full_config(request):
    """GET/POST the full server-side WireGuard config including [Interface] and generated [Peer] blocks."""
    if request.method == "POST":
        config_text = write_full_server_config()
    else:
        config_text = get_full_server_config()["config_text"]

    config_info = get_full_server_config()
    return JsonResponse(
        {
            "success": True,
            "config": config_text,
            "path": config_info["path"],
            "settings": get_server_settings(),
        }
    )
