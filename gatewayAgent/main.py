# Import the setup variables
from setup import *                                     

# Import AE functions
from ae import register_AE, unregister_AE

from container import create_container, retrieve_container

# Import subscription function
from subscription import create_subscription 

from contentInstance import create_contentInstance, retrieve_contentinstance, delete_contentinstance

# Import notification function
from notificationReceiver import run_notification_receiver, stop_notification_receiver

import atexit

from init import start_CSE, update_config


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

# Register gatewayAgent AE and create cmd/data only under gatewayAgent (orchestrator does not create these)
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
if create_subscription(originator, application_path+'/cmd', subscription_name, notificationURIs) == False:
    unregister_AE(originator, application_name)
    stop_notification_receiver()
    exit()






# Content in gatewayAgent/cmd and gatewayAgent/data (orchestrator pushes via API; optional initial values here)
create_contentInstance(originator, application_path+'/cmd', 'execute')
create_contentInstance(originator, application_path+'/data', 'acme-mn1')



# Retrieve the <container> resource
cin=retrieve_contentinstance(originator, application_path+'/cmd/la')
if cin['con']=='execute': #cmd
    if delete_contentinstance(application_path+'/cmd/'+cin['rn'])==False:
        pass

    # unregister_AE(originator, application_name)
    # stop_notification_receiver()
    # exit()
cin=retrieve_contentinstance(originator, application_path+'/data/la')
name=cin['con']
update_config('acme_mn1/acme.ini', name)
if start_CSE('acme-mn1')==False:
    pass




# Unregister the AE and stop the notification server
# unregister_AE(originator, application_name)
# stop_notification_receiver()

atexit.register(lambda:unregister_AE(originator, application_name))
atexit.register(lambda:stop_notification_receiver())

