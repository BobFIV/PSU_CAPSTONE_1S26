import json
import os
from datetime import datetime, timezone
from pathlib import Path


STATE_DIR = Path(__file__).resolve().parent / "data"
STATE_FILE = STATE_DIR / "wireguard_peers.json"
SERVER_CONFIG_FILE = STATE_DIR / "wireguard_server_peers.conf"
SERVER_SETTINGS_FILE = STATE_DIR / "wireguard_server_settings.json"
SERVER_FULL_CONFIG_FILE = STATE_DIR / "wireguard_server_full.conf"


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"peers": {}}
    with STATE_FILE.open() as f:
        return json.load(f)


def _write_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def _load_server_settings() -> dict:
    defaults = {
        "interface": os.environ.get("WG_SERVER_INTERFACE", "wg0"),
        "address": os.environ.get("WG_SERVER_ADDRESS", "10.0.0.1/24"),
        "listen_port": os.environ.get("WG_SERVER_LISTEN_PORT", "51820"),
        "private_key": os.environ.get("WG_SERVER_PRIVATE_KEY", ""),
        "post_up": os.environ.get("WG_SERVER_POST_UP", ""),
        "post_down": os.environ.get("WG_SERVER_POST_DOWN", ""),
    }

    if not SERVER_SETTINGS_FILE.exists():
        return defaults

    with SERVER_SETTINGS_FILE.open() as f:
        stored = json.load(f)

    defaults.update(stored)
    return defaults


def _write_server_settings(settings: dict) -> dict:
    merged = _load_server_settings()
    merged.update({k: v for k, v in settings.items() if v is not None})
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with SERVER_SETTINGS_FILE.open("w") as f:
        json.dump(merged, f, indent=2, sort_keys=True)
    return merged


def _normalize_allowed_ips(peer_name: str, metadata: dict) -> str:
    allowed_ips = (metadata.get("serverAllowedIPs") or metadata.get("address") or "").strip()
    if not allowed_ips:
        return ""
    if "/" in allowed_ips:
        return allowed_ips
    return f"{allowed_ips}/32"


def _peer_block(peer_name: str, peer_record: dict) -> str:
    metadata = peer_record.get("metadata") or {}
    lines = [
        "[Peer]",
        f"# {peer_name}",
        f"PublicKey = {peer_record['public_key']}",
    ]

    allowed_ips = _normalize_allowed_ips(peer_name, metadata)
    if allowed_ips:
        lines.append(f"AllowedIPs = {allowed_ips}")

    keepalive = str(metadata.get("persistentKeepalive") or metadata.get("wgPersistentKeepalive") or "25").strip()
    if keepalive:
        lines.append(f"PersistentKeepalive = {keepalive}")

    return "\n".join(lines)


def generate_server_config_text() -> str:
    peers = list_peers()
    if not peers:
        return ""

    blocks = [_peer_block(peer_name, peer_record) for peer_name, peer_record in sorted(peers.items())]
    return "\n\n".join(blocks) + "\n"


def write_server_config() -> str:
    config_text = generate_server_config_text()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with SERVER_CONFIG_FILE.open("w") as f:
        f.write(config_text)
    write_full_server_config()
    return config_text


def generate_full_server_config_text() -> str:
    settings = _load_server_settings()
    lines = [
        "[Interface]",
        f"Address = {settings['address']}",
        f"ListenPort = {settings['listen_port']}",
    ]

    if settings.get("private_key"):
        lines.append(f"PrivateKey = {settings['private_key']}")
    if settings.get("post_up"):
        lines.append(f"PostUp = {settings['post_up']}")
    if settings.get("post_down"):
        lines.append(f"PostDown = {settings['post_down']}")

    peer_text = generate_server_config_text().strip()
    if peer_text:
        lines.extend(["", peer_text])

    return "\n".join(lines) + "\n"


def write_full_server_config() -> str:
    full_config_text = generate_full_server_config_text()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with SERVER_FULL_CONFIG_FILE.open("w") as f:
        f.write(full_config_text)
    return full_config_text


def save_peer(peer_name: str, public_key: str, metadata: dict | None = None) -> dict:
    state = _load_state()
    peers = state.setdefault("peers", {})
    peer_record = {
        "public_key": public_key,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
    }
    peers[peer_name] = peer_record
    _write_state(state)
    write_server_config()
    return peer_record


def list_peers() -> dict:
    return _load_state().get("peers", {})


def get_server_config() -> dict:
    config_text = generate_server_config_text()
    if not SERVER_CONFIG_FILE.exists():
        write_server_config()
    return {
        "config_text": config_text,
        "path": str(SERVER_CONFIG_FILE),
    }


def save_server_settings(settings: dict) -> dict:
    merged = _write_server_settings(settings)
    write_full_server_config()
    return merged


def get_server_settings() -> dict:
    settings = _load_server_settings()
    if not SERVER_SETTINGS_FILE.exists():
        _write_server_settings({})
    return settings


def get_full_server_config() -> dict:
    config_text = generate_full_server_config_text()
    if not SERVER_FULL_CONFIG_FILE.exists():
        write_full_server_config()
    return {
        "config_text": config_text,
        "path": str(SERVER_FULL_CONFIG_FILE),
    }
