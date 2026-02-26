import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from . import services
from .setup import cse_url


@require_http_methods(["GET"])
def api_status(request):
    """GET /api/status/ – registration status and CSE URL."""
    return JsonResponse({
        "registration_status": services.final_registration_status,
        "cse_url": cse_url,
    })


@require_http_methods(["POST"])
@csrf_exempt
def api_gateway_command(request):
    """POST /api/gateway/command/ – body: {"command": "execute"}. Creates contentInstance in gatewayAgent/cmd."""
    try:
        body = json.loads(request.body) if request.body else {}
        content = body.get("command", "execute")
    except json.JSONDecodeError:
        content = "execute"
    ok, status_code, cse_response = services.send_command_to_gateway(content)
    out = {"success": ok, "message": "Command sent" if ok else "Failed to create contentInstance"}
    if not ok:
        out["status_code"] = status_code
        out["cse_response"] = cse_response[:500] if cse_response else ""
    return JsonResponse(out)


@require_http_methods(["POST"])
@csrf_exempt
def api_gateway_data(request):
    """POST /api/gateway/data/ – body: {"data": "acme-mn1"}. Creates contentInstance in gatewayAgent/data with the MN-CSE name, then creates contentInstance in gatewayAgent/cmd with 'execute'."""
    try:
        body = json.loads(request.body) if request.body else {}
        cse_name = body.get("cseName", "")
        http_port = body.get("httpPort", "")
        cse_ID = body.get("cseID", "")
        fields = {
            "cseName": cse_name,
            "httpPort": http_port,
            "cseID": cse_ID
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
        content = "\n".join(lines) + ("\n" if lines else "")
    except json.JSONDecodeError:
        return JsonResponse({
            "success":False,
            "message": "Invalid JSON body"
        })

    ok_data, status_data, cse_data = services.send_data_to_gateway(content)
    ok_cmd, status_cmd, cse_cmd = services.send_command_to_gateway("execute")

    success = ok_data and ok_cmd
    if success:
        message = "Data and execute command sent"
    elif ok_data and not ok_cmd:
        message = "Data sent; failed to create execute in cmd"
    elif not ok_data and ok_cmd:
        message = "Execute sent; failed to create data contentInstance"
    else:
        message = "Failed to create contentInstances (data and cmd)"

    out = {"success": success, "message": message}
    if not ok_data:
        out["data_status_code"] = status_data
        out["data_cse_response"] = (cse_data or "")[:500]
    if not ok_cmd:
        out["cmd_status_code"] = status_cmd
        out["cmd_cse_response"] = (cse_cmd or "")[:500]
    return JsonResponse(out)
