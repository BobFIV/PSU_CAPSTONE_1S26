import random, string

# Setup variables
cse_url = 'http://localhost:8080/~/id-in/cse-in'                  # The url of the CSE
notificationURIs = ['http://localhost:7070']                # The notification target
application_name = 'Corchestrator'                         # The name of the application entity
application_path = cse_url + '/' + application_name         # The path of the application entity
container_name = 'myContainer'                              # The name of the container
container_path = application_path + '/' + container_name    # The path of the container
subscription_name = 'mySubscription'                        # The name of the subscription


def randomID() -> str:
    """ Generate an ID. Prevent certain patterns in the ID.

        Return:
            String with a random ID
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = 10))