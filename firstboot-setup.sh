#!/usr/bin/env bash
#
# Wire into cloud-init runcmd to make zero-touch:
#   - sh -c 'BOOT=/boot/firmware; cp $BOOT/firstboot-setup.sh /tmp/;
#            cp $BOOT/wg0.conf /tmp/; cp $BOOT/.env.rpi1 /tmp/ 2>/dev/null;
#            cp $BOOT/.env.rpi2 /tmp/ 2>/dev/null; cp $BOOT/docker-compose.yml /tmp/;
#            chmod +x /tmp/firstboot-setup.sh;
#            bash /tmp/firstboot-setup.sh --install'
# ==============================================================

# ---------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------
LAPTOP_REGISTRY="10.0.0.1:5000"
GATEWAY_INSTALL_DIR="/opt/gateway"
GATEWAY_CSE_DATA_DIR="/opt/gateway/cse-data"
WG_INTERFACE="wg0"
WG_CONF_DST="/etc/wireguard/${WG_INTERFACE}.conf"

# Source files: prefer /tmp/ (cloud-init runcmd copies them there), fall back to /boot/firmware/.
pick_src() {
    local name="$1"
    if [ -f "/tmp/$name" ]; then echo "/tmp/$name"
    elif [ -f "/boot/firmware/$name" ]; then echo "/boot/firmware/$name"
    elif [ -f "/boot/$name" ]; then echo "/boot/$name"
    else echo ""; fi
}

LOG_FILE="/var/log/pi-startup.log"
SCRIPT_PATH="/usr/local/sbin/firstboot-setup.sh"


case "$(hostname)" in
    mn1)  GATEWAY_SERVICE="gateway-app1"; GATEWAY_ENV_FILE=".env.rpi1" ;;
    mn2)  GATEWAY_SERVICE="gateway-app2"; GATEWAY_ENV_FILE=".env.rpi2" ;;
    mn*)  echo "[startup] WARNING: hostname $(hostname) not in known list, defaulting to gateway-app1" >&2
          GATEWAY_SERVICE="gateway-app1"; GATEWAY_ENV_FILE=".env.rpi1" ;;
    *)    GATEWAY_SERVICE="gateway-app1"; GATEWAY_ENV_FILE=".env.rpi1" ;;
esac

# ---------------------------------------------------------------
# INSTALL MODE
# Sets up the systemd service and enables it. Run once via SSH or
# cloud-init runcmd after imaging the Pi.
# ---------------------------------------------------------------
if [ "${1:-}" = "--install" ]; then
    echo "[install] Copying script to $SCRIPT_PATH"
    sudo cp "$0" "$SCRIPT_PATH"
    sudo chmod +x "$SCRIPT_PATH"

    echo "[install] Writing firstboot-setup.service"
    sudo tee /etc/systemd/system/firstboot-setup.service >/dev/null <<'SERVICE'
[Unit]
Description=Pi gateway first-boot setup (packages, WG, docker compose up)
Wants=network-online.target docker.service
After=network-online.target docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/firstboot-setup.sh
TimeoutStartSec=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

    sudo systemctl daemon-reload
    sudo systemctl enable firstboot-setup.service


    if systemctl list-unit-files 2>/dev/null | grep -q '^gateway-bootstrap\.service'; then
        echo "[install] Removing legacy gateway-bootstrap.service"
        sudo systemctl disable gateway-bootstrap.service 2>/dev/null || true
        sudo rm -f /etc/systemd/system/gateway-bootstrap.service
        sudo systemctl daemon-reload
    fi

    echo "[install] Done. Service enabled. Run now via:"
    echo "  sudo systemctl start firstboot-setup.service"
    echo "  sudo journalctl -u firstboot-setup.service -f"
    exit 0
fi

# ---------------------------------------------------------------
# MAIN — runs every boot as firstboot-setup.service
# Idempotent: presence checks on each step.
# ---------------------------------------------------------------
exec > >(tee -a "$LOG_FILE") 2>&1
echo "[startup] ===== $(date) ====="
echo "[startup] hostname=$(hostname) service=$GATEWAY_SERVICE"

# --- wait for internet (needed for apt + image pull) ---
echo "[startup] Waiting for internet..."
CONNECTED=0
for n in $(seq 1 180); do
    if curl -fsS --max-time 5 https://github.com >/dev/null 2>&1; then
        echo "[startup] Internet OK (attempt $n)"
        CONNECTED=1
        break
    fi
    sleep 2
done
if [ "$CONNECTED" -eq 0 ]; then
    echo "[startup] ERROR: No internet after 6 minutes — aborting."
    exit 1
fi


echo "[startup] Ensuring system clock is synced..."
timedatectl set-ntp true 2>/dev/null || true
for n in $(seq 1 30); do
    if timedatectl status 2>/dev/null | grep -q "System clock synchronized: yes"; then
        echo "[startup] Clock synced (attempt $n)"
        break
    fi
    sleep 1
done

# --- install system packages (first time only) ---
need_install=0
command -v docker >/dev/null 2>&1 || need_install=1
command -v wg >/dev/null 2>&1 || need_install=1
command -v wg-quick >/dev/null 2>&1 || need_install=1
docker compose version >/dev/null 2>&1 || need_install=1

if [ "$need_install" -eq 1 ]; then
    echo "[startup] Installing system packages..."
    # apt repos: docker-compose-plugin isn't in Debian/RPi OS default repos,
    # so install docker.io + wireguard-tools from apt and pull the compose
    # plugin binary from GitHub.
    apt-get update -y
    apt-get install -y curl ca-certificates docker.io wireguard-tools

    # Install Docker Compose v2 as a CLI plugin (binary, arch-aware)
    if ! docker compose version >/dev/null 2>&1; then
        echo "[startup] Installing docker compose plugin (binary)..."
        ARCH=$(dpkg --print-architecture)
        case "$ARCH" in
            arm64)  COMPOSE_ARCH=aarch64 ;;
            armhf)  COMPOSE_ARCH=armv7   ;;
            amd64)  COMPOSE_ARCH=x86_64  ;;
            *)      COMPOSE_ARCH="$ARCH" ;;
        esac
        mkdir -p /usr/libexec/docker/cli-plugins
        curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-${COMPOSE_ARCH}" \
            -o /usr/libexec/docker/cli-plugins/docker-compose
        chmod +x /usr/libexec/docker/cli-plugins/docker-compose
        echo "[startup] docker compose plugin installed: $(docker compose version 2>&1 | head -1)"
    fi

    echo "[startup] System packages installed."
else
    echo "[startup] System packages already installed — skipping."
fi

# --- trust laptop's insecure private registry (HTTP on the VPN) ---
DOCKER_DAEMON_CFG="/etc/docker/daemon.json"
DESIRED='{"insecure-registries":["'"$LAPTOP_REGISTRY"'"]}'
if [ ! -f "$DOCKER_DAEMON_CFG" ] || ! grep -q "$LAPTOP_REGISTRY" "$DOCKER_DAEMON_CFG"; then
    echo "[startup] Writing $DOCKER_DAEMON_CFG with insecure registry $LAPTOP_REGISTRY..."
    mkdir -p "$(dirname "$DOCKER_DAEMON_CFG")"
    echo "$DESIRED" > "$DOCKER_DAEMON_CFG"
    systemctl restart docker
    echo "[startup] Docker restarted with insecure registry config."
else
    echo "[startup] Docker daemon.json already trusts $LAPTOP_REGISTRY — skipping."
fi

# --- WireGuard: install orchestrator-generated wg0.conf and bring up tunnel ---
WG_CONF_SRC=$(pick_src "wg0.conf")
if [ ! -f "$WG_CONF_DST" ]; then
    if [ -z "$WG_CONF_SRC" ]; then
        echo "[startup] ERROR: wg0.conf not found in /tmp/, /boot/firmware/, or /boot/."
        echo "[startup] The orchestrator (Django) must generate it via /api/provision/host/"
        echo "[startup] and you must stage it on the SD card before flashing."
        exit 1
    fi
    echo "[startup] Installing wg0.conf from $WG_CONF_SRC"
    mkdir -p "$(dirname "$WG_CONF_DST")"
    cp "$WG_CONF_SRC" "$WG_CONF_DST"
    chmod 600 "$WG_CONF_DST"
else
    echo "[startup] $WG_CONF_DST already exists — skipping copy."
fi

if ip link show "$WG_INTERFACE" >/dev/null 2>&1; then
    echo "[startup] WireGuard interface $WG_INTERFACE already up."
else
    echo "[startup] Bringing up WireGuard tunnel..."
    if wg-quick up "$WG_INTERFACE"; then
        echo "[startup] WireGuard tunnel established."
    else
        echo "[startup] WARNING: wg-quick up $WG_INTERFACE failed."
    fi
fi


systemctl enable "wg-quick@${WG_INTERFACE}" 2>/dev/null || true

# --- gateway compose stack: stage env + compose, run compose up ---
mkdir -p "$GATEWAY_INSTALL_DIR" "$GATEWAY_CSE_DATA_DIR"

# Stage whichever .env.rpi* files were placed on the SD (only the relevant
# one needs to exist for the chosen service).
for envfile in .env.rpi1 .env.rpi2; do
    src=$(pick_src "$envfile")
    if [ -n "$src" ]; then
        cp "$src" "$GATEWAY_INSTALL_DIR/$envfile"
        chmod 600 "$GATEWAY_INSTALL_DIR/$envfile"
        echo "[startup] Installed $envfile to $GATEWAY_INSTALL_DIR"
    fi
done

ENV_FILE_PATH="$GATEWAY_INSTALL_DIR/$GATEWAY_ENV_FILE"
if [ -f "$ENV_FILE_PATH" ]; then
    IMAGE_REF=$(grep '^IMAGE=' "$ENV_FILE_PATH" | cut -d= -f2- | tr -d '\r\n ')
    echo "[startup] Starting $GATEWAY_SERVICE from $IMAGE_REF (env: $GATEWAY_ENV_FILE)"

    docker network create acme-net 2>/dev/null || true

    docker rm -f "$GATEWAY_SERVICE" 2>/dev/null || true
    docker pull "$IMAGE_REF" || echo "[startup] WARNING: docker pull failed; falling back to cached image."

    docker run -d \
        --name "$GATEWAY_SERVICE" \
        --network acme-net \
        --env-file "$ENV_FILE_PATH" \
        -p 9000:9000 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$GATEWAY_CSE_DATA_DIR":/shared-cse \
        --restart unless-stopped \
        "$IMAGE_REF"

    docker ps --filter "name=$GATEWAY_SERVICE"
else
    echo "[startup] WARNING: $ENV_FILE_PATH missing — not starting gateway."
fi

echo "[startup] ===== $(date) — done ====="
