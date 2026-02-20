"""Handle subscription notifications from CSE (e.g. new contentInstance in gatewayAgent/cmd)."""


def process(data:str):
    return data['m2m:sgn']['nev']['rep']['m2m:cin']

