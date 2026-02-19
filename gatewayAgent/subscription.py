import requests
from setup import randomID

def create_subscription(originator:str, path:str, rn:str, notificationURIs:list[str]) -> bool:
    """ Create a <subscription> resource

        Args:
            originator: The originator of the request
            path: The path of the parent resource
            rn: The resource name of the <subscription> resource

        Returns:
            bool: True if the <subscription> resource was created successfully, False otherwise
    """
    # Set the oneM2M headers for creating the <subscription> resource
    headers = {
        'Content-Type': 'application/json;ty=23',   # Type of the resource to be created
        'X-M2M-Origin': originator,                 # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }

    # Define the <subscription> resource
    body = {
        'm2m:sub': {
            'rn': rn,
            'enc': {
                'net':[1,2,3,4]
                # 'om': [ {                           # Enable operation monitoring
                #     'ops' : 2,                      # Monitor RETRIEVE operations
                #     'org': originator               # Originator of the operation
                # } ],
            },
            'nct': 1,
            'nu': notificationURIs
        }
    }

    # Perform the http request to create the <subscription> resource
    response = requests.post(path, headers=headers, json=body)

    # Check the response
    if response.status_code == 201:
        print('Subscription created successfully')
    else:
        print('Error creating subscription: ' + str(response.status_code))
        return False

    return True