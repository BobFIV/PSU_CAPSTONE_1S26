# PSU_CAPSTONE_1S26
oneM2M Orchestrator

## Running CSEs
- Mount and start IN-CSE
~~~sh
docker run -it -p 8080:8080 -e hostIPAddress=localhost -v ./acme_in:/data --name acme-in ankraft/acme-onem2m-cse:latest
~~~


- Check for running container
~~~sh
docker ps
~~~

## MSC
participant GA as GatewayAgent
participant IN as IN-CSE (ACME)
participant MN as MN-CSE (ACME)
participant CB as Callback Server

1. Start MN-CSE
    - ACME on :8080, mapped to host :8080
2. Gateway Agent reads config
    - MN-CSE base URL: http://localhost:8080
    - originator: Sgateway
    - notification URL: 
3. Start callback server on :9000
4. AE registration
    - GA $\to$ MN: CREATE AE
    - MN $\to$ GA: 201 Created
5. Container Setup
    - GA $\to$ MN: CREATE cmd, data
    - MN $\to$ GA: 201 Created
6. Subscription Setup
    - GA $\to$ MN: CREATE sub
    - MN $\to$ GA: 201 Created

## WireGuard Deployment Flow

Gateway WireGuard deployment now follows the same oneM2M control path used for MN-CSE startup:

1. Orchestrator `POST /api/gateway/data/`
2. Payload is stored in `gatewayAgent/data`
3. Orchestrator sends `execute` to `gatewayAgent/cmd`
4. Gateway receives the notification and reads the latest `data`
5. If `vpnType=wireguard`, Gateway:
   - installs `wireguard` if needed
   - generates private/public keys
   - writes `/etc/wireguard/wg0.conf`
   - runs `wg-quick up wg0`
   - runs `systemctl enable wg-quick@wg0`
   - reports the gateway public key to `POST /api/wireguard/peers/`

Example payload:

```json
{
  "vpnType": "wireguard",
  "wgInterface": "wg0",
  "wgAddress": "10.0.0.2/24",
  "wgServerPublicKey": "<server-public-key>",
  "wgEndpoint": "vpn.example.com:51820",
  "wgAllowedIPs": "10.0.0.0/24",
  "wgPersistentKeepalive": 25,
  "cseName": "cse-mn1",
  "cseID": "id-mn1",
  "localPort": "8081"
}
```

Stored peer keys can be queried from:

```sh
curl http://127.0.0.1:8000/api/wireguard/peers/
```

Generated server-side WireGuard peer config can be queried from:

```sh
curl http://127.0.0.1:8000/api/wireguard/server-config/
```

For local macOS code-path testing without root privileges, run the gateway with:

```sh
ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000 WG_CONFIG_DIR=$(pwd)/.wg WG_KEY_DIR=$(pwd)/.wg WG_SKIP_INTERFACE_UP=1 python3 main.py
```

## WireGuard Changes

The following WireGuard-related changes were added:

1. The orchestrator now accepts WireGuard deployment fields through `POST /api/gateway/data/`.
2. The gateway parses WireGuard settings from the oneM2M `data` container and starts WireGuard handling when it receives `execute`.
3. The gateway generates a private key, public key, and `wg0.conf`.
4. The gateway reports its generated public key back to the orchestrator through `POST /api/wireguard/peers/`.
5. The orchestrator stores reported peer keys and metadata in `orchestrator/ui/data/wireguard_peers.json`.
6. The orchestrator automatically generates server-side peer config in `orchestrator/ui/data/wireguard_server_peers.conf`.
7. The existing MN-CSE deployment flow continues after the WireGuard handling step.

## WireGuard Test Steps

### macOS local test

This validates the code path, key generation, config generation, peer reporting, and local interface bring-up.

1. Start the IN-CSE from the project root:

```sh
docker rm -f acme-in 2>/dev/null
docker run -d -p 8080:8080 -e hostIPAddress=localhost -v "$(pwd)/acme_in:/data" --name acme-in ankraft/acme-onem2m-cse:latest
docker logs --tail 30 acme-in
```

2. Start the orchestrator:

```sh
cd /Users/taehyunkim/capstone/PSU_CAPSTONE_1S26/orchestrator
source venv/bin/activate
python manage.py runserver 127.0.0.1:8000
```

3. Start the gateway in macOS-safe test mode:

```sh
cd /Users/taehyunkim/capstone/PSU_CAPSTONE_1S26/gatewayAgent
mkdir -p .wg
ORCHESTRATOR_BASE_URL=http://127.0.0.1:8000 WG_CONFIG_DIR=$(pwd)/.wg WG_KEY_DIR=$(pwd)/.wg WG_SKIP_INTERFACE_UP=1 python3 main.py
```

4. Send a WireGuard deployment payload:

```sh
curl -X POST http://127.0.0.1:8000/api/gateway/data/ \
  -H "Content-Type: application/json" \
  -d '{
    "vpnType":"wireguard",
    "wgInterface":"wg0",
    "wgAddress":"10.0.0.2/24",
    "wgServerPublicKey":"<server-public-key>",
    "wgEndpoint":"127.0.0.1:51820",
    "wgAllowedIPs":"10.0.0.0/24",
    "wgPersistentKeepalive":25,
    "cseName":"cse-mn1",
    "cseID":"id-mn1",
    "localPort":"8081"
  }'
```

5. Confirm generated files and stored peer data:

```sh
ls -la /Users/taehyunkim/capstone/PSU_CAPSTONE_1S26/gatewayAgent/.wg
curl http://127.0.0.1:8000/api/wireguard/peers/
curl http://127.0.0.1:8000/api/wireguard/server-config/
cat /Users/taehyunkim/capstone/PSU_CAPSTONE_1S26/orchestrator/ui/data/wireguard_server_peers.conf
```

6. Optional macOS interface bring-up test:

Create a temporary test server public key:

```sh
wg genkey | tee /tmp/wg_server.key | wg pubkey > /tmp/wg_server.pub
cat /tmp/wg_server.pub
```

Replace `wgServerPublicKey` in `gatewayAgent/.wg/wg0.conf` with that generated public key, then run:

```sh
sudo wg-quick up /Users/taehyunkim/capstone/PSU_CAPSTONE_1S26/gatewayAgent/.wg/wg0.conf
sudo wg show
ifconfig utun7
sudo wg-quick down /Users/taehyunkim/capstone/PSU_CAPSTONE_1S26/gatewayAgent/.wg/wg0.conf
```

Note: on macOS the `wg0` configuration is mapped to a `utun` interface such as `utun7`.

### Linux SBC validation

This is the target-environment validation for actual interface startup and persistence.

1. Install WireGuard if needed:

```sh
sudo apt-get update
sudo apt-get install -y wireguard wireguard-tools
```

2. Start the gateway on the SBC without `WG_SKIP_INTERFACE_UP`:

```sh
cd /path/to/PSU_CAPSTONE_1S26/gatewayAgent
sudo env ORCHESTRATOR_BASE_URL=http://<orchestrator-ip>:8000 python3 main.py
```

3. Send the same WireGuard payload from the orchestrator host.

4. Verify the interface and persistence on the SBC:

```sh
sudo cat /etc/wireguard/wg0.conf
sudo wg show
ip addr show wg0
sudo systemctl status wg-quick@wg0
sudo systemctl is-enabled wg-quick@wg0
```
