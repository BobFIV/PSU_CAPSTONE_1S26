import subprocess
import configparser, os
from pathlib import Path
from processData import parse_cin
from setup import *
import time, requests

def start_CSE(id:str, name:str, loport:str, port:str, timeout:float=12)->bool:
    #docker run -it -p 8081:8080 -e hostIPAddress=localhost -v ./acme_in:/data --name acme-in ankraft/acme-onem2m-cse:latest
    subprocess.run(["docker", "rm", "-f", name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cmd=["docker", "run", "--rm", "--name", name]
    cmd+=["-d"]
    cmd+=["-p", f"{loport}:{port}", "-e", "hostIPAddress=localhost", "-v", f"./acme_mn1:/data", image]
    r=subprocess.run(cmd, capture_output=True, text=True, cwd=grandparent)

    url=f'http://localhost:{loport}/~/{id}/{name}'
    headers={
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": "ping",
        "X-M2M-RVI": "4",
        "Accept": "application/json",
    }
    if r.returncode!=0:
        print('CSE failed:', "rc:", r.returncode, "STDOUT:", r.stdout, "STDERR:", r.stderr)
        return False
    
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, headers=headers, timeout=1)
            print('CSE Started successfully')
            # any HTTP response means server is up enough to talk
            return True
        except requests.RequestException:
            time.sleep(0.2)
    print('CSE failed: time out')
    return False

def stop_CSE(docker_container):
    subprocess.run(["docker", "stop", docker_container], check=False)

def read_config(dirfilename, section): #not using yet
    # parent=os.path.dirname(__file__)
    # grandparent=os.path.dirname(parent)
    ini_path=os.path.join(grandparent, dirfilename)
    p=Path(ini_path)
    cfg=configparser.ConfigParser()
    cfg.optionxform=str
    cfg.read(p)
    return cfg['basic.config'][section]

def update_config(dirfilename, data):
    #update and return new configs
    ini_path=os.path.join(grandparent, dirfilename)
    p=Path(ini_path)
    if not p.exists():
        raise FileNotFoundError(p)
    d=parse_cin(data)
    cfg=configparser.ConfigParser()
    cfg.optionxform=str
    cfg.read(p)
    for section,name in d.items():
        if cfg.has_section(section):
            cfg['basic.config'][section]=name
        else:
            port= name
    #can be more

    with p.open("w") as f:
        cfg.write(f)
    
    print(f"Configuration updated successfully")
    return cfg['basic.config']['cseID'],cfg['basic.config']['cseName'], port