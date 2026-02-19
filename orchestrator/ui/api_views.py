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
    """POST /api/gateway/data/ – body: {"data": "acme-mn1"}. Creates contentInstance in gatewayAgent/data."""
    try:
        body = json.loads(request.body) if request.body else {}
        content = body.get("data", "acme-mn1")
    except json.JSONDecodeError:
        content = "acme-mn1"
    ok, status_code, cse_response = services.send_data_to_gateway(content)
    out = {"success": ok, "message": "Data sent" if ok else "Failed to create contentInstance"}
    if not ok:
        out["status_code"] = status_code
        out["cse_response"] = cse_response[:500] if cse_response else ""
    return JsonResponse(out)
