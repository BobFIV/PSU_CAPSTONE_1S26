import subprocess
import configparser, os
from pathlib import Path
from processData import parse_cin, parse_port
from setup import *
import time, requests

#use container id or name-> if same, restart, if not, leave it and create new one.
#currently it's deleting and creating but don't delete it
def start_CSE(id:str, name:str, loport:str, port:str, timeout:float=12)->bool:
    #docker run -it -p 8081:8080 -e hostIPAddress=localhost -v ./acme_in:/data --name acme-in ankraft/acme-onem2m-cse:latest
    # subprocess.run(["docker", "rm", "-f", name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    global MAX_MN
    global localports

    
    if exists_CSE(name): #same cse=name and port
        old_port=check_port_mapping(name)
        if loport != old_port: # same name diff port-> delete/create
            if loport in localports:
                print("Want to move port? Port is already allocated")
                return False
            localports.remove(old_port)
            localports.append(loport)
            subprocess.run(["docker", "rm", "-f", name], check=False, cwd=grandparent)
            cmd = ["docker", "run", "--name", name, "-d",
               "-p", f"{loport}:{port}",
               "-e", "hostIPAddress=localhost",
               "-v", f"./{name}:/data", image]
        elif not is_running_CSE(name): #same name same port not running
            cmd=["docker", "start", name] #start
        else: #same name same port running
            print(f"CSE {name} already exists and running") #need orchestrator to warn user if name already there
            return True
            
    else:
        if MAX_MN==0:
            print("Reached maximum number of MN-CSE")
            return False
        if loport in localports:
            print("Want to create? Port is already allocated")
            return False
        localports.append(loport)
        MAX_MN-=1
        cmd=["docker", "run", "--name", name] #create
        cmd+=["-d"]
        cmd+=["-p", f"{loport}:{port}", "-e", "hostIPAddress=localhost", "-v", f"./{name}:/data", image]
    
    r=subprocess.run(cmd, capture_output=True, text=True, cwd=grandparent)
    
    if r.returncode!=0:
        print('CSE failed:', "rc:", r.returncode, "STDOUT:", r.stdout, "STDERR:", r.stderr)
        return False

    url=f'http://localhost:{loport}/~/{id}/{name}'
    headers={
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": "ping",
        "X-M2M-RVI": "4",
        "Accept": "application/json",
    }
    
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            response = requests.get(url, headers=headers, timeout=1)
            print('CSE Started successfully')
            # any HTTP response means server is up enough to talk
            return True
        except requests.RequestException:
            time.sleep(0.2)
    print('CSE failed: time out')
    return False

def get_all_containers():
    r = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    if r.returncode != 0:
        return []
    return [line.strip() for line in r.stdout.strip().split()]

def stop_CSE(docker_container):
    subprocess.run(["docker", "stop", docker_container], check=False)

def exists_CSE(name):
    r=subprocess.run(["docker", "inspect", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=grandparent)
    if r.returncode!=0:
        print('CSE not found:', "rc:", r.returncode, "STDOUT:", r.stdout, "STDERR:", r.stderr)
        return False
    return True

def is_running_CSE(name):
    r = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", name],
            capture_output=True,
            text=True,
            cwd=grandparent,
        )
    if r.returncode!=0:
        print('CSE not running: ', "rc:", r.returncode, "STDOUT:", r.stdout, "STDERR:", r.stderr)
        return False
        
    return r.stdout.strip().lower()=="true"

def check_port_mapping(name):
    r = subprocess.run(
        ["docker", "port", name],
        capture_output=True,
        text=True,
        cwd=grandparent,
    )
    # if r.returncode != 0:
    #     return False
    # expected = f"{port}/tcp -> 0.0.0.0:{loport}"
    # expected_ipv6 = f"{port}/tcp -> [::]:{loport}"
    out = r.stdout
    # print("this",out)
    old_port=parse_port(out.strip())
    return old_port

def read_config(dirfilename, section): #not using yet
    # parent=os.path.dirname(__file__)
    # grandparent=os.path.dirname(parent)
    ini_path=os.path.join(grandparent, dirfilename)
    p=Path(ini_path)
    cfg=configparser.ConfigParser()
    cfg.optionxform=str
    cfg.read(p)
    return cfg['basic.config'][section]

def update_config(data):
    #update and return new configs
    d=parse_cin(data)
    dirfilename=f"{d["dockerName"]}/acme.ini"
    ini_path=os.path.join(grandparent, dirfilename)
    p=Path(ini_path)

    if not p.exists():
        os.makedirs(os.path.dirname(ini_path), exist_ok=True)
        with p.open("x") as f:
            f.write(f"[basic.config]\ncseType = MN\ncseID = {d["cseID"]}\ncseName = {d["cseName"]}\n"+
                    "serviceProviderID = //acme.example.com\n"+
                    "adminID = CAdmin\n"+
                    "networkInterface = 0.0.0.0\n"+
                    "cseHost = ${hostIPAddress}\n"+
                    "httpPort = 8080\n"+
                    "cseSecret = MY_SECRET\n"+""
                    "databaseType = tinydb\n"+
                    "logLevel = debug\n"+
                    "consoleTheme = dark\n\n"+
                    "[cse.registration]\n"+
                    "allowedCSROriginators = /id-in,/id-mn*,/id-asn\n\n"+
                    "[textui]\n"+
                    "startWithTUI = false\n\n"+
                    "[cse.operation.requests]\n"+
                    "enable = true\n\n"+
                    "[http]\n"+
                    "enableUpperTesterEndpoint = true\n"+
                    "enableStructureEndpoint = true\n"+
                    "enableManagementEndpoint = true")
           
    
    else:
        cfg=configparser.ConfigParser()
        cfg.optionxform=str
        cfg.read(p)
        for option,name in d.items():
            if cfg.has_option('basic.config', option):
                cfg['basic.config'][option]=name
            
        #can be more

        with p.open("w") as f:
            cfg.write(f)
    
    print(f"Configuration updated successfully")
    return d['cseID'],d['cseName'], d['localPort'], d['dockerName']

def set_maxmn():
    global MAX_MN
    r = subprocess.run(["docker", "ps", "-aq"], capture_output=True, text=True)
    MAX_MN-=len([x for x in r.stdout.split('\n') if x.strip()])+1


def set_localports():
    global localports
    r=subprocess.run(["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"], capture_output=True, text=True)
    out=r.stdout
    # print(out)
    for line in out.strip().split('\n'):
        # print(out)
        localports.append(parse_port(line))
    # print(localports)