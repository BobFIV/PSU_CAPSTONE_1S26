
import requests
from setup import randomID




def create_container(originator:str, application_path:str, rn:str)->bool:
    """ Create a <container> resource

        Args:
            originator: The originator of the request
            path: The path of the parent resource
            rn: The resource name of the <container> resource

        Returns:
            bool: True if the <container> resource was created successfully, False otherwise
    """
    # Set the oneM2M headers for retrieving the <AE> resource
    headers = {
        'Content-Type': 'application/json;ty=3',         # Encoding
        'X-M2M-Origin': originator,                 # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }

    # Define the <AE> resource
    body = {
        'm2m:cnt': {
            'rn': rn
        }
    }

    # Perform the http request to create the container resource
    response = requests.post(application_path, headers=headers, json=body)

    # Check the response
    if response.status_code == 201:
        print('Container created successfully')
    else:
        print('Error creating Container: ' + str(response.status_code))
        return False

    return True


def retrieve_container(originator:str, path:str) -> bool:
    """ Retrieve a container

        Args:
            originator: The originator of the request
            path: The path of the <container> resource
    """
    # Set the oneM2M headers for retrieving the <AE> resource
    headers = {
        'Content-Type': 'application/json',         # Encoding
        'X-M2M-Origin': originator,                 # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }

    response = requests.get(path, headers=headers) 

    # Check the response
    if response.status_code == 200:
        print('Container retrieved successfully')
    else:
        print('Error retrieving container: ' + str(response.status_code))
        return False

    return True
    