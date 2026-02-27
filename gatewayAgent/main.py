# Import the setup variables
from setup import *

# Import AE functions
from ae import register_AE, unregister_AE
from container import create_container

# Import subscription function
from subscription import create_subscription
from contentInstance import retrieve_contentinstance, delete_contentinstance

# Import notification function
from notificationReceiver import run_notification_receiver, stop_notification_receiver

import atexit
import time

from init import start_CSE, update_config


POLL_INTERVAL_SEC = 2


def parse_cse_name_from_data(content: str) -> str:
    """Accept plain value or key=value lines and return cseName."""
    if not isinstance(content, str):
        return "acme-mn1"

    value = content.strip()
    if not value:
        return "acme-mn1"

    fields = {}
    for line in value.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, parsed = line.split("=", 1)
        fields[key.strip()] = parsed.strip()

    if fields.get("cseName"):
        return fields["cseName"]

    return value


def apply_execute_command() -> None:
    try:
        data_cin = retrieve_contentinstance(originator, application_path + "/data/la")
    except Exception as e:
        print("Failed to retrieve latest data contentInstance:", e)
        return

    if not data_cin or "con" not in data_cin:
        print("No usable data contentInstance found; skipping execute")
        return

    cse_name = parse_cse_name_from_data(data_cin.get("con", ""))
    print(f"Applying execute using cseName='{cse_name}'")

    try:
        update_config("acme_mn1/acme.ini", cse_name)
    except Exception as e:
        print("Failed to update config:", e)
        return

    if not start_CSE("acme-mn1"):
        print("Docker start failed")


def main() -> int:
    run_notification_receiver()

    if not register_AE(originator, application_name):
        stop_notification_receiver()
        return 1

    if not create_container(originator, application_path, "cmd"):
        stop_notification_receiver()
        return 1

    if not create_container(originator, application_path, "data"):
        stop_notification_receiver()
        return 1

    if not create_subscription(originator, application_path + "/cmd", subscription_name, notificationURIs):
        unregister_AE(originator, application_name)
        stop_notification_receiver()
        return 1

    atexit.register(lambda: unregister_AE(originator, application_name))
    atexit.register(lambda: stop_notification_receiver())

    # Only process commands that arrive after this process starts.
    baseline_cmd_ct = None
    processed_cmd_rns = set()
    try:
        existing_cmd = retrieve_contentinstance(originator, application_path + "/cmd/la")
        if existing_cmd:
            baseline_cmd_ct = existing_cmd.get("ct")
    except Exception:
        # If there is no existing cmd/la (or retrieval fails), just wait for the first new one.
        pass

    print("Gateway is ready. Waiting for new Orchestrator command in gatewayAgent/cmd ...")
    try:
        while True:
            try:
                cmd_cin = retrieve_contentinstance(originator, application_path + "/cmd/la")
            except Exception as e:
                print("Failed to retrieve latest cmd contentInstance:", e)
                time.sleep(POLL_INTERVAL_SEC)
                continue

            if not cmd_cin:
                time.sleep(POLL_INTERVAL_SEC)
                continue

            cmd_rn = cmd_cin.get("rn")
            cmd_con = cmd_cin.get("con")
            cmd_ct = cmd_cin.get("ct")

            if not cmd_rn or not cmd_ct:
                time.sleep(POLL_INTERVAL_SEC)
                continue

            if cmd_rn in processed_cmd_rns:
                time.sleep(POLL_INTERVAL_SEC)
                continue

            if baseline_cmd_ct is not None and cmd_ct <= baseline_cmd_ct:
                processed_cmd_rns.add(cmd_rn)
                time.sleep(POLL_INTERVAL_SEC)
                continue

            if cmd_con != "execute":
                print(f"Ignoring unsupported cmd content: {cmd_con!r}")
                processed_cmd_rns.add(cmd_rn)
                time.sleep(POLL_INTERVAL_SEC)
                continue

            print(f"Received execute command (rn={cmd_rn})")
            processed_cmd_rns.add(cmd_rn)
            apply_execute_command()

            cmd_url = application_path + "/cmd/" + cmd_rn
            if delete_contentinstance(cmd_url) is False:
                print("Failed to delete processed cmd contentInstance")

            time.sleep(POLL_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("Gateway stopped by user")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
