# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import MagicMock
from maxbloks.networktest import network_discovery


class TestNetworkDiscovery(unittest.TestCase):

    def setUp(self):
        self.callback = MagicMock()
        self.discovery = network_discovery.NetworkDiscovery(
            on_device_discovered=self.callback
        )

    def tearDown(self):
        try:
            self.discovery.send_socket.close()
        except Exception:
            pass
        try:
            self.discovery.listen_socket.close()
        except Exception:
            pass

    def test_multicast_group(self):
        self.assertEqual(network_discovery.NetworkDiscovery.MULTICAST_GROUP, "239.255.190.19")

    def test_discovery_port(self):
        self.assertEqual(network_discovery.NetworkDiscovery.DISCOVERY_PORT, 19019)

    def test_broadcast_interval_positive(self):
        self.assertGreater(network_discovery.NetworkDiscovery.BROADCAST_INTERVAL, 0)

    def test_local_ip_not_empty(self):
        self.assertIsNotNone(self.discovery.local_ip)
        self.assertGreater(len(self.discovery.local_ip), 0)

    def test_instance_id_unique(self):
        callback2 = MagicMock()
        d2 = network_discovery.NetworkDiscovery(on_device_discovered=callback2)
        try:
            self.assertNotEqual(self.discovery.instance_id, d2.instance_id)
        finally:
            d2.send_socket.close()
            d2.listen_socket.close()

    def test_not_running_initially(self):
        self.assertFalse(self.discovery.running)
