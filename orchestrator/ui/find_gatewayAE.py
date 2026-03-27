import requests
from .setup import randomID

def retrieve_gatewayAE(originator:str, path:str) -> bool:
    """ Retrieve gatewayAEs

        Args:
            originator: The originator of the request
            path: The path of the cse base
    """
    # Set the oneM2M headers for retrieving the <AE> resource
    headers = {
        'Content-Type': 'application/json',         # Encoding
        'X-M2M-Origin': originator,                 # unique application entity identifier
        'X-M2M-RI': randomID(),                     # unique request identifier
        'X-M2M-RVI': '4' 
    }
    params = {
        'fu': 2,
        'rcn': 4,
        'ty': 2,
        'lbl': 'gatewayAgent'
    }

    response = requests.get(path, headers=headers,params=params) 

    # Check the response
    if response.status_code == 200:
        data = response.json()

        uris = data.get("m2m:uril", [])

        print(f"[oneM2M] Found {len(uris)} gatewayAgent AE(s):")
        for uri in uris:
            print(f" - {uri}")

        return True

    else:
        print("[oneM2M] Discovery failed")
        print("Status:", response.status_code)
        print(response.text)
        return False