import requests
from .setup import randomID

def create_contentInstance(originator:str, path:str, content:str) -> bool:
    """ Create a <container> resource

        Args:
            originator: The originator of the request
            path: The path of the parent resource
            content: The content of the <contentInstance> resource

        Returns:
            bool: True if the <contentInstance> resource was created successfully, False otherwise
    """
    # Set the oneM2M headers for creating the <container> resource
    headers = {
        'Content-Type': 'application/json;ty=4',    # Type of the resource to be created
        'X-M2M-Origin': originator,                 # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }

    # Define the <container> resource
    body = {
        'm2m:cin': {
            'con': content
        }
    }

    # Perform the http request to create the <container> resource
    response = requests.post(path, headers=headers, json=body)

    # Check the response
    if response.status_code == 201:
        print('ContentInstance created successfully')
        return True
    print('Error creating ContentInstance: ' + str(response.status_code), response.text[:200] if response.text else "")
    return False


def create_contentInstance_with_response(originator: str, path: str, content: str) -> tuple:
    """Create contentInstance and return (success, status_code, response_text) for API error reporting."""
    headers = {
        'Content-Type': 'application/json;ty=4',
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4'
    }
    body = {'m2m:cin': {'con': content}}
    response = requests.post(path, headers=headers, json=body)
    if response.status_code == 201:
        return True, response.status_code, (response.text or "")
    return False, response.status_code, (response.text or response.reason or "")