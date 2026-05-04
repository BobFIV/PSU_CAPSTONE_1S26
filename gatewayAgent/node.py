from setup import *
import requests


def retrieve_node(originator:str, path:str):
    headers = {
        'Content-Type': 'application/json',         # Encoding
        'X-M2M-Origin': originator,                 # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }

    response = requests.get(path, headers=headers)
    nod=response.json()['m2m:nod'] 
    # print(nod)

    # Check the response
    if response.status_code == 200:
        print('Node retrieved successfully')
    else:
        print('Error retrieving Node: ' + str(response.status_code))
        return

    return nod
