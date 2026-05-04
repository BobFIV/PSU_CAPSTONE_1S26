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
    host_name = body.get("hostName", "")

    ok, status_code, cse_response = services.send_command_to_gateway(content, host_name)

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
    try:
        body = json.loads(request.body) if request.body else {}
        cse_name = body.get("cseName", "")
        local_port = body.get("localPort", "")
        cse_id = body.get("cseID", "")
        deploy_type = body.get("deployType", "Deploy CSE")
        docker_name = body.get("dockerName", "")
        host_name = body.get("hostName", "")  # <-- add this

        fields = {
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

    pre_check = services.check_host_availability(host_name, docker_name)
    if pre_check:
        return JsonResponse({
            "success": False,
            "message": pre_check,
        })
    ok_data, status_data, cse_data = services.send_data_to_gateway(content, host_name)      # <-- pass host_name
    ok_cmd, status_cmd, cse_cmd = services.send_command_to_gateway("execute", host_name)    # <-- pass host_name

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
            host_name=host_name,
            docker_name=docker_name,  # <-- add this
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

@require_http_methods(["POST"])
@csrf_exempt
def api_provision_host(request):
    try:
        body = json.loads(request.body) if request.body else {}
        name = body.get("name", "")
        success = services.initialize_provision_host(name)
        if success:
            return JsonResponse({"success": True, "name": name})
        else:
            return JsonResponse({"success": False})
    except Exception as e:
        print(e)
        return JsonResponse({"success": False})
