import requests
from .setup import randomID

def create_container(originator:str, path:str, rn:str) -> bool:
    """ Create a <container> resource

        Args:
            originator: The originator of the request
            path: The path of the parent resource
            rn: The resource name of the <container> resource

        Returns:
            bool: True if the <container> resource was created successfully, False otherwise
    """
    # Set the oneM2M headers for creating the <container> resource
    headers = {
        'Content-Type': 'application/json;ty=3',    # Type of the resource to be created
        'X-M2M-Origin': originator,                 # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }

    # Define the <container> resource
    body = {
        'm2m:cnt': {
            'rn': rn
        }
    }

    # Perform the http request to create the <container> resource
    response = requests.post(path, headers=headers, json=body)

    # Check the response
    if response.status_code == 201:
        print('Container created successfully')
    else:
        print('Error creating container: ' + str(response.status_code))
        return False

    return True