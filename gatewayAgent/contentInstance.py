import requests
from setup import *

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
    else:
        print('Error creating ContentInstance: ' + str(response.status_code))
        return False

    return True


def retrieve_contentinstance(originator:str, path:str) -> dict:
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
    # data=notify_q.get()
    
    # cin=data['m2m:sgn']['nev']['rep']['m2m:cin']

 
    response = requests.get(path, headers=headers)
    if response.status_code != 200:
        # 404 on /la is expected when no contentInstance exists yet.
        if response.status_code != 404:
            print('Error retrieving contentinstance: ' + str(response.status_code))
        return None

    try:
        cin = response.json().get('m2m:cin')
    except Exception:
        print('Error parsing contentinstance response')
        return None

    if not cin:
        print('No contentinstance in response')
        return None

    print('Contentinstance retrieved successfully')
    return cin


    
def delete_contentinstance(url:str)->bool:
    h = {
            "X-M2M-Origin": originator,
            "X-M2M-RI": randomID(),
            "X-M2M-RVI": "4",
            "Accept": "application/json",
        }
    r=requests.delete(url, headers=h)
    
    if r.status_code == 200:
        print('Contentinstance deleted successfully')
    else:
        print('Error deleting contentinstance: ' + str(r.status_code))
        return False
