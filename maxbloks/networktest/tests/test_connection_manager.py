# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import socket
import unittest
from unittest.mock import MagicMock
from maxbloks.networktest import connection_manager


class TestConnection(unittest.TestCase):

    def setUp(self):
        self.sock = MagicMock(spec=socket.socket)
        self.conn = connection_manager.Connection(self.sock, "192.168.1.1")

    def test_initial_state(self):
        self.assertTrue(self.conn.connected)
        self.assertEqual(self.conn.peer_ip, "192.168.1.1")

    def test_close_sets_disconnected(self):
        self.conn.close()
        self.assertFalse(self.conn.connected)

    def test_send_message_calls_socket(self):
        self.sock.sendall = MagicMock()
        result = self.conn.send_message({"type": "test"})
        self.assertTrue(result)
        self.sock.sendall.assert_called_once()


class TestConnectionManager(unittest.TestCase):

    def setUp(self):
        self.on_established = MagicMock()
        self.on_lost = MagicMock()
        self.on_received = MagicMock()
        self.cm = connection_manager.ConnectionManager(
            on_connection_established=self.on_established,
            on_connection_lost=self.on_lost,
            on_message_received=self.on_received,
        )

    def tearDown(self):
        try:
            self.cm.server_socket.close()
        except Exception:
            pass

    def test_listen_port(self):
        self.assertEqual(connection_manager.ConnectionManager.LISTEN_PORT, 19019)

    def test_initial_no_connections(self):
        self.assertEqual(self.cm.get_connected_peers(), [])

    def test_not_running_initially(self):
        self.assertFalse(self.cm.running)

    def test_disconnect_nonexistent_peer(self):
        self.cm.disconnect_peer("1.2.3.4")
        self.on_lost.assert_called_once_with("1.2.3.4")
