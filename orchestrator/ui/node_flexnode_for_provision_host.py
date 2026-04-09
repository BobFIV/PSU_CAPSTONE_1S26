import requests
from .setup import randomID

import logging

logger = logging.getLogger(__name__)

def create_node(originator: str, path: str, rn: str) -> bool:
    """ Create a <node> resource under CSEBase

    Args:
        originator: The originator of the request
        path: The path of the CSEBase (e.g., /in-cse/in-name)
        rn: The resource name of the <node>

    Returns:
        bool: True if created successfully, False otherwise
    """

    headers = {
        'Content-Type': 'application/json;ty=14',
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4'
    }

    body = {
        'm2m:nod': {   
            'rn': rn,
            # optional:
            # 'ni': rn,
            # 'lbl': ['node']
        }
    }

    response = requests.post(path, headers=headers, json=body)

    if response.status_code == 201:
        logger.info("Node created successfully (rn=%s, path=%s)", rn, path)
    else:
        logger.error(
                "Error creating node (rn=%s, status=%s): %s",
                rn,
                response.status_code,
                response.text
            )
        return False

    return True

#from the documentation we can get that a flexnode is just a flex container
def create_flex_container(originator: str, path: str, rn: str) -> bool:
    headers = {
        'Content-Type': 'application/json;ty=28',
        'X-M2M-Origin': originator,
        'X-M2M-RI': randomID(),
        'X-M2M-RVI': '4'
    }

    body = {
        'm2m:fcn': {
            'rn': rn,
            'cnd': 'org.onem2m.common.moduleclass.custom' #the custom here I belive can be changed
        }
    }

    response = requests.post(path, headers=headers, json=body)

    if response.status_code == 201:
        logger.info("FlexContainer created successfully (rn=%s, path=%s)", rn, path)
        return True
    else:
        logger.error(
                "Error creating FlexContainer (rn=%s, status=%s): %s",
                rn,
                response.status_code,
                response.text
            )
        return False