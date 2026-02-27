"""Handle subscription notifications from CSE (e.g. new contentInstance in gatewayAgent/cmd)."""


def process_cin(data:str):
    return data['m2m:sgn']['nev']['rep']['m2m:cin']

def parse_cin(data):
    #"csename=df"
    lst=data.split('\n')
    d={}
    for field in lst[:-1]:
        l=field.split("=")
        section, info = l[0], l[1]
        d[section]=info
    return d
