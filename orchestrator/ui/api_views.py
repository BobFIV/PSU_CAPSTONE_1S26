import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from . import services
from .setup import cse_url


@require_http_methods(["GET"])
def api_status(request):
    return JsonResponse({
        "registration_status": services.final_registration_status,
        "cse_url": cse_url,
    })


@require_http_methods(["GET"])
def api_topology(request):
    return JsonResponse({
        "success": True,
        "topology": services.get_topology_snapshot(),
    })


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

        fields = {
            "cseName": cse_name,
            "localPort": local_port,
            "cseID": cse_id,
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