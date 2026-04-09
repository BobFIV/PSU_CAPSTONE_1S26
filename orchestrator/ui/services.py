import atexit
import copy
import threading
from datetime import datetime, timezone

from .setup import *
from .ae import register_AE, unregister_AE
from .container import create_container
from .subscription import create_subscription
from .contentInstance import create_contentInstance, create_contentInstance_with_response
from .notificationReceiver import run_notification_receiver, stop_notification_receiver

registration_status = "Not connected to IN-CSE"
final_registration_status = "Not Connected to IN-CSE"

# -----------------------------
# In-memory topology state
# -----------------------------
_topology_lock = threading.RLock()
_topology_state = {
    "version": 0,
    "updated_at": None,
    "cses": [],
    "aes": [],
}


def _utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def _touch_topology():
    _topology_state["version"] += 1
    _topology_state["updated_at"] = _utc_now_iso()


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    cleaned = []
    prev_dash = False
    for ch in value:
        if ch.isalnum():
            cleaned.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                cleaned.append("-")
                prev_dash = True
    out = "".join(cleaned).strip("-")
    return out or "item"


def _next_default_name(prefix: str, items: list) -> str:
    return f"{prefix}-{len(items) + 1}"


def get_topology_snapshot():
    with _topology_lock:
        if _topology_state["updated_at"] is None:
            _touch_topology()
        return copy.deepcopy(_topology_state)


def clear_topology():
    with _topology_lock:
        _topology_state["cses"] = []
        _topology_state["aes"] = []
        _touch_topology()


def _latest_cse_node_id_locked():
    if not _topology_state["cses"]:
        return None
    return _topology_state["cses"][-1]["nodeId"]


def _find_cse_by_cse_id_locked(cse_id: str):
    for item in _topology_state["cses"]:
        if item.get("cseID") == cse_id:
            return item
    return None


def make_cse_node_id(name: str = "", cse_id: str = "", port: str = "") -> str:
    base = (cse_id or "").strip() or f"{(name or '').strip()}-{(port or '').strip()}" or f"cse-{_utc_now_iso()}"
    return f"mn-{_slugify(base)}"


def upsert_cse_topology(name: str = "", cse_id: str = "", port: str = "", deploy_type: str = "Deploy CSE", source: str = "api"):
    with _topology_lock:
        final_name = (name or "").strip() or _next_default_name("mn-cse", _topology_state["cses"])
        final_cse_id = (cse_id or "").strip()
        final_port = (port or "").strip()
        node_id = make_cse_node_id(final_name, final_cse_id, final_port)

        record = {
            "nodeId": node_id,
            "name": final_name,
            "cseID": final_cse_id,
            "port": final_port,
            "deployType": deploy_type or "Deploy CSE",
            "source": source,
            "updatedAt": _utc_now_iso(),
        }

        for index, existing in enumerate(_topology_state["cses"]):
            if existing["nodeId"] == node_id:
                _topology_state["cses"][index] = {**existing, **record}
                _touch_topology()
                return copy.deepcopy(_topology_state["cses"][index])

        _topology_state["cses"].append(record)
        _touch_topology()
        return copy.deepcopy(record)


def add_ae_to_topology(name: str = "", parent_node_id: str = "", parent_cse_id: str = "", deploy_type: str = "Deploy AE", source: str = "api"):
    with _topology_lock:
        target_parent = (parent_node_id or "").strip()

        if not target_parent and parent_cse_id:
            cse = _find_cse_by_cse_id_locked(parent_cse_id.strip())
            if cse:
                target_parent = cse["nodeId"]

        if not target_parent:
            target_parent = _latest_cse_node_id_locked()

        # Fall back to IN-CSE node if no MN-CSE exists yet
        if not target_parent:
            target_parent = "in-cse"   # <-- this is the fix

        final_name = (name or "").strip() or _next_default_name("sample-ae", _topology_state["aes"])

        for existing in _topology_state["aes"]:
            if existing["parentNodeId"] == target_parent and existing["name"] == final_name:
                existing["deployType"] = deploy_type or existing.get("deployType") or "Deploy AE"
                existing["source"] = source
                existing["updatedAt"] = _utc_now_iso()
                _touch_topology()
                return copy.deepcopy(existing)

        seed = f"{target_parent}-{final_name}-{len(_topology_state['aes']) + 1}"
        node_id = f"ae-{_slugify(seed)}"
        record = {
            "nodeId": node_id,
            "parentNodeId": target_parent,
            "name": final_name,
            "deployType": deploy_type or "Deploy AE",
            "source": source,
            "updatedAt": _utc_now_iso(),
        }
        _topology_state["aes"].append(record)
        _touch_topology()
        return copy.deepcopy(record)


def handle_gateway_agent_notification(ae_resource: dict):
    """
    Called by notificationReceiver when a gatewayAgent AE creation notification arrives.
    Attaches the AE to the most recently added CSE unless parent info is available later.
    """
    ae_name = (ae_resource or {}).get("rn", "gatewayAgent")
    return add_ae_to_topology(
        name=ae_name,
        deploy_type="Auto-detected gatewayAgent",
        source="notification",
    )


def initalize_Full_startup(application_name, application_path, container_name, container_path, subscription_name, notificationURIs):
    global registration_status
    global final_registration_status
    try:
        run_notification_receiver()
        registration_status = "Notification Server Started"

        if not register_AE(application_name):
            registration_status = "AE registration failed"
            stop_notification_receiver()
            return False

        registration_status = "AE registered"

        if not create_container(application_name, application_path, container_name):
            registration_status = "container creation failed"
            unregister_AE(application_name)
            stop_notification_receiver()
            return False

        registration_status = "Container created"

        if not create_subscription(application_name, container_path, subscription_name, notificationURIs):
            registration_status = "Subscription creation failed"
            unregister_AE(application_name)
            stop_notification_receiver()
            return False

        registration_status = "subscription created"

        if not create_contentInstance(application_name, container_path, 'Hello World!'):
            registration_status = "ContentInstance creation failed"
            unregister_AE(application_name)
            stop_notification_receiver()
            return False

        atexit.register(stop_notification_receiver)
        atexit.register(lambda: unregister_AE(application_name))
        registration_status = "ContentInstance created"
        return True

    except Exception as e:
        registration_status = f"Error: {e}"
        stop_notification_receiver()
        return False


def subscribe_to_cse_base():
    """
    Start notification receiver and subscribe to the IN-CSE base so the Orchestrator
    gets AE-create notifications (for gatewayAgent detection).
    """
    try:
        run_notification_receiver()
        atexit.register(stop_notification_receiver)
        ok = create_subscription(
            originator_gateway_control,
            cse_url,
            "orchestratorSubToCSEBase",
            notificationURIs,
        )
        if ok:
            print("Orchestrator subscribed to IN-CSE base (AE-create notifications on port 7070)")
        else:
            print("Orchestrator: subscription to IN-CSE base failed")
        return ok
    except Exception as e:
        print("Orchestrator subscribe_to_cse_base:", e)
        return False


def initialize_AE_only(application_name):
    """
    Startup logic:
    - register orchestrator AE
    - start notification receiver
    - subscribe to IN-CSE base for gatewayAgent AE-create notifications
    """
    global registration_status
    global final_registration_status
    try:
        if not register_AE(originator_ae_create):
            registration_status = f"AE registration failed for '{application_name}'"
            return False

        atexit.register(lambda: unregister_AE(application_name, originator_ae_create))
        registration_status = f"AE '{application_name}' registered successfully"
        print(registration_status)
        final_registration_status = "Orchestrator AE successfully created"

        subscribe_to_cse_base()
        return True

    except Exception as e:
        registration_status = f"Error registering AE: {e}"
        return False


def send_command_to_gateway(content: str) -> tuple:
    """Create contentInstance in gatewayAgent/cmd."""
    return create_contentInstance_with_response(originator_gateway_control, gateway_cmd_path, content)


def send_data_to_gateway(content: str) -> tuple:
    """Create contentInstance in gatewayAgent/data."""
    return create_contentInstance_with_response(originator_gateway_control, gateway_data_path, content)

def discover_resources_from_cse() -> dict:
    """
    Query the IN-CSE for registered remoteCSEs and AEs.
    Returns a dict with keys 'cses' and 'aes'.
    """
    import requests as _requests

    headers_base = {
        'X-M2M-Origin': originator_gateway_control,
        'X-M2M-RVI': '4',
        'Accept': 'application/json',
    }

    discovered_cses = []
    discovered_aes = []

    # --- Discover MN-CSEs (remoteCSE, ty=16) ---
    try:
        h = {**headers_base, 'X-M2M-RI': randomID()}
        r = _requests.get(cse_url, params={'fu': 1, 'ty': 16}, headers=h, timeout=5)
        if r.status_code == 200:
            data = r.json()
            # Response is a list of resource URIs under 'm2m:uril'
            uris = data.get('m2m:uril', [])
            for uri in uris:
                # Fetch each remoteCSE resource for its details
                h2 = {**headers_base, 'X-M2M-RI': randomID()}
                r2 = _requests.get(f'http://localhost:8080/{uri}', headers=h2, timeout=5)
                if r2.status_code == 200:
                    csr = r2.json().get('m2m:csr', {})
                    cse_name = csr.get('csn', csr.get('rn', ''))
                    cse_id   = csr.get('csi', '')
                    # Try to extract port from pointOfAccess (poa)
                    poa_list = csr.get('poa', [])
                    port = ''
                    if poa_list:
                        # e.g. "http://localhost:8081"
                        try:
                            port = poa_list[0].split(':')[-1]
                        except Exception:
                            pass
                    discovered_cses.append({
                        'name': cse_name,
                        'cseID': cse_id,
                        'port': port,
                    })
    except Exception as e:
        print(f'discover_resources_from_cse (CSE): {e}')

    # --- Discover AEs (ty=2) ---
    try:
        h = {**headers_base, 'X-M2M-RI': randomID()}
        r = _requests.get(cse_url, params={'fu': 1, 'ty': 2}, headers=h, timeout=5)
        if r.status_code == 200:
            data = r.json()
            uris = data.get('m2m:uril', [])
            for uri in uris:
                h2 = {**headers_base, 'X-M2M-RI': randomID()}
                r2 = _requests.get(f'http://localhost:8080/{uri}', headers=h2, timeout=5)
                if r2.status_code == 200:
                    ae = r2.json().get('m2m:ae', {})
                    ae_name = ae.get('rn', '')
                    ae_api  = ae.get('api', '')
                    discovered_aes.append({
                        'name': ae_name,
                        'api': ae_api,
                    })
    except Exception as e:
        print(f'discover_resources_from_cse (AE): {e}')

    return {'cses': discovered_cses, 'aes': discovered_aes}


def sync_topology_from_cse():
    discovered = discover_resources_from_cse()

    for cse in discovered['cses']:
        upsert_cse_topology(
            name=cse['name'],
            cse_id=cse['cseID'],
            port=cse['port'],
            deploy_type='Discovered from IN-CSE',
            source='cse-discovery',
        )

    for ae in discovered['aes']:
        if ae['name'] == 'CAdmin':
            continue
        add_ae_to_topology(
            name=ae['name'],
            parent_node_id='in-cse',   # <-- always attach to IN-CSE
            deploy_type='Discovered from IN-CSE',
            source='cse-discovery',
        )
def query_node_properties(node_type: str, name: str) -> dict:
    """
    Query the IN-CSE directly for a resource's properties.
    node_type: 'in'  -> query the CSE base (m2m:cb)
               'mn'  -> query remoteCSE by name (m2m:csr)
               'ae'  -> query AE by name (m2m:ae)
    name: the resource name (rn) on the CSE
    """
    import requests as _requests

    headers = {
        'X-M2M-Origin': originator_gateway_control,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4',
        'Accept': 'application/json',
    }

    try:
        if node_type == 'in':
            url = cse_url
        elif node_type in ('mn', 'ae'):
            if not name:
                return {"success": False, "message": "Resource name required"}
            url = f"{cse_url}/{name}"
        else:
            return {"success": False, "message": f"Unknown node type: {node_type}"}

        r = _requests.get(url, headers=headers, timeout=5)

        if r.status_code != 200:
            return {
                "success": False,
                "message": f"CSE returned {r.status_code}",
                "raw": r.text[:300] if r.text else "",
            }

        data = r.json()

        # Extract the inner resource object regardless of wrapper key
        resource = None
        for key in ('m2m:cb', 'm2m:ae', 'm2m:csr'):
            if key in data:
                resource = data[key]
                resource_type = key
                break

        if resource is None:
            return {"success": False, "message": "Unrecognised resource format", "raw": data}

        # Build a clean human-readable properties dict
        label_map = {
            'rn':   'Resource Name',
            'ri':   'Resource ID',
            'pi':   'Parent ID',
            'ct':   'Created At',
            'lt':   'Last Modified',
            'csi':  'CSE ID',
            'csn':  'CSE Name',
            'cst':  'CSE Type',
            'srt':  'Supported Resource Types',
            'srv':  'Supported Release Versions',
            'poa':  'Point of Access',
            'api':  'App ID',
            'aei':  'AE ID',
            'rr':   'Request Reachability',
            'nl':   'Node Link',
            'lbl':  'Labels',
        }

        props = {}
        for k, v in resource.items():
            label = label_map.get(k, k)
            props[label] = v

        return {
            "success": True,
            "resourceType": resource_type,
            "properties": props,
        }

    except _requests.RequestException as e:
        return {"success": False, "message": f"Request failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {e}"}
