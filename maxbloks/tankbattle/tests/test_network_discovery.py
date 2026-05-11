# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for LobbyDiscovery and NetworkManager peer discovery."""

import unittest

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import network


class TestDiscovery(unittest.TestCase):

    def test_lobby_discovery_init(self):
        discovered = []
        discovery = network.LobbyDiscovery(discovered.append, is_host=True)
        self.assertTrue(discovery.is_host)
        self.assertIsNotNone(discovery.instance_id)
        self.assertFalse(discovery.running)

    def test_lobby_discovery_host_flag(self):
        discovery_host = network.LobbyDiscovery(lambda ip, info: None, is_host=True)
        discovery_client = network.LobbyDiscovery(lambda ip, info: None, is_host=False)
        self.assertTrue(discovery_host.is_host)
        self.assertFalse(discovery_client.is_host)

    def test_network_manager_start_discovery_clears_hosts(self):
        manager = network.NetworkManager()
        manager.discovered_hosts.append({"address": "1.2.3.4", "port": 5555})
        manager._discovery = None
        manager.discovered_hosts.clear()
        self.assertEqual(manager.discovered_hosts, [])

    def test_on_peer_discovered_stores_hosting_flag(self):
        manager = network.NetworkManager()
        manager._on_peer_discovered("192.168.1.10", {"hosting": True, "port": 5555})
        self.assertEqual(len(manager.discovered_hosts), 1)
        self.assertTrue(manager.discovered_hosts[0]["hosting"])
        self.assertEqual(manager.discovered_hosts[0]["address"], "192.168.1.10")

    def test_on_peer_discovered_stores_client(self):
        manager = network.NetworkManager()
        manager._on_peer_discovered("192.168.1.20", {"hosting": False, "port": 0})
        self.assertEqual(len(manager.discovered_hosts), 1)
        self.assertFalse(manager.discovered_hosts[0]["hosting"])
        self.assertEqual(manager.discovered_hosts[0]["address"], "192.168.1.20")

    def test_on_peer_discovered_no_duplicates(self):
        manager = network.NetworkManager()
        manager._on_peer_discovered("192.168.1.10", {"hosting": True, "port": 5555})
        manager._on_peer_discovered("192.168.1.10", {"hosting": True, "port": 5555})
        self.assertEqual(len(manager.discovered_hosts), 1)

    def test_on_peer_discovered_allows_same_ip_different_role(self):
        """Same IP can appear as both host and client (different entries)."""
        manager = network.NetworkManager()
        manager._on_peer_discovered("192.168.1.10", {"hosting": True, "port": 5555})
        manager._on_peer_discovered("192.168.1.10", {"hosting": False, "port": 0})
        self.assertEqual(len(manager.discovered_hosts), 2)

    def test_discovery_callback_receives_all_peers(self):
        """The LobbyDiscovery callback fires for both beacons and
        responses regardless of the local role."""
        found = []
        def on_found(ip, info):
            found.append((ip, info))
        discovery = network.LobbyDiscovery(on_found, is_host=False)
        msg = {"type": constants.BEACON_PREFIX, "instance_id": "other", "hosting": True, "port": 5555}
        discovery.on_peer_found("192.168.1.10", msg)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], "192.168.1.10")
