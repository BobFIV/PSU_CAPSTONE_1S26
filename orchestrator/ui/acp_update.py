import requests
from .setup import randomID

def create_acp(originator: str, path: str, rn: str, allowed_originator: str) -> str | None:
    """ Create an <ACP> resource

        Args:
            originator: The originator of the request (likely CAdmin)
            path: The path of the parent resource (e.g., CSEBase)
            rn: The resource name of the <ACP>
            allowed_originator: The originator allowed by this ACP

        Returns:
            str | None: ACP resource ID (ri) if successful, None otherwise
    """

    headers = {
        'Content-Type': 'application/json;ty=1',
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4'
    }

    body = {
        'm2m:acp': {
            'rn': rn,
            'pv': {
                'acr': [{
                    'acor': ["all"],
                    'acop': 63
                }]
            },
            'pvs': {
                'acr': [{
                    'acor': [allowed_originator],
                    'acop': 63
                }]
            }
        }
    }

    response = requests.post(path, headers=headers, json=body)

    if response.status_code == 201:
        print('ACP created successfully')
        try:
            print(response.json())
            return response.json()['m2m:acp']['ri']
        except KeyError:
            print('ACP created but no RI found in response')
            return None
    else:
        print('Error creating ACP: ' + str(response.status_code))
        print(response.text)
        return None

def attach_acp(originator: str, path: str, acp_id: str) -> bool:
    """ Attach an ACP to a resource (e.g., CSEBase or container)

        Args:
            originator: The originator of the request (likely CAdmin)
            path: The path of the resource to attach the ACP to
            acp_id: The resource ID (ri) of the ACP

        Returns:
            bool: True if successful, False otherwise
    """

    headers = {
        'Content-Type': 'application/json',
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4'
    }

    body = {
        'm2m:cb': {
            'acpi': [acp_id]
        }
    }

    response = requests.put(path, headers=headers, json=body)

    if response.status_code in [200, 204]:
        print('ACP attached successfully')
    else:
        print('Error attaching ACP: ' + str(response.status_code))
        print(response.text)
        return False

    return True

def acp_shutdown(originator: str, path: str, acp_id: str) -> bool:
    """ Remove ACP attachment from CSEBase and delete ACP resource

        Args:
            originator: The originator performing cleanup (likely CAdmin)
            path: The CSEBase path
            acp_id: The ACP resource ID (ri)

        Returns:
            bool: True if cleanup succeeded, False otherwise
    """

    headers = {
        'Content-Type': 'application/json',
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4'
    }

    # ---------------------------------------------------
    # STEP 1: Get current CSEBase to read acpi list
    # ---------------------------------------------------
    get_resp = requests.get(path, headers=headers)

    if get_resp.status_code != 200:
        print("Failed to fetch CSEBase")
        return False

    try:
        current_acpi = get_resp.json()['m2m:cb'].get('acpi', [])
    except Exception:
        print("No acpi field found")
        current_acpi = []

    # ---------------------------------------------------
    # STEP 2: Remove our ACP
    # ---------------------------------------------------
    updated_acpi = [a for a in current_acpi if a != acp_id]

    # ---------------------------------------------------
    # STEP 3: Update CSEBase
    # ---------------------------------------------------
    update_body = {
        'm2m:cb': {
            'acpi': updated_acpi
        }
    }

    put_resp = requests.put(path, headers=headers, json=update_body)

    if put_resp.status_code not in [200, 204]:
        print("Failed to detach ACP from CSEBase")
        print(put_resp.text)
        return False

    print("ACP detached successfully")

    # ---------------------------------------------------
    # STEP 4: Delete ACP resource itself
    # ---------------------------------------------------
    delete_url = f"{path}/ACPOrchestrator"  # or store ACP RI mapping properly

    del_resp = requests.delete(delete_url, headers=headers)

    if del_resp.status_code not in [200, 204]:
        print("Warning: ACP resource not deleted (may not exist or name mismatch)")
    else:
        print("ACP resource deleted successfully")

    return True