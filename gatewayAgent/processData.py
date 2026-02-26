"""Handle subscription notifications from CSE (e.g. new contentInstance in gatewayAgent/cmd)."""


def process(data):
    """Process oneM2M notification. On cmd contentInstance with con=='execute', handle execute command."""
    try:
        sgn = data.get("m2m:sgn") or {}
        if sgn.get("vrq"):
            return  # verification request, no payload to process
        nev = sgn.get("nev") or {}
        rep = nev.get("rep")
        if not rep:
            return
        cin = rep.get("m2m:cin")
        if not cin:
            return
        content = cin.get("con")
        if content == "execute":
            print("[processData] Received execute command from Orchestrator – ready for custom logic (e.g. config, restart).")
        elif content:
            print("[processData] Received data:", content[:100] if isinstance(content, str) else content)
    except Exception as e:
        print("[processData] Error:", e)
