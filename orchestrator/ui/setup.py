import random, string
import os

# Setup variables
cse_url = 'http://localhost:8080/~/id-in/cse-in'                  # The url of the CSE
notificationURIs = ['http://host.docker.internal:7070']                # The notification target
application_name = 'orchestrator'                         # The name of the application entity (AE resource name, path)
originator = 'Corchestrator'                               # X-M2M-Origin for requests (ACME expects C-prefix)
# Originator for AE create request. Must not be already registered (CAdmin is already an AE on CSE).
originator_ae_create = 'Corchestrator'
application_path = cse_url + '/' + application_name         # The path of the application entity
# Gateway Agent paths (Orchestrator sends command/data via IN-CSE)
# Use CAdmin so CSE allows CREATE on gatewayAgent containers (Corchestrator has no ACP privilege there)
originator_gateway_control = "CAdmin"
gateway_ae_name = "gatewayAgent"
gateway_cmd_path = cse_url + '/' + gateway_ae_name + '/cmd'
gateway_data_path = cse_url + '/' + gateway_ae_name + '/data'
container_name = 'myContainer'                              # The name of the container
container_path = application_path + '/' + container_name    # The path of the container
subscription_name = 'mySubscription'                        # The name of the subscription

# WireGuard startup package defaults
wg_interface = os.environ.get("WG_INTERFACE", "wg0")
wg_server_public_key = os.environ.get("WG_SERVER_PUBLIC_KEY", "<ORCHESTRATOR_PUBLIC_KEY>")
wg_server_endpoint = os.environ.get("WG_SERVER_ENDPOINT", "10.10.0.1:51820")
wg_allowed_ips = os.environ.get("WG_ALLOWED_IPS", "0.0.0.0/0")
wg_persistent_keepalive = os.environ.get("WG_PERSISTENT_KEEPALIVE", "25")
wg_client_address_prefix = os.environ.get("WG_CLIENT_ADDRESS_PREFIX", "10.10.0")
wg_client_address_mask = os.environ.get("WG_CLIENT_ADDRESS_MASK", "24")


def randomID() -> str:
    """ Generate an ID. Prevent certain patterns in the ID.

        Return:
            String with a random ID
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = 10))
