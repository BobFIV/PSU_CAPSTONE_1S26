import random, string
from dataclasses import dataclass
from queue import Queue
import os
from dotenv import load_dotenv
from config import GatewayConfig

import docker

client = docker.from_env()

# Setup variables
# cse_url = 'http://localhost:8080/~/id-in/cse-in'            # The url of the CSE - use host port of 8081 for mn1, 8080 for in
# notificationURIs = ['http://host.docker.internal:9000']                # The notification target
# application_name = 'gatewayAgent'                         # The name of the application entity
# application_path = cse_url + '/' + application_name         # The path of the application entity
# subscription_name = 'gatewaySubscription'                        # The name of the subscription
# originator = 'CgatewayAgent'
# image='ankraft/acme-onem2m-cse:latest'


load_dotenv()
cfg=GatewayConfig.from_env()


cse_url = cfg.in_cse_base_url
originator = cfg.originator_id
application_name = cfg.application_name
subscription_name = cfg.subscription_name
image = cfg.image
acme_image=cfg.acme_image
# MAX_MN = cfg.max_mn
notificationURIs = [cfg.callback_url]
host_cse_base=cfg.host_cse_base_dir
cnt_cse_base=cfg.cnt_cse_base_dir

application_path = cse_url + "/" + application_name
# parent=os.path.dirname(__file__)
# grandparent=os.path.dirname(parent)
notify_q=Queue()
# localports=[]
# num_mn=0
# not create ini folder if reached maximum (or cse not started)

# container_name='cmd'
# container_path=application_path+'/'+container_name

# originator = Cgateway
# acme port: 8080
# port for acme: 8080, 8081, 8082
# port for notification: 9000

# @dataclass
# class Cfg:
#     cse_url:str           # The url of the CSE - use host port of 8081 for mn1, 8080 for in
#     notificationURIs:list[str]               # The notification target
#     application_name:str                         # The name of the application entity
#     application_path:str        # The path of the application entity
#     subscription_name:str                      # The name of the subscription
#     originator:str
#     container_name:str
#     container_path:str


def randomID() -> str:
    """ Generate an ID. Prevent certain patterns in the ID.

        Return:
            String with a random ID
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = 10))

