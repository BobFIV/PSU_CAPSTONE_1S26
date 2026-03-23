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
