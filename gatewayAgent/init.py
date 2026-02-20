import subprocess
import configparser, os
from pathlib import Path

def start_CSE(docker_container:str)->bool:
    r=subprocess.run(["docker", 'start', docker_container], capture_output=True, text=True)

    if r.returncode!=0:
        print('CSE failed:', "rc:", r.returncode, "STDOUT:", r.stdout, "STDERR:", r.stderr)
        return False
    print('CSE Started successfully')
    return True

def stop_docker(docker_container):
    subprocess.run(["docker", "stop", docker_container], check=False)

def update_config(dirfilename, name):
    #cseID = id-mn1
    #cseName = cse-mn1
    parent=os.path.dirname(__file__)
    grandparent=os.path.dirname(parent)
    ini_path=os.path.join(grandparent, dirfilename)
    p=Path(ini_path)
    if not p.exists():
        raise FileNotFoundError(p)
    cfg=configparser.ConfigParser()
    cfg.optionxform=str
    cfg.read(p)
    cfg['basic.config']["cseName"]='cse-'+name
    cfg['basic.config']["cseID"]='id-'+name

    with p.open("w") as f:
        cfg.write(f)
    
    print(f"Configuration updated successfully")