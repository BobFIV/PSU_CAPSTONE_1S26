import re
import shutil
import subprocess
from pathlib import Path

from .setup import (
    wg_allowed_ips,
    wg_client_address_mask,
    wg_client_address_prefix,
    wg_interface,
    wg_persistent_keepalive,
    wg_server_endpoint,
    wg_server_public_key,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def get_gateway_node_dir(node_name: str) -> Path:
    return _project_root() / f"NodeName_{node_name}"


def get_wireguard_dir(node_name: str) -> Path:
    return get_gateway_node_dir(node_name) / "wireguard"


def allocate_gateway_vpn_address(node_name: str) -> str:
    matches = re.findall(r"(\d+)", node_name or "")
    if matches:
        host_octet = int(matches[-1]) + 1
    else:
        existing = sorted(_project_root().glob("NodeName_*"))
        host_octet = len(existing) + 2

    if host_octet < 2 or host_octet > 254:
        raise ValueError(f"Unable to allocate a valid WireGuard address for node '{node_name}'")

    return f"{wg_client_address_prefix}.{host_octet}/{wg_client_address_mask}"


def generate_wireguard_keypair() -> tuple[str, str]:
    if shutil.which("wg") is None:
        raise RuntimeError("WireGuard CLI 'wg' is required on the orchestrator host to generate key pairs")

    private_key = subprocess.run(
        ["wg", "genkey"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    public_key = subprocess.run(
        ["wg", "pubkey"],
        check=True,
        capture_output=True,
        text=True,
        input=private_key,
    ).stdout.strip()

    return private_key, public_key


def render_wg0_conf(private_key: str, address: str) -> str:
    lines = [
        "[Interface]",
        "# Private key for this gateway (keep secure)",
        f"PrivateKey = {private_key}",
        "",
        "# VPN IP assigned to this gateway",
        f"Address = {address}",
        "",
        "[Peer]",
        "# Public key of the orchestrator / VPN server",
        f"PublicKey = {wg_server_public_key}",
        "",
        "# Allowed traffic through the VPN",
        f"AllowedIPs = {wg_allowed_ips}",
        "",
        "# VPN server endpoint",
        f"Endpoint = {wg_server_endpoint}",
        "",
        "# Keep connection alive behind NAT",
        f"PersistentKeepalive = {wg_persistent_keepalive}",
        "",
    ]
    return "\n".join(lines)


def provision_wireguard_package(node_name: str) -> dict:
    wireguard_dir = get_wireguard_dir(node_name)
    wireguard_dir.mkdir(parents=True, exist_ok=True)

    private_key, public_key = generate_wireguard_keypair()
    address = allocate_gateway_vpn_address(node_name)
    config_text = render_wg0_conf(private_key, address)

    private_key_path = wireguard_dir / "privatekey"
    public_key_path = wireguard_dir / "publickey"
    config_path = wireguard_dir / "wg0.conf"

    private_key_path.write_text(private_key + "\n")
    public_key_path.write_text(public_key + "\n")
    config_path.write_text(config_text)

    return {
        "nodeName": node_name,
        "interface": wg_interface,
        "address": address,
        "privateKeyPath": str(private_key_path),
        "publicKeyPath": str(public_key_path),
        "configPath": str(config_path),
        "publicKey": public_key,
    }
