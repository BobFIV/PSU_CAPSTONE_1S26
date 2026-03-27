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

from cse import start_CSE, update_config, read_config, stop_CSE, set_nummn, set_localports

from processData import process_cin, parse_cin

# import logging
# import requests

# import sys

# Start the notification server first
run_notification_receiver()
set_nummn()
set_localports()
# print(localports)


# Register gatewayAgent AE and create cmd/data only under gatewayAgent (orchestrator does not create these)
# Register an AE
if register_AE(originator, application_name, cse_url) == False:
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

# while not notify_q:
#     data=notify_q.get()
# if create_subscription(originator, application_path+'/data', subscription_name, notificationURIs) == False:
#     unregister_AE(originator, application_name)
#     stop_notification_receiver()
#     exit()

print("Waiting for orchestrator to create CIN")
while True: #stop when no notification, don't keep retrieving
    #another sub on data for gateway with field data| or cmd| OR only proceed when notification, add delete notification (current net=[3])
    data=notify_q.get() #block when q is empty
    # print(94,data)

    try:
        cin_cmd= process_cin(data)
        # cin_cmd=retrieve_contentinstance(originator, application_path+'/data/la')
        if cin_cmd['con']=='execute': #cmd
            if delete_contentinstance(application_path+'/cmd/'+cin_cmd['rn']):
                try:
                    #orchestrator create data first so this way will retrieve both
                    #gateway is late so this cin can be already old=>concern
                    cin_data=retrieve_contentinstance(originator, application_path+'/data/la') #only la needed for data
                    # print(cin_data)
                    if 'cseName' in cin_data['con']: #condition
                        mn_id, mn_name, mn_loport, docker_name=update_config(cin_data['con'])
                        mn_port=read_config(f'{docker_name}/acme.ini', 'httpPort')
                        mn_url=f'http://localhost:{mn_loport}/~/{mn_id}/{mn_name}'
                        
                        if start_CSE(mn_id, docker_name, mn_loport, mn_port): #container name==cse name-> don't give name
                            register_AE('CgatewayAgentMN', 'gatewayAgentMN', mn_url)
                except KeyError:
                    print("CIN does not exist in data")

        else:
            print("Not execute command")
        

            # unregister_AE(originator, application_name)
            # stop_notification_receiver()
            # exit()
        # cin=retrieve_contentinstance(originator, application_path+'/data/la')
        # data=cin['con']

    except KeyError:
        print("CIN does not exist in cmd")
    
    


# Content in gatewayAgent/cmd and gatewayAgent/data (orchestrator pushes via API; optional initial values here)
# register_AE('Corchestrator', 'orchestrator', cse_url)
# create_contentInstance(originator, application_path+'/cmd', 'execute')
# create_contentInstance(originator, application_path+'/data', 'cseName=cse-mn1\ncseID=id-mn1\nlocalPort=8081\n')




# Retrieve the <container> resource
        # cin=retrieve_contentinstance(originator, application_path+'/cmd/la')
        
        
# register_AE('CgatewayAgentMN', 'gatewayAgentMN', f'http://localhost:8081/~/id-mn1/cse-mn1')

# Unregister the AE and stop the notification server
# unregister_AE(originator, application_name)
# stop_notification_receiver()

    atexit.register(lambda:unregister_AE(originator, application_name))
    atexit.register(lambda:stop_notification_receiver())
# atexit.register(lambda:stop_CSE())

