from .setup import cse_url, randomID
import requests

def register_AE(originator:str) -> bool:
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
            'rn': 'orchestrator',
            'api': 'Nmy-application.example.com',
            'rr': True,
            'srv': ['4']
        }
    }

    # Perform the http request to create the <AE> resource
    response = requests.post(cse_url, headers=headers, json=body)

    # Check the response
    if response.status_code == 201:
        print('AE created successfully')
        return True
    if response.status_code == 403:
        try:
            text = (response.text or "")
            if "already registered" in text and originator in text:
                print("AE already exists (originator already registered on CSE)")
                return True
        except Exception:
            pass
    print('Error creating AE: ' + str(response.status_code))
    try:
        print('CSE response: ' + (response.text or response.reason))
    except Exception:
        pass
    return False


# Unregister AE
def unregister_AE(application_name: str, request_originator: str = None) -> bool:
    """ Unregister an Application Entity

        Args:
            application_name: AE resource name (path segment)
            request_originator: X-M2M-Origin for the request (default: application_name)

        Returns:
            bool: True if the AE was unregistered successfully, False otherwise
    """
    if request_originator is None:
        request_originator = application_name

    # Set the oneM2M headers for deleting the <AE> resource
    headers = {
        'X-M2M-Origin': request_originator,
        'X-M2M-RI': randomID(),
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