import json
from unittest.mock import patch

from django.test import Client, TestCase

from .wireguard_state import SERVER_CONFIG_FILE, STATE_FILE


class GatewayApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        if SERVER_CONFIG_FILE.exists():
            SERVER_CONFIG_FILE.unlink()

    @patch("ui.api_views.services.send_command_to_gateway", return_value=(True, 200, ""))
    @patch("ui.api_views.services.send_data_to_gateway", return_value=(True, 200, ""))
    def test_gateway_data_includes_wireguard_fields(self, send_data_mock, send_cmd_mock):
        response = self.client.post(
            "/api/gateway/data/",
            data=json.dumps(
                {
                    "vpnType": "wireguard",
                    "wgInterface": "wg0",
                    "wgAddress": "10.0.0.2/24",
                    "wgServerPublicKey": "server-public-key",
                    "wgEndpoint": "vpn.example.com:51820",
                    "wgAllowedIPs": "10.0.0.0/24",
                    "wgPersistentKeepalive": 25,
                    "cseName": "cse-mn1",
                    "cseID": "id-mn1",
                    "localPort": "8081",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        sent_payload = send_data_mock.call_args.args[0]
        self.assertIn("vpnType=wireguard", sent_payload)
        self.assertIn("wgInterface=wg0", sent_payload)
        self.assertIn("wgServerPublicKey=server-public-key", sent_payload)
        self.assertIn("cseName=cse-mn1", sent_payload)
        send_cmd_mock.assert_called_once_with("execute")

    def test_wireguard_peer_registry_round_trip(self):
        post_response = self.client.post(
            "/api/wireguard/peers/",
            data=json.dumps(
                {
                    "peerName": "gatewayAgent",
                    "publicKey": "pubkey123",
                    "metadata": {"interface": "wg0"},
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertTrue(STATE_FILE.exists())

        get_response = self.client.get("/api/wireguard/peers/")
        self.assertEqual(get_response.status_code, 200)
        peers = get_response.json()["peers"]
        self.assertEqual(peers["gatewayAgent"]["public_key"], "pubkey123")
        self.assertTrue(SERVER_CONFIG_FILE.exists())

    def test_wireguard_server_config_generation(self):
        self.client.post(
            "/api/wireguard/peers/",
            data=json.dumps(
                {
                    "peerName": "gatewayAgent",
                    "publicKey": "pubkey123",
                    "metadata": {
                        "address": "10.0.0.2/24",
                        "persistentKeepalive": 30,
                    },
                }
            ),
            content_type="application/json",
        )

        response = self.client.get("/api/wireguard/server-config/")
        self.assertEqual(response.status_code, 200)
        config_text = response.json()["config"]
        self.assertIn("[Peer]", config_text)
        self.assertIn("PublicKey = pubkey123", config_text)
        self.assertIn("AllowedIPs = 10.0.0.2/24", config_text)
        self.assertIn("PersistentKeepalive = 30", config_text)
