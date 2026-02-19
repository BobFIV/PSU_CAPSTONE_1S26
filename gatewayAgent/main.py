# Import the setup variables
from setup import *                                     

# Import AE functions
from ae import register_AE, unregister_AE, retrieve_AE

from container import create_container

# Import subscription function
from subscription import create_subscription 

from contentInstance import create_contentInstance

# Import notification function
from notificationReceiver import run_notification_receiver, stop_notification_receiver

# import sys



# if len(sys.argv)!=3:
#     print("Format Error: python3 main.py IN/MN1/MN2 CONTAINER")
#     sys.exit(1)

# if sys.argv[1]=='IN':
#     cse_url = 'http://localhost:8080/~/id-in/cse-in'            # The url of the CSE - use host port of 8081 for mn1, 8080 for in
#     notificationURIs = ['http://host.docker.internal:9000']                # The notification target
#     application_name = 'gatewayAgent'                         # The name of the application entity
#     application_path = cse_url + '/' + application_name         # The path of the application entity
#     subscription_name = 'gatewaySubscription'                        # The name of the subscription
#     originator = 'CgatewayAgent'
#     container_name=sys.argv[2]
#     container_path=application_path+'/'+container_name

# # Setup variables
# elif sys.argv[1]=='MN1':
#     cse_url = 'http://localhost:8081/~/id-mn1/cse-mn1'            # The url of the CSE - use host port of 8081 for mn1, 8080 for in
#     notificationURIs = ['http://host.docker.internal:9000']                # The notification target
#     application_name = 'gatewayAgentMN1'                         # The name of the application entity
#     application_path = cse_url + '/' + application_name         # The path of the application entity
#     subscription_name = 'gatewaySubscription'                        # The name of the subscription
#     originator = 'CgatewayAgentMN1'
#     container_name=sys.argv[2]
#     container_path=application_path+'/'+container_name

# elif sys.argv[1]=='MN2':
#     cse_url = 'http://localhost:8082/~/id-mn2/cse-mn2'            # The url of the CSE - use host port of 8081 for mn1, 8080 for in
#     notificationURIs = ['http://host.docker.internal:9000']                # The notification target
#     application_name = 'gatewayAgentMN2'                          # The name of the application entity
#     application_path = cse_url + '/' + application_name         # The path of the application entity
#     subscription_name = 'gatewaySubscription'                        # The name of the subscription
#     originator = 'CgatewayAgentMN2'
#     container_name=sys.argv[2]
#     container_path=application_path+'/'+container_name

# cfg=Cfg(cse_url, notificationURIs, application_name, application_path, subscription_name, originator, container_name, container_path)

# Start the notification server first
run_notification_receiver()

# Register an AE
if register_AE(originator, application_name) == False:
    stop_notification_receiver()
    exit()

# Create a <container> resource
if create_container(originator, application_path, 'cmd')==False:
    stop_notification_receiver()
    exit()

if create_container(originator, application_path, 'data')==False:
    stop_notification_receiver()
    exit()

# Create a <subscription> resource under the <container> resource
if create_subscription(originator, application_path, subscription_name, notificationURIs) == False:
    unregister_AE(originator, application_name)
    stop_notification_receiver()
    exit()

# Retrieve the <container> resource
if retrieve_AE(originator, application_path) == False:
    unregister_AE(originator, application_name)
    stop_notification_receiver()
    exit()

# Unregister the AE and stop the notification server
# unregister_AE(originator, application_name)
# stop_notification_receiver()
