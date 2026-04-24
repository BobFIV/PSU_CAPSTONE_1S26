import subprocess
import configparser, os
from pathlib import Path
from processData import parse_cin, parse_port
from setup import *
import time, requests
import shutil
from ae import unregister_AE





# import docker
from docker.errors import NotFound, APIError

# client = docker.from_env()



# better to use a named volume than "./{name}:/data"
# because Docker bind mounts are host-side, not relative to the gateway container's cwd

def get_cse_dirs(name: str):
    host_dir = Path(os.path.join(host_cse_base,name))
    container_dir = Path(os.path.join(cnt_cse_base, name))
    host_dir.mkdir(parents=True, exist_ok=True) #or cnt_base
    return host_dir, container_dir

def _volume_spec(name: str):
    host_dir, _=get_cse_dirs(name)
    return {
        str(host_dir): {
            "bind": "/data",
            "mode": "rw"
        }
    }

def exists_CSE(name: str) -> bool:
    try:
        client.containers.get(name)
        return True
    except NotFound:
        return False

def is_running_CSE(name: str) -> bool:
    try:
        c = client.containers.get(name)
        c.reload()
        return c.status == "running"
    except NotFound:
        return False

def check_port_mapping(name: str) -> str | None:
    try:
        c = client.containers.get(name)
        c.reload()
        ports = c.attrs["NetworkSettings"]["Ports"]
        # example key: "8080/tcp"
        port_info = ports.get("8080/tcp")
        if not port_info:
            return None
        return port_info[0]["HostPort"]
    except NotFound:
        return None

def remove_CSE(name: str) -> None:
    try:
        c = client.containers.get(name)
        c.remove(force=True)
    except NotFound:
        pass

def create_CSE(name: str, loport: str, port: str, network_name: str | None = None) -> bool:
    try:
        client.images.get(acme_image)
    except docker.errors.ImageNotFound:
        client.images.pull(acme_image)
    
    advertised_host=name if network_name else "host.docker.internal"
    kwargs = {
        "image": acme_image,
        "name": name,
        "detach": True,
        "ports": {f"{port}/tcp": int(loport)},
        "environment": {
            # use host.docker.internal only if the MN-CSE needs to call back to the host
            "hostIPAddress": advertised_host
        },
        "volumes": _volume_spec(name),
    }
    if network_name:
        kwargs["network"] = network_name

    client.containers.run(**kwargs)
    return True

def start_CSE(id: str, name: str, mn_name:str, loport: str, port: str, url, update, timeout: float = 12, network_name: str | None = None) -> bool:
    print(f"[start_CSE] entered name={name} loport={loport} port={port}, network={network_name}", flush=True)
    try:
        if exists_CSE(name):
                
            old_port = check_port_mapping(name)

            if old_port is None:
                print(f"CSE {name} exists but port mapping could not be read")
                return False

            # #let orchestrator not create same name docker twice. either delete and create or if update, do safety check. (no same name, id exists)
            # #when user input-> orchestrator check if same name docker exists.-> if yes, check if all fields are the same
            # # if not, update it with safetycheck
            # # so anything sent here is safe. & add update: t/f field-> if updated, need to remove and create cse. if not, just restart
            if update or loport != old_port: # not exactly match
                remove_CSE(name)
                create_CSE(name, loport, port, network_name=network_name)


            elif not is_running_CSE(name): #name, port match
                c = client.containers.get(name)
                c.start()

            else:
                print(f"CSE {name} already exists and running")
                return True

        else:
            create_CSE(name, loport, port, network_name=network_name)
       
    except APIError as e:
        print("CSE failed:", str(e))
        return False

    # url = f"http://localhost:{loport}/~/{id}/{name}"
    # url = f"http://{name}:8080/~/{id}/{mn_name}"
    
    headers = {
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": "ping",
        "X-M2M-RVI": "4",
        "Accept": "application/json",
    }

    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            requests.get(url, headers=headers, timeout=1)
            # if not create_CSR(id, name, mn_name):
            #     print("CSE created but CSR registration failed")
            #     return False
            print("CSE Started successfully")
            return True
        except requests.RequestException:
            time.sleep(0.2)

    print("CSE failed: time out")
    return False

'''
#use container id or name-> if same, restart, if not, leave it and create new one.
#currently it's deleting and creating but don't delete it
def start_CSE(id:str, name:str, loport:str, port:str, timeout:float=12)->bool:
    #docker run -it -p 8081:8080 -e hostIPAddress=localhost -v ./acme_in:/data --name acme-in ankraft/acme-onem2m-cse:latest
    # subprocess.run(["docker", "rm", "-f", name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # global num_mn
    # global localports

    
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
        # if num_mn==MAX_MN:
        #     delete_config(name)
        #     print("Reached maximum number of MN-CSE")
        #     return False
        # if loport in localports:
        #     delete_config(name)
        #     print("Want to create? Port is already allocated")
        #     return False
        # localports.append(loport)
        # num_mn+=1
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
'''

def get_all_containers():
    r = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    if r.returncode != 0:
        return []
    return [line.strip() for line in r.stdout.strip().split()]

'''
def delete_CSE():
    pass

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
'''

def read_config(dirfilename, section): #not using yet
    # parent=os.path.dirname(__file__)
    # grandparent=os.path.dirname(parent)
    ini_path=os.path.join(cnt_cse_base, dirfilename)
    p=Path(ini_path)
    cfg=configparser.ConfigParser()
    cfg.optionxform=str
    cfg.read(p)
    return cfg['basic.config'][section]

def update_config(data):
    #update and return new configs
    d=parse_cin(data)
    dirfilename=f"{d['dockerName']}/acme.ini"
    ini_path=os.path.join(cnt_cse_base, dirfilename)
    p=Path(ini_path)
    update=False

    if not p.exists():
        os.makedirs(os.path.dirname(ini_path), exist_ok=True)
        with p.open("x") as f:
            f.write(f'[basic.config]\ncseType = MN\ncseID = {d["cseID"]}\ncseName = {d["cseName"]}\n'+
                    "serviceProviderID = //acme.example.com\n"+
                    "adminID = CAdmin\n"+
                    "networkInterface = 0.0.0.0\n"+
                    f'cseHost = {d["dockerName"]}\n'+ #dockername used as directory name and network host name
                    "httpPort = 8080\n"+
                    "cseSecret = MY_SECRET\n"+""
                    "databaseType = tinydb\n"+
                    "logLevel = debug\n"+
                    "consoleTheme = dark\n\n"+
                    "[cse.registrar]\n"+
                    "address = http://acme-in:8080\n"+
                    "cseID = /id-in\n"+
                    "resourceName = cse-in\n"+
                    "serialization = json\n\n"+
                    # "registrarCSEHost = acme-in\n"+
                    # "registrarCSEPort = 8080\n"+
                    # "registrarCSEID = /id-in\n"+
                    # "registrarCSEName = cse-in\n\n"+
                    "[cse.registration]\n"+
                    "allowedCSROriginators = /id-in\n\n"+
                    "[textui]\n"+
                    "startWithTUI = false\n\n"+
                    "[cse.operation.requests]\n"+
                    "enable = true\n\n"+
                    "[http]\n"+
                    "enableUpperTesterEndpoint = true\n"+
                    "enableStructureEndpoint = true\n"+
                    "enableManagementEndpoint = true\n\n"+
                    "[logging]\n"+
                    "enableScreenLogging = true")
        print(f"Configuration Created")
           
    
    else:
        cfg=configparser.ConfigParser()
        cfg.optionxform=str
        cfg.read(p)
        for option,name in d.items():
            if cfg.has_option('basic.config', option):
                if cfg['basic.config'][option]!=name:
                    update=True
                    cfg['basic.config'][option]=name
            
        #can be more

        with p.open("w") as f:
            cfg.write(f)
    if update:
        print(f"Configuration updated successfully")
    else:
        print(f"Nothing to update")
    return d['cseID'],d['cseName'], d['localPort'], d['dockerName'], update


# def set_nummn():
#     global num_mn
#     r = subprocess.run(["docker", "ps", "-aq"], capture_output=True, text=True)
#     num_mn+=len([x for x in r.stdout.split('\n') if x.strip()])-1


# def set_localports():
#     global localports
#     r=subprocess.run(["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"], capture_output=True, text=True)
#     out=r.stdout
#     # print(out)
#     for line in out.strip().split('\n'):
#         if '\t' not in line:
#             continue
#         ports_col = line.split('\t')[1]
#         for port_entry in ports_col.split(', '):
#             if '->' in port_entry:
#                 localports.append(parse_port(port_entry))
    # print(localports)

def delete_config(dirname):
    ini_path=os.path.join(host_cse_base, dirname)
    p=Path(ini_path)
    shutil.rmtree(p)

# def create_CSR (id:str, name:str, mn_name:str)->bool:
#     headers = {
#     "Content-Type": "application/json;ty=16", #or 13
#     "X-M2M-Origin": "/"+id,
#     "X-M2M-RI": randomID(),
#     "X-M2M-RVI": "5",
#     "Accept": "application/json",
#     }

#     body={
#         "m2m:csr": {
#             "rn": id,
#             "rr": True,
#             "csi": "/"+id,
#             "cst": 2,
#             "csz": ["application/json", "application/cbor"],
#             "poa": [f"http://{name}:8080"],
#             "srv": ["2a","3","4","5"],
#             "cb": "/"+id+"/"+mn_name,
#             "dcse": []
#         }
#     }
#     response = requests.post(cse_url, headers=headers, json=body)


#     # Check the response
#     if response.status_code == 201:
#         print('CSR created successfully')
#         return True
#     # if response.status_code == 403:
#     #     try:
#     #         text = (response.text or "")
#     #         if "already registered" in text and originator in text:
#     #             print("AE already exists (originator already registered on CSE)")
#     #             return True
#     #     except Exception:
#     #         pass
#     print('Error creating CSR: ' + str(response.status_code))
#     return False
    
def cleanup(docker_name, mn_id, mn_originator, mn_AEname):
    unregister_AE(mn_originator, mn_AEname)
    url=f"{cse_url}/{mn_id}"
    headers={
        "X-M2M-Origin": "CAdmin",
        "X-M2M-RI": randomID(),
        "X-M2M-RVI": "4"
    }
    r = requests.delete(url, headers=headers, timeout=10)
    if r.status_code in (200,202,204):
        print("CSR Successfully deleted")
    remove_CSE(docker_name)
    unregister_AE(originator, application_name)


