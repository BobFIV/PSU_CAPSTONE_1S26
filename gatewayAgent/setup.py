import random, string

# Setup variables
cse_url = 'http://localhost:8081/~/id-mn1/cse-mn1'            # The url of the CSE - use host port of 8081 for mn1, 8080 for in
notificationURIs = ['http://localhost:9000']                # The notification target
application_name = 'gatewayAE'                         # The name of the application entity
application_path = cse_url + '/' + application_name         # The path of the application entity
subscription_name = 'gatewaySubscription'                        # The name of the subscription
originator = 'Cgateway'
container_name='cmd'
container_path=application_path+'/'+container_name

# originator = Cgateway
# acme port: 8080
# port for acme: 8080, 8081, 8082
# port for notification: 9000

def randomID() -> str:
    """ Generate an ID. Prevent certain patterns in the ID.

        Return:
            String with a random ID
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = 10))