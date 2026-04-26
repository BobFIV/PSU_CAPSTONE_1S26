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

# import atexit

from cse import start_CSE, update_config, read_config
from node import retrieve_node

from processData import process_cin, parse_cin
import time
import re
import signal
from finish import shutdown

# import logging
# import requests

# import sys

# Start the notification server first
run_notification_receiver()

d=re.search(r'(\d+)$', application_name)
if not d:
    raise ValueError
node_name='gw-node-0'+d.group(1)

for i in range(200):
    print("Trying registering AE")
    try:
        node_url=f"{node_base_url}/{node_name}"
        if retrieve_node('CAdmin', f'{cse_url}/{node_name}'):
            if register_AE(originator, application_name, cse_url, node_url) == False:
                stop_notification_receiver()
                exit()
            break
    except Exception:
        time.sleep(2)


# Create a <container> resource
# if create_container(originator, application_path, 'cmd')==False:
#     stop_notification_receiver()
#     exit()

# if create_container(originator, application_path, 'data')==False:
#     stop_notification_receiver()
#     exit()

# Create a <subscription> resource under the <container> resource
if create_subscription('CAdmin', f'{cse_url}/{node_name}/resources/gateway_cmd', subscription_name, notificationURIs) == False:
    unregister_AE(originator, application_name, cse_url)
    stop_notification_receiver()
    exit()



print("Waiting for orchestrator to create CIN")
while True: 
    data=notify_q.get() #block when q is empty


    try:
        cin_cmd= process_cin(data)
        
        if cin_cmd['con']=='execute': #cmd
            if delete_contentinstance('CAdmin', f'{cse_url}/{node_name}/resources/gateway_cmd/'+cin_cmd['rn']):
                try:
                   
                    cin_data=retrieve_contentinstance('CAdmin', f'{cse_url}/{node_name}/resources/gateway_data/la') #only la needed for data
                   
                    if 'cseName' in cin_data['con']: 
                        mn_id, mn_name, mn_loport, docker_name, update=update_config(cin_data['con'])
                        mn_port=read_config(f'{docker_name}/acme.ini', 'httpPort')
                        # mn_url=f'http://localhost:{mn_loport}/~/{mn_id}/{mn_name}' #mn_loport(pi port):cseport
                        mn_url=f'http://{docker_name}:{mn_port}/~/{mn_id}/{mn_name}' 
                        if start_CSE(mn_id, docker_name, mn_name, mn_loport, mn_port, mn_url, update, network_name=docker_net): #container name==networkhostname, dockernet is defined
                            register_AE(originator+'MN', application_name+'MN', mn_url)
                            
                except KeyError:
                    print("CIN does not exist in data")

        else:
            print("Not execute command")


    except KeyError:
        print("CIN does not exist in cmd")
    

    
    signal.signal(signal.SIGINT, lambda signum, frame: shutdown(docker_name, mn_id,originator+'MN', application_name+'MN', mn_url, signum, frame))   # Ctrl+C
    signal.signal(signal.SIGTERM, lambda signum, frame: shutdown(docker_name, mn_id,originator+'MN', application_name+'MN', mn_url, signum, frame))
    # atexit.register(shutdown)


