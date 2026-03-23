import json
from datetime import datetime, timezone
from pathlib import Path


STATE_DIR = Path(__file__).resolve().parent / "data"
STATE_FILE = STATE_DIR / "wireguard_peers.json"
SERVER_CONFIG_FILE = STATE_DIR / "wireguard_server_peers.conf"


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"peers": {}}
    with STATE_FILE.open() as f:
        return json.load(f)


def _write_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


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
    return config_text


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
