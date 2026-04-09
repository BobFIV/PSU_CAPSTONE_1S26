"""Handle subscription notifications from CSE (e.g. new contentInstance in gatewayAgent/cmd)."""


def process_cin(data:str):
    return data['m2m:sgn']['nev']['rep']['m2m:cin']


def parse_cin(data):
    lst = [field for field in data.strip().split('\n') if field.strip()]
    d = {}
    for field in lst:
        if "=" not in field:
            continue
        section, info = field.split("=", 1)
        d[section] = info
    return d

def parse_port(data):
    #8080/tcp -> 0.0.0.0:8081
    lst=data.strip().split('->')
    # print(lst)
    contains_port=lst[0] if ":" in lst[0] else lst[1]
    # print(contains_port)
    lst2=contains_port.strip().split()
    contains_port2=lst2[0] if ":" in lst2[0] else lst2[1]
    port=contains_port2.split(":")[1].strip()
    # print(port)
    return port