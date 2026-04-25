import signal
import sys

from ae import unregister_AE
from setup import *
import requests
from cse import remove_CSE
from notificationReceiver import stop_notification_receiver
import time


def cleanup(docker_name, mn_id, mn_originator, mn_AEname, mn_url):
    ok=unregister_AE(mn_originator, mn_AEname, f'{mn_url}/{mn_AEname}')
    csr_mn_url=f"{mn_url}/id-in" #hard coded
    headers={
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": randomID(),
        "X-M2M-RVI": "4"
    }
    r = requests.delete(csr_mn_url, headers=headers, timeout=10)
    if r.status_code in (200,202,204):
        print("CSR(MN-side) Successfully deleted")
    else:
        print(f"CSR(MN-side) delete failed: {r.status_code} {r.text}")

    csr_in_url=f"{cse_url}/{mn_id}"
    headers={
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": randomID(),
        "X-M2M-RVI": "4"
    }
    r = requests.delete(csr_in_url, headers=headers, timeout=10)
    if r.status_code in (200,202,204):
        print("CSR(IN-side) Successfully deleted")
    else:
        print(f"CSR(IN-side) delete failed: {r.status_code} {r.text}")
    
    unregister_AE(originator, application_name, cse_url + '/' + application_name)
    if ok:
        time.sleep(2)
        remove_CSE(docker_name)
    print("Gateway cleanup completed")



def shutdown(docker_name, mn_id, mn_originator, mn_AEname, mn_url, signum=None, frame=None):

    print("\nShutting down...")

    try:
        stop_notification_receiver()
    except Exception as e:
        print(f"Error stopping receiver: {e}")

    try:
        cleanup(docker_name, mn_id, mn_originator, mn_AEname, mn_url)
    except Exception as e:
        print(f"Error during cleanup: {e}")

    sys.exit(0)
