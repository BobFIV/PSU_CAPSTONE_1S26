from setup import cse_url, randomID
import requests

def register_AE(originator:str, application_name: str) -> bool:
    """ Register an Application Entity

        Args:
            originator: The originator of the request

        Returns:
            bool: True if the AE was registered successfully, False otherwise
    """

    # Set the oneM2M headers for creating the <AE> resource
    headers = {
        'Content-Type': 'application/json;ty=2',    # Type of the resource to be created
        'X-M2M-Origin': originator,                 # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }

    # Define the <AE> resource
    body = {
        'm2m:ae': {
            'rn': application_name, 
            'api': 'N.org.'+application_name,
            'rr': True,
            'srv': ['4']
        }
    }


    # Perform the http request to create the <AE> resource
    response = requests.post(cse_url, headers=headers, json=body)


    # Check the response
    if response.status_code == 201:
        print('AE created successfully')
    else:
        print('Error creating AE: ' + str(response.status_code))
        return False

    return True


# Unregister AE
def unregister_AE(originator, application_name:str) -> bool:
    """ Unregister an Application Entity

        Args:
            originator: The originator of the request

        Returns:
            bool: True if the AE was unregistered successfully, False otherwise
    """

    # Set the oneM2M headers for deleting the <AE> resource
    headers = {
        'X-M2M-Origin': originator,           # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }

    # Perform the http request to delete the <AE> resource
    response = requests.delete(cse_url + '/' + application_name, headers=headers)

    # Check the response
    if response.status_code == 200:
        print('AE deleted successfully')
    else:
        print('Error deleting AE: ' + str(response.status_code))
        return False

    return True


def retrieve_AE(originator:str, path:str) -> bool:
    """ Retrieve an Application Entity

        Args:
            originator: The originator of the request
            path: The path of the <AE> resource
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
        print('AE retrieved successfully')
    else:
        print('Error retrieving AE: ' + str(response.status_code))
        return False

    return True

