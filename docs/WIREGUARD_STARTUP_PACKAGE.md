# WireGuard Startup Package

## Purpose
This document describes the current orchestrator-side preparation work for gateway startup artifacts.

The goal is to let the orchestrator generate a per-gateway directory structure ahead of RPi boot, so that WireGuard and gateway-agent files can be placed on the device later as part of provisioning.

## Current Scope
At the current stage, the orchestrator is responsible for preparing gateway startup artifacts, not for executing them on the RPi.

This means the orchestrator now handles:
- creating the per-gateway directory structure
- generating a fresh WireGuard key pair for each gateway
- assigning a client VPN address for each gateway
- generating a client `wg0.conf`

This does not yet include:
- running `wg-quick up wg0` on the RPi
- generating the gateway-agent `docker-compose.yml`
- generating the gateway-agent `.env`
- copying files onto the SD card
- verifying connectivity from the RPi

## Directory Layout
When a host is provisioned through the orchestrator, the code now creates two dedicated subdirectories inside the existing node directory:

~~~text
NodeName_<node_name>/
  config.txt
  wireguard/
  gateway-agent/
~~~

This change extends the existing `NodeName_<node_name>` host directory instead of introducing a completely separate artifact root.

## Why This Structure
- `config.txt` remains the simple node metadata file.
- `wireguard/` is reserved for WireGuard client startup files.
- `gateway-agent/` is reserved for Docker runtime files for the gateway agent.

This keeps VPN-related files and gateway runtime files separated while preserving the existing provisioning flow.

## Files Created So Far
The following files are currently created during host provisioning:

### `wireguard/`
- `wg0.conf`
- `privatekey`
- `publickey`

The following files are planned for the next step:

### `gateway-agent/`
- `docker-compose.yml`
- `.env`

## Implementation Flow
The current implementation flows through these files:

### `orchestrator/ui/setup.py`
This file stores the WireGuard startup package defaults used by the orchestrator when it generates a gateway package.

Current WireGuard defaults include:
- `wg_interface`
- `wg_server_public_key`
- `wg_server_endpoint`
- `wg_allowed_ips`
- `wg_persistent_keepalive`
- `wg_client_address_prefix`
- `wg_client_address_mask`

These are not the final output files themselves. They are the source settings used to render each gateway's `wg0.conf`.

### `orchestrator/ui/gateway_package.py`
This file contains the provisioning logic for WireGuard package generation.

It currently handles:
- locating the gateway node directory
- locating the `wireguard/` subdirectory
- allocating a client VPN address
- generating a fresh private/public key pair
- rendering the `wg0.conf` contents
- writing `privatekey`, `publickey`, and `wg0.conf`

### `orchestrator/ui/services.py`
The existing host provisioning flow now calls the WireGuard package generator during `initialize_provision_host(...)`.

That means a successful host provisioning operation now performs both:
- oneM2M host resource creation
- local startup artifact generation for the new gateway node

## Responsibility Split
The orchestrator side is responsible for generating and storing the startup package artifacts.

The RPi side is responsible for:
- booting with those files available
- running `sudo wg-quick up wg0`
- verifying connectivity with commands such as `wg show`, `ping`, and `curl`
- starting the gateway agent after the VPN is up

## Current `wg0.conf` Inputs
The generated client `wg0.conf` currently uses:

- `PrivateKey`: generated per gateway
- `Address`: generated per gateway
- `PublicKey`: orchestrator / VPN server public key
- `AllowedIPs`: shared default from orchestrator settings
- `Endpoint`: shared default from orchestrator settings
- `PersistentKeepalive`: shared default from orchestrator settings

The interface name itself is currently represented by the target filename `wg0.conf` and by the configured default `wg_interface = "wg0"`.

## Key Generation Rule
Each newly provisioned gateway must receive its own unique WireGuard key pair.

This means:
- the private key is generated again for each newly registered gateway
- the public key is generated from that private key
- key pairs are not shared between RPis
- client VPN addresses must also be unique per gateway

This matches the expected provisioning rule for new RPi registrations.

## Files Updated So Far
The current directory creation and WireGuard artifact generation logic was updated in:

- `orchestrator/ui/setup.py`
- `orchestrator/ui/gateway_package.py`
- `orchestrator/ui/services.py`

## New File Added

### `orchestrator/ui/gateway_package.py`
This file did not exist before. It was added to keep the WireGuard startup package generation logic separate from the existing oneM2M service flow.

The following new functions were added in this file:

#### `get_gateway_node_dir(node_name)`
Returns the base gateway directory:

~~~text
NodeName_<node_name>/
~~~

#### `get_wireguard_dir(node_name)`
Returns the WireGuard subdirectory:

~~~text
NodeName_<node_name>/wireguard/
~~~

#### `allocate_gateway_vpn_address(node_name)`
Builds a client VPN address for the gateway.

This is used to generate the `Address = ...` line in `wg0.conf`.

#### `generate_wireguard_keypair()`
Generates a fresh WireGuard private/public key pair using the local `wg` CLI.

This is the part that enforces the rule that every newly provisioned RPi must receive a new key pair.

#### `render_wg0_conf(private_key, address)`
Builds the client-side `wg0.conf` text using:
- the per-gateway private key
- the per-gateway VPN address
- the shared orchestrator-side defaults from `setup.py`

#### `provision_wireguard_package(node_name)`
Writes the actual WireGuard artifact files into:

~~~text
NodeName_<node_name>/wireguard/
  privatekey
  publickey
  wg0.conf
~~~

This is the main function that ties the WireGuard package generation flow together.

## Existing Files Modified

### `orchestrator/ui/setup.py`
This file already existed. It was updated by adding shared WireGuard startup defaults.

The following variables were added:
- `wg_interface`
- `wg_server_public_key`
- `wg_server_endpoint`
- `wg_allowed_ips`
- `wg_persistent_keepalive`
- `wg_client_address_prefix`
- `wg_client_address_mask`

These are used as shared input values when rendering each gateway's `wg0.conf`.

In other words:
- this file does not generate the config directly
- it stores the common values used by the generator

Code added in this file:
- shared WireGuard defaults for interface name
- shared WireGuard defaults for server public key and endpoint
- shared WireGuard defaults for allowed IPs and keepalive
- shared WireGuard defaults for client address prefix and mask

### `orchestrator/ui/services.py`
This file already existed. It was updated inside the existing `initialize_provision_host(...)` flow.

The following logic was added there:
- create `wireguard/` subdirectory
- create `gateway-agent/` subdirectory
- call `provision_wireguard_package(node_rn)`

This means that when a new host node is provisioned, the orchestrator now does more than just create oneM2M node resources. It also creates the local WireGuard startup artifacts for that gateway.

Code added in this file:
- directory creation for `NodeName_<node_name>/wireguard/`
- directory creation for `NodeName_<node_name>/gateway-agent/`
- call into the new WireGuard package generator during host provisioning

### `docs/WIREGUARD_STARTUP_PACKAGE.md`
This documentation file was added to explain the current implementation status.

It exists to make the following clear:
- which files were newly added
- which existing files were modified
- what code was added in each place
- what is already implemented versus what is still pending

## Example Output
An example generated gateway directory currently looks like this:

~~~text
NodeName_gw-node-01/
  config.txt
  wireguard/
    privatekey
    publickey
    wg0.conf
  gateway-agent/
~~~

This means the host provisioning flow now creates:
- `NodeName_<node_name>/wireguard/`
- `NodeName_<node_name>/gateway-agent/`
- `NodeName_<node_name>/wireguard/privatekey`
- `NodeName_<node_name>/wireguard/publickey`
- `NodeName_<node_name>/wireguard/wg0.conf`

## Current Status
The current implementation now does the following during host provisioning:

- creates the `wireguard/` and `gateway-agent/` directories
- generates a fresh WireGuard private/public key pair for the gateway
- allocates a gateway VPN address
- writes `wireguard/wg0.conf`
- writes `wireguard/privatekey`
- writes `wireguard/publickey`

The key generation is intended to happen again for each newly registered gateway, so each RPi receives its own unique key pair and client address.

It does not yet:
- generate `docker-compose.yml`
- generate `.env`
- execute anything on the RPi
