import requests

registration_status = "Startup not executed yet."

def create_starter_AE():

    # The URL of the oneM2M CSE
    cse_url = 'http://localhost:8080/~/cse-in' #might need to change this depending

    # Set the oneM2M headers
    headers = {
        'Content-Type': 'application/json;ty=2',
        'X-M2M-Origin': 'CMyApplication',
        'X-M2M-RI': '12345',
        'X-M2M-RVI': '4'
    }

    # Define the oneM2M body for the AE
    body = {
        'm2m:ae': {
            'rn': 'Corchestrator',
            'api': 'Nmy-application.example.com',
            'rr': True,
            'srv': ['4']
        }
    }

    # Send the request to the oneM2M CSE
    response = requests.post(cse_url, headers=headers, json=body)

    # Check the response status code
    if response.status_code == 201:
        print(f'AE registration successful: {response.status_code} / {response.headers["X-M2M-RSC"]}')
        print(response.json())
    else:
        print(f'AE registration failed: {response.status_code} / {response.headers["X-M2M-RSC"]} {response.json()}')

    return response.status_code