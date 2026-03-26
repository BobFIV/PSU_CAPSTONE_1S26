import requests
from .setup import randomID


def create_contentInstance(originator: str, path: str, content: str) -> bool:
    headers = {
        'Content-Type': 'application/json;ty=4',
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4'
    }
    body = {'m2m:cin': {'con': content}}

    try:
        response = requests.post(path, headers=headers, json=body, timeout=10)
    except requests.RequestException as e:
        print(f'Error creating ContentInstance: request failed: {e}')
        return False

    if response.status_code == 201:
        print('ContentInstance created successfully')
        return True

    print('Error creating ContentInstance: ' + str(response.status_code), response.text[:200] if response.text else "")
    return False


def create_contentInstance_with_response(originator: str, path: str, content: str) -> tuple:
    """
    Returns: (success: bool, status_code: int, response_text: str)
    Never raises requests exceptions.
    """
    headers = {
        'Content-Type': 'application/json;ty=4',
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4'
    }
    body = {'m2m:cin': {'con': content}}

    try:
        response = requests.post(path, headers=headers, json=body, timeout=10)
    except requests.RequestException as e:
        return False, 0, f"request failed: {e}"

    if response.status_code == 201:
        return True, response.status_code, (response.text or "")

    return False, response.status_code, (response.text or response.reason or "")