# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import unittest

from maxbloks.tankbattle import constants
from maxbloks.tankbattle.network import manager as _manager

NetworkManager = _manager.NetworkManager


class TestNetworkManager(unittest.TestCase):

    def setUp(self):
        self.nm = NetworkManager()

    def tearDown(self):
        self.nm.close()

    # --- Initial state ---

    def test_initial_role_is_none(self):
        self.assertIsNone(self.nm.role)

    def test_initial_connected_is_false(self):
        self.assertFalse(self.nm.connected)

    def test_initial_discovered_hosts_is_empty(self):
        self.assertEqual(self.nm.discovered_hosts, [])

    def test_initial_tcp_socket_is_none(self):
        self.assertIsNone(self.nm.tcp_socket)

    def test_initial_udp_socket_is_none(self):
        self.assertIsNone(self.nm.udp_socket)

    def test_monitor_is_created(self):
        self.assertIsNotNone(self.nm.monitor)

    # --- _get_local_ip ---

    def test_local_ip_is_string(self):
        self.assertIsInstance(self.nm.local_ip, str)

    def test_local_ip_has_dots(self):
        self.assertIn('.', self.nm.local_ip)

    # --- make_handshake / parse_handshake ---

    def test_make_handshake_returns_bytes(self):
        data = self.nm.make_handshake("1.0", 1)
        self.assertIsInstance(data, bytes)

    def test_make_handshake_contains_prefix(self):
        data = self.nm.make_handshake("1.0", 1)
        payload = json.loads(data)
        self.assertEqual(payload["prefix"], constants.HANDSHAKE_PREFIX)

    def test_make_handshake_contains_player_id(self):
        data = self.nm.make_handshake("1.0", 2)
        payload = json.loads(data)
        self.assertEqual(payload["player_id"], 2)

    def test_make_handshake_contains_protocol_version(self):
        data = self.nm.make_handshake("1.0", 1)
        payload = json.loads(data)
        self.assertEqual(payload["protocol"], constants.PROTOCOL_VERSION)

    def test_parse_handshake_valid(self):
        data = self.nm.make_handshake("1.0", 1)
        result = self.nm.parse_handshake(data)
        self.assertEqual(result["player_id"], 1)

    def test_parse_handshake_wrong_prefix_raises(self):
        bad = json.dumps({
            "prefix": "WRONG",
            "version": "1.0",
            "player_id": 1,
            "protocol": constants.PROTOCOL_VERSION,
        }).encode()
        with self.assertRaises(ValueError):
            self.nm.parse_handshake(bad)

    def test_parse_handshake_wrong_protocol_raises(self):
        bad = json.dumps({
            "prefix": constants.HANDSHAKE_PREFIX,
            "version": "1.0",
            "player_id": 1,
            "protocol": 9999,
        }).encode()
        with self.assertRaises(ValueError):
            self.nm.parse_handshake(bad)

    # --- should_send_update ---

    def test_should_send_update_true_after_interval(self):
        now = constants.NETWORK_UPDATE_INTERVAL
        self.assertTrue(self.nm.should_send_update(now))

    def test_should_send_update_false_before_interval(self):
        now = constants.NETWORK_UPDATE_INTERVAL
        self.nm.should_send_update(now)  # consume the slot
        self.assertFalse(self.nm.should_send_update(now))

    def test_should_send_update_true_again_after_second_interval(self):
        first = constants.NETWORK_UPDATE_INTERVAL
        self.nm.should_send_update(first)
        second = first + constants.NETWORK_UPDATE_INTERVAL
        self.assertTrue(self.nm.should_send_update(second))

    # --- _on_peer_discovered ---

    def test_on_peer_discovered_adds_host(self):
        self.nm._on_peer_discovered("10.0.0.1", {"hosting": True, "port": 5555})
        self.assertEqual(len(self.nm.discovered_hosts), 1)

    def test_on_peer_discovered_no_duplicate_same_role(self):
        self.nm._on_peer_discovered("10.0.0.1", {"hosting": True, "port": 5555})
        self.nm._on_peer_discovered("10.0.0.1", {"hosting": True, "port": 5555})
        self.assertEqual(len(self.nm.discovered_hosts), 1)

    def test_on_peer_discovered_allows_different_roles(self):
        self.nm._on_peer_discovered("10.0.0.1", {"hosting": True, "port": 5555})
        self.nm._on_peer_discovered("10.0.0.1", {"hosting": False, "port": 0})
        self.assertEqual(len(self.nm.discovered_hosts), 2)

    def test_on_peer_discovered_stores_address(self):
        self.nm._on_peer_discovered("10.0.0.2", {"hosting": True, "port": 5555})
        self.assertEqual(self.nm.discovered_hosts[0]["address"], "10.0.0.2")

    # --- close / stop_discovery ---

    def test_close_with_no_sockets_does_not_raise(self):
        nm = NetworkManager()
        nm.close()

    def test_stop_discovery_when_none_does_not_raise(self):
        self.nm.stop_discovery()

    # --- start_host ---

    def test_start_host_sets_role(self):
        self.nm.start_host(port=0)
        self.assertEqual(self.nm.role, "host")

    def test_start_host_creates_tcp_socket(self):
        self.nm.start_host(port=0)
        self.assertIsNotNone(self.nm.tcp_socket)

    def test_start_host_creates_udp_socket(self):
        self.nm.start_host(port=0)
        self.assertIsNotNone(self.nm.udp_socket)

    # --- send_ping_if_due ---

    def test_send_ping_when_not_connected_does_not_raise(self):
        self.nm.connected = False
        self.nm.send_ping_if_due(now=100.0)

    def test_send_ping_when_no_remote_address_does_not_raise(self):
        self.nm.connected = True
        self.nm.remote_address = None
        self.nm.send_ping_if_due(now=100.0)

    # --- process_tcp_messages ---

    def test_process_tcp_messages_no_socket_returns_empty(self):
        events = self.nm.process_tcp_messages()
        self.assertEqual(events, [])

    # --- _send_welcome ---

    def test_send_welcome_with_no_socket_does_not_raise(self):
        self.nm.role = "host"
        self.nm._send_welcome()

    # --- send_reliable_event ---

    def test_send_reliable_event_no_socket_returns_false(self):
        self.nm.role = "host"
        result = self.nm.send_reliable_event("match_start")
        self.assertFalse(result)

    def test_send_reliable_event_host_no_client_returns_false(self):
        self.nm.start_host(port=0)
        result = self.nm.send_reliable_event("match_start")
        self.assertFalse(result)

    def test_send_reliable_event_client_with_socket_returns_true(self):
        """Start a host and connect a client, then send a reliable event."""
        host = NetworkManager()
        host.start_host(port=0)
        # Get the actual port the host bound to
        host_port = host.tcp_socket.getsockname()[1]
        self.nm.role = "client"
        self.nm.connect_to_host("127.0.0.1", host_port)
        result = self.nm.send_reliable_event("match_start", {"seed": 42})
        self.assertTrue(result)
        host.close()
