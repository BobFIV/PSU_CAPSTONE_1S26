import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional


import requests

from setup import (
    orchestrator_base_url,
    wireguard_config_dir,
    wireguard_default_interface,
    wireguard_key_dir,
    wireguard_peer_report_path,
    wireguard_skip_interface_up,
)


def _run_command(cmd: list[str], check: bool = True, input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
        input=input_text,
    )


def _binary_exists(name: str) -> bool:
    return shutil.which(name) is not None


def install_wireguard() -> None:
    if _binary_exists("wg") and _binary_exists("wg-quick"):
        return

    if not _binary_exists("apt-get"):
        raise RuntimeError("WireGuard is not installed and apt-get is unavailable")

    _run_command(["apt-get", "update"])
    _run_command(["apt-get", "install", "-y", "wireguard", "wireguard-tools"])


def ensure_keypair(interface: str = wireguard_default_interface) -> tuple[str, str]:
    key_dir = Path(wireguard_key_dir)
    key_dir.mkdir(parents=True, exist_ok=True)
    private_key_path = key_dir / f"{interface}.key"
    public_key_path = key_dir / f"{interface}.pub"

    if private_key_path.exists() and public_key_path.exists():
        return (
            private_key_path.read_text().strip(),
            public_key_path.read_text().strip(),
        )

    private_key = _run_command(["wg", "genkey"]).stdout.strip()
    public_key = _run_command(["wg", "pubkey"], input_text=private_key).stdout.strip()

    private_key_path.write_text(private_key + "\n")
    public_key_path.write_text(public_key + "\n")
    os.chmod(private_key_path, 0o600)
    os.chmod(public_key_path, 0o644)
    return private_key, public_key


def build_config(payload: dict, private_key: str) -> str:
    interface = payload.get("wgInterface", wireguard_default_interface)
    address = payload.get("wgAddress", "").strip()
    peer_public_key = payload.get("wgServerPublicKey", "").strip()
    endpoint = payload.get("wgEndpoint", "").strip()
    allowed_ips = payload.get("wgAllowedIPs", "").strip() or "0.0.0.0/0"
    keepalive = payload.get("wgPersistentKeepalive", "").strip() or "25"
    listen_port = payload.get("wgListenPort", "").strip()

    if not address or not peer_public_key or not endpoint:
        raise ValueError("wgAddress, wgServerPublicKey, and wgEndpoint are required")

    lines = [
        "[Interface]",
        f"PrivateKey = {private_key}",
        f"Address = {address}",
    ]
    if listen_port:
        lines.append(f"ListenPort = {listen_port}")

    lines.extend(
        [
            "",
            "[Peer]",
            f"PublicKey = {peer_public_key}",
            f"AllowedIPs = {allowed_ips}",
            f"Endpoint = {endpoint}",
            f"PersistentKeepalive = {keepalive}",
            "",
        ]
    )
    return "\n".join(lines), interface


def write_config(interface: str, config_text: str) -> Path:
    config_dir = Path(wireguard_config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f"{interface}.conf"
    config_path.write_text(config_text)
    os.chmod(config_path, 0o600)
    return config_path


def bring_up_interface(interface: str) -> None:
    _run_command(["wg-quick", "down", interface], check=False)
    _run_command(["wg-quick", "up", interface])


def enable_on_boot(interface: str) -> None:
    if not _binary_exists("systemctl"):
        print(f"Skipping persistent enable for {interface}: systemctl is unavailable on this host")
        return
    _run_command(["systemctl", "enable", f"wg-quick@{interface}"])
    status = _run_command(["systemctl", "is-enabled", f"wg-quick@{interface}"])
    print(f"Persistent startup for {interface}: {status.stdout.strip()}")


def report_public_key(peer_name: str, public_key: str, metadata: Optional[dict] = None) -> None:
    url = orchestrator_base_url.rstrip("/") + wireguard_peer_report_path
    response = requests.post(
        url,
        json={
            "peerName": peer_name,
            "publicKey": public_key,
            "metadata": metadata or {},
        },
        timeout=5,
    )
    response.raise_for_status()


def configure_wireguard(peer_name: str, payload: dict) -> str:
    install_wireguard()
    private_key, public_key = ensure_keypair(payload.get("wgInterface", wireguard_default_interface))
    config_text, interface = build_config(payload, private_key)
    write_config(interface, config_text)
    report_public_key(
        peer_name,
        public_key,
        {
            "interface": interface,
            "address": payload.get("wgAddress", ""),
            "endpoint": payload.get("wgEndpoint", ""),
            "config_path": str(Path(wireguard_config_dir) / f"{interface}.conf"),
            "interface_bringup_skipped": wireguard_skip_interface_up,
            "platform": platform.system(),
        },
    )
    if wireguard_skip_interface_up:
        print(f"Skipping wg-quick up for {interface} because WG_SKIP_INTERFACE_UP is enabled")
        return public_key

    bring_up_interface(interface)
    print(f"WireGuard interface {interface} brought up successfully")
    enable_on_boot(interface)
    return public_key
