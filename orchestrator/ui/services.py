import requests
import atexit

from .setup import *
from .ae import register_AE, unregister_AE
from .container import create_container
from .subscription import create_subscription
from .contentInstance import create_contentInstance, create_contentInstance_with_response
from .notificationReceiver import run_notification_receiver, stop_notification_receiver

registration_status = "Not connected to IN-CSE" #can help in potentially debuging information in terminal
final_registration_status = "Not Connected to IN-CSE" #use this string to print in the Django Application

#this function is the same as from the OneM2M reciepes where this has the full code content, however, we are going to be using parts of this in the beginning
def initalize_Full_startup(application_name, application_path, container_name, container_path, subscription_name, notificationURIs):
    global registration_status
    global final_registration_status
    try:
        #start notification server
        run_notification_receiver()
        registration_status = "Notification Server Started"

        if not register_AE(application_name):
            registration_status = "AE registration failed"
            stop_notification_receiver()
            return False

        registration_status = "AE registered"

        if not create_container(application_name, application_path, container_name):
            registration_status = "container creation failed"
            unregister_AE(application_name)
            stop_notification_receiver()
            return False
        
        registration_status = "Container created"

        if not create_subscription(application_name, container_path, subscription_name,notificationURIs):
            registration_status = "Subscription creation failed"
            unregister_AE(application_name)
            stop_notification_receiver()
            return False
        
        registration_status = "subscription created"

        if not create_contentInstance(application_name,container_path, 'Hello World!'):
            registration_status = "ContentInstance creation failed"
            unregister_AE(application_name)
            stop_notification_receiver()
            return False
        atexit.register(stop_notification_receiver)
        atexit.register(lambda: unregister_AE(application_name))
        registration_status = "ContentInstance created"

        # Optionally: keep notification server running
        # stop_notification_receiver()  # only stop on shutdown
        return True
    
    except Exception as e:
        registration_status = f"Error: {e}"
        stop_notification_receiver()
        return False
    
def subscribe_to_gateway_data():
    """Start notification receiver and subscribe to gatewayAgent/data so Orchestrator gets NOTIFY when data changes."""
    try:
        run_notification_receiver()
        atexit.register(stop_notification_receiver)
        ok = create_subscription(
            originator_gateway_control,
            gateway_data_path,
            "orchestratorSubToGatewayData",
            notificationURIs,
        )
        if ok:
            print("Orchestrator subscribed to gatewayAgent/data (notifications on port 7070)")
        else:
            print("Orchestrator: subscription to gatewayAgent/data failed (Gateway may not be running yet)")
        return ok
    except Exception as e:
        print("Orchestrator subscribe_to_gateway_data:", e)
        return False


#startup function to just register an AE to the IN-CSE 
def initialize_AE_only(application_name):
    """Startup logic: register the AE and subscribe to Gateway's data container."""
    global registration_status
    global final_registration_status
    try:
        # Register AE only (use CAdmin for first AE create; ACME often requires admin originator)
        if not register_AE(originator_ae_create):
            registration_status = f"AE registration failed for '{application_name}'"
            return False
        atexit.register(lambda: unregister_AE(application_name, originator_ae_create))
        registration_status = f"AE '{application_name}' registered successfully"
        print(registration_status)
        final_registration_status = "Orchestrator AE successfully created"

        # Subscribe to gatewayAgent/data (no own containers; observe Gateway's data via oneM2M)
        subscribe_to_gateway_data()

        return True

    except Exception as e:
        registration_status = f"Error registering AE: {e}"
        return False


# --- Gateway control (Orchestrator → Gateway via IN-CSE) ---
def send_command_to_gateway(content: str) -> tuple:
    """Create contentInstance in gatewayAgent/cmd. Uses originator_gateway_control (CAdmin) for CREATE privilege."""
    return create_contentInstance_with_response(originator_gateway_control, gateway_cmd_path, content)


def send_data_to_gateway(content: str) -> tuple:
    """Create contentInstance in gatewayAgent/data. Uses originator_gateway_control (CAdmin) for CREATE privilege."""
    return create_contentInstance_with_response(originator_gateway_control, gateway_data_path, content)
