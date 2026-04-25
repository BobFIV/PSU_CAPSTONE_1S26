import random, string
from dataclasses import dataclass
from queue import Queue
import os
# from dotenv import load_dotenv
from config import GatewayConfig

import docker
import re




def _build_docker_client(cfg: GatewayConfig) -> docker.DockerClient:
    if cfg.docker_host:
        return docker.DockerClient(base_url=cfg.docker_host)
    return docker.from_env()

def randomID() -> str:
    """ Generate an ID. Prevent certain patterns in the ID.

        Return:
            String with a random ID
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k = 10))

# load_dotenv()
cfg=GatewayConfig.from_env()
client = _build_docker_client(cfg)

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
docker_host=cfg.docker_host
docker_net=cfg.docker_net

application_path = cse_url + "/" + application_name
# parent=os.path.dirname(__file__)
# grandparent=os.path.dirname(parent)
notify_q=Queue()
node_base_url=cse_url.split("~")[1]


#container(docker) name=directory name =in docker network name
#id-mn=csr name
#"cb": "/"+id+"/"+mn_name
#"csi": "/"+id

