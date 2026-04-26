import atexit
import copy
import threading
from datetime import datetime, timezone
import signal
import sys
from pathlib import Path
import shutil

from .setup import *
from .ae import register_AE, unregister_AE
from .container import create_container
from .subscription import create_subscription
from .contentInstance import create_contentInstance, create_contentInstance_with_response
from .notificationReceiver import run_notification_receiver, stop_notification_receiver

from .node_flexnode_for_provision_host import create_node, create_flex_container
from .gateway_package import provision_wireguard_package

registration_status = "Not connected to IN-CSE"
final_registration_status = "Not Connected to IN-CSE"
provisioned_host_names = []
env_file_number = 1


# -----------------------------
# In-memory topology state
# -----------------------------
_topology_lock = threading.RLock()
_topology_state = {
    "version": 0,
    "updated_at": None,
    "hosts": [],
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


def upsert_cse_topology(name: str = "", cse_id: str = "", port: str = "", deploy_type: str = "Deploy CSE", source: str = "api", host_name: str = "", docker_name: str = ""):
    with _topology_lock:
        final_name = (name or "").strip() or _next_default_name("mn-cse", _topology_state["cses"])
        final_cse_id = (cse_id or "").strip()
        final_port = (port or "").strip()
        final_docker_name = (docker_name or "").strip()
        node_id = make_cse_node_id(final_name, final_cse_id, final_port)

        if host_name and host_name.strip():
            host_node_id = f"host-{_slugify(host_name.strip())}"
        else:
            host_node_id = _latest_host_node_id_locked()

        record = {
            "nodeId": node_id,
            "name": final_name,
            "cseID": final_cse_id,
            "port": final_port,
            "dockerName": final_docker_name,
            "deployType": deploy_type or "Deploy CSE",
            "hostNodeId": host_node_id,
            "source": source,
            "updatedAt": _utc_now_iso(),
        }

        # Match on dockerName if provided, otherwise fall back to nodeId
        for index, existing in enumerate(_topology_state["cses"]):
            match = (
                final_docker_name and existing.get("dockerName") == final_docker_name
            ) or (
                not final_docker_name and existing["nodeId"] == node_id
            )
            if match:
                if source == "cse-discovery" and not host_name and existing.get("hostNodeId"):
                    record["hostNodeId"] = existing["hostNodeId"]
                # Preserve nodeId from existing record so diagram node doesn't change
                record["nodeId"] = existing["nodeId"]
                _topology_state["cses"][index] = {**existing, **record}
                _touch_topology()
                return copy.deepcopy(_topology_state["cses"][index])
        
        # Check max 1 MN-CSE per node before creating a new one
        if not any(
            (final_docker_name and existing.get("dockerName") == final_docker_name)
            for existing in _topology_state["cses"]
        ):
            # This is a new CSE, not an update — check if host is already occupied
            if host_node_id and _host_has_cse_locked(host_node_id, exclude_docker_name=final_docker_name):
                return {"error": "Host already has an MN-CSE. Only one MN-CSE per host is allowed."}

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
    global registration_status
    global final_registration_status
    try:
        if not register_AE(originator_ae_create):
            registration_status = f"AE registration failed for '{application_name}'"
            return False

        registration_status = f"AE '{application_name}' registered successfully"
        print(registration_status)
        final_registration_status = "Orchestrator AE successfully created"

        subscribe_to_cse_base()

        # Register cleanup for all exit scenarios
        atexit.register(_cleanup_on_exit)
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)

        return True

    except Exception as e:
        registration_status = f"Error registering AE: {e}"
        return False


def send_command_to_gateway(content: str, host_name: str = "") -> tuple:
    """Create contentInstance in the selected host's gateway_cmd container."""
    if not provisioned_host_names:
        return False, 0, "No host provisioned yet. Use Provision Host first."
    
    # Use selected host if valid, otherwise fall back to latest
    target = host_name.strip() if host_name and host_name.strip() in provisioned_host_names else provisioned_host_names[-1]
    path = cse_url + '/' + target + '/resources/gateway_cmd'
    return create_contentInstance_with_response(originator_gateway_control, path, content)


def send_data_to_gateway(content: str, host_name: str = "") -> tuple:
    """Create contentInstance in the selected host's gateway_data container."""
    if not provisioned_host_names:
        return False, 0, "No host provisioned yet. Use Provision Host first."
    
    target = host_name.strip() if host_name and host_name.strip() in provisioned_host_names else provisioned_host_names[-1]
    path = cse_url + '/' + target + '/resources/gateway_data'
    return create_contentInstance_with_response(originator_gateway_control, path, content)

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
                    cse_name = csr.get('rn', csr.get('csn', ''))
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
        elif node_type == 'host':
            if not name:
                return {"success": False, "message": "Resource name required"}
            url = f"{cse_url}/{name}"
        elif node_type == 'ae':
            if not name:
                return {"success": False, "message": "Resource name required"}
            url = f"{cse_url}/{name}"
        elif node_type == 'mn':
            if not name:
                return {"success": False, "message": "Resource name required"}
            clean_name = name.lstrip('/')
            url = f"{cse_url}/{clean_name}"
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
        for key in ('m2m:cb', 'm2m:ae', 'm2m:csr', 'm2m:nod'):
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
            'et': 'Expiry Time',
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
    
def initialize_provision_host(name: str) -> bool:
    global provisioned_host_names 
    global env_file_number
    try:
        node_rn = name.strip() if name and name.strip() else "gw-node-01"
        created = create_node(originator_gateway_control, cse_url, node_rn)
        if created:
            print("node created Successfully")
            provisioned_host_names.append(node_rn)   # store for other functions to use
            #for making new directory

            # Base directory = project root (adjust parents[] as needed)
            BASE_DIR = Path(__file__).resolve().parent.parent.parent

            name = "NodeName_" +node_rn
            new_dir = BASE_DIR / name
            new_dir.mkdir(exist_ok=True)

            wireguard_dir = new_dir / "wireguard"
            gateway_agent_dir = new_dir / "gateway-agent"
            wireguard_dir.mkdir(exist_ok=True)
            gateway_agent_dir.mkdir(exist_ok=True)

            provision_wireguard_package(node_rn)

            # Derive node number from node name (gw-node-01 -> 1, gw-node-02 -> 2).
            # This makes the env file deterministic per node, independent of
            # provisioning order and the global env_file_number counter.
            import re, os
            m = re.search(r'(\d+)$', node_rn)
            node_num = int(m.group(1)) if m else env_file_number

            # Read the just-generated wg0.conf to extract this Pi's WG IP
            # (needed for CALLBACK_URL and GATEWAY_HOST_ADDR so cross-machine
            # works — the Pi must be reachable at its WG IP, not at a docker
            # bridge hostname).
            wg_conf_path = wireguard_dir / "wg0.conf"
            pi_wg_addr = None
            if wg_conf_path.exists():
                for line in wg_conf_path.read_text().splitlines():
                    s = line.strip()
                    if s.startswith("Address"):
                        # "Address = 10.0.0.2/24" -> "10.0.0.2"
                        try:
                            pi_wg_addr = s.split("=", 1)[1].strip().split("/")[0]
                        except Exception:
                            pass
                        break

            # Cross-machine defaults; override via env vars if needed.
            in_cse_url = os.environ.get(
                "ORCHESTRATOR_IN_CSE_URL",
                "http://10.0.0.1:8080/~/id-in/cse-in")
            gateway_image = os.environ.get(
                "ORCHESTRATOR_GATEWAY_IMAGE",
                "10.0.0.1:5000/gateway-agent:latest")
            acme_image = os.environ.get(
                "ORCHESTRATOR_ACME_IMAGE",
                "10.0.0.1:5000/acme-onem2m-cse:arm64")
            host_cse_dir = os.environ.get(
                "ORCHESTRATOR_HOST_CSE_BASE_DIR",
                "/opt/gateway/cse-data")
            container_cse_dir = os.environ.get(
                "ORCHESTRATOR_CONTAINER_CSE_BASE_DIR",
                "/shared-cse")
            docker_net = os.environ.get(
                "ORCHESTRATOR_DOCKER_NET",
                "acme-net")

            callback_url = (f"http://{pi_wg_addr}:9000"
                            if pi_wg_addr
                            else f"http://gateway-app{node_num}:9000")
            gateway_host_addr = pi_wg_addr if pi_wg_addr else "10.0.0.1"

            file_path = new_dir / f".env.rpi{node_num}"

            with open(file_path, "w") as f:
                f.write(f"NODE_NAME={node_rn}\n")
                f.write(f"IN_CSE_BASE_URL={in_cse_url}\n")
                f.write(f"ORIGINATOR_ID=CgatewayAgent{node_num}\n")
                f.write(f"CALLBACK_URL={callback_url}\n")
                f.write(f"APPLICATION_NAME=gatewayAgent{node_num}\n")
                f.write(f"SUBSCRIPTION_NAME=gatewaySubscription{node_num}\n")
                f.write(f"IMAGE={gateway_image}\n")
                f.write(f"ACME_IMAGE={acme_image}\n")
                f.write(f"GATEWAY_HOST_ADDR={gateway_host_addr}\n")
                f.write(f"LOG_LEVEL=DEBUG\n")
                f.write(f"HOST_CSE_BASE_DIR={host_cse_dir}\n")
                f.write(f"CONTAINER_CSE_BASE_DIR={container_cse_dir}\n")
                f.write(f"DOCKER_HOST=unix:///var/run/docker.sock\n")
                f.write(f"DOCKER_NET={docker_net}\n")
            env_file_number += 1
            
            upsert_host_topology(node_rn) 
            node_path = cse_url + '/' + node_rn
            flex_node_created = create_flex_container(originator_gateway_control, node_path, "resources")
            if flex_node_created:
                print("Node / Flexnode created")
                gateway_container_path = node_path + "/" + "resources"
                cmd_container_created = create_container(originator_gateway_control,gateway_container_path,"gateway_cmd")
                data_container_created = create_container(originator_gateway_control,gateway_container_path,"gateway_data")
                if cmd_container_created and data_container_created:
                    print("node struture created successfully")
                    return True
                elif not cmd_container_created:
                    print("failed to create cmd containter")
                    return False
                else:
                    print("failed to create data container")
                    return False
            else:
                print("flex container not created")
                return False
        else:
            print("error in creating Node / flexnode")
            return False
    except Exception as e:
        print("major error in creating node / flexnode", e)
        return False

def upsert_host_topology(name: str) -> dict:
    with _topology_lock:
        node_id = f"host-{_slugify(name)}"
        for index, existing in enumerate(_topology_state["hosts"]):
            if existing["nodeId"] == node_id:
                _touch_topology()
                return copy.deepcopy(existing)
        record = {
            "nodeId": node_id,
            "name": name,
            "updatedAt": _utc_now_iso(),
        }
        _topology_state["hosts"].append(record)
        _touch_topology()
        return copy.deepcopy(record)

def _latest_host_node_id_locked():
    if not _topology_state["hosts"]:
        return None
    return _topology_state["hosts"][-1]["nodeId"]

def delete_subscription(originator: str, path: str) -> bool:
    import requests as _requests
    headers = {
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4',
    }
    try:
        r = _requests.delete(path, headers=headers, timeout=5)
        if r.status_code == 200:
            print('Subscription deleted successfully')
            return True
        print(f'Error deleting subscription: {r.status_code}')
        return False
    except Exception as e:
        print(f'Error deleting subscription: {e}')
        return False


def delete_node(originator: str, path: str) -> bool:
    import requests as _requests
    headers = {
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4',
    }
    try:
        r = _requests.delete(path, headers=headers, timeout=5)
        if r.status_code == 200:
            print('Node deleted successfully')
            return True
        print(f'Error deleting node: {r.status_code}')
        return False
    except Exception as e:
        print(f'Error deleting node: {e}')
        return False

def _cleanup_on_exit():
    """Remove all oneM2M resources created by the orchestrator."""
    print("Orchestrator shutting down — cleaning up oneM2M resources...")
    
    # Delete subscription
    delete_subscription(
        originator_gateway_control,
        cse_url + '/orchestratorSubToCSEBase'
    )

    BASE_DIR = Path(__file__).resolve().parents[2]
    print("BASE_DIR:", BASE_DIR)
    
    for item in BASE_DIR.iterdir():
        if (
            item.is_dir()
            and item.name.startswith("NodeName_")
            and any(item.glob(".env.rpi*"))
        ):
            try:
                shutil.rmtree(item)
                print(f"Deleted directory: {item}")
            except Exception as e:
                print(f"Failed to delete {item}: {e}")
    

    # Delete provisioned node if one exists
    for host_name in provisioned_host_names:
        delete_node(
            originator_gateway_control,
            cse_url + '/' + host_name
        )

    # Unregister orchestrator AE
    unregister_AE(application_name, originator_ae_create)

    stop_notification_receiver()
    print("Cleanup complete.")


def _signal_handler(sig, frame):
    _cleanup_on_exit()
    sys.exit(0)

def _host_has_cse_locked(host_node_id: str, exclude_docker_name: str = "") -> bool:
    """Returns True if the host already has an MN-CSE assigned to it."""
    for cse in _topology_state["cses"]:
        if cse.get("hostNodeId") == host_node_id:
            # Allow if it's the same docker name (update case)
            if exclude_docker_name and cse.get("dockerName") == exclude_docker_name:
                continue
            return True
    return False

def check_host_availability(host_name: str, docker_name: str) -> str:
    """Returns an error message string if the host is occupied, empty string if ok."""
    with _topology_lock:
        if host_name and host_name.strip():
            host_node_id = f"host-{_slugify(host_name.strip())}"
        else:
            host_node_id = _latest_host_node_id_locked()
        
        if host_node_id and _host_has_cse_locked(host_node_id, exclude_docker_name=(docker_name or "").strip()):
            return "An mn-cse is already deployed on this node so update that mn-cse using the same dockername"
        return ""