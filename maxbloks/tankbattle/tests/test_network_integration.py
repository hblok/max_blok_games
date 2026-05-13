# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Integration tests for the TankBattle network layer.

TCP tests use socket.socketpair() (AF_UNIX stream) so no real port
binding is needed and there are no loopback timing races.  UDP tests
use a single ephemeral-port receiver socket to verify packet
serialisation + transport without involving NetworkManager internals.
"""

import unittest

from maxbloks.tankbattle import constants
from maxbloks.tankbattle.network import manager as _manager
from maxbloks.tankbattle.network import packet as _packet
from maxbloks.tankbattle.tests import network_test_utils as _utils

NetworkManager = _manager.NetworkManager
PlayerUpdatePacket = _packet.PlayerUpdatePacket
PacketCodec = _packet.PacketCodec


def _make_packet(**kwargs):
    defaults = dict(
        player_id=1, x=100.0, y=200.0,
        body_angle=45.0, turret_angle=90.0,
        hp=8, weapon="primary", weapon_timer=0.0,
    )
    defaults.update(kwargs)
    return PlayerUpdatePacket(**defaults)


# ---------------------------------------------------------------------------
# TCP handshake
# ---------------------------------------------------------------------------

class TestTCPHandshake(unittest.TestCase):
    """Two NetworkManagers connected via socketpair complete a WELCOME
    handshake without any real TCP stack or port binding."""

    def setUp(self):
        self.host = NetworkManager()
        self.client = NetworkManager()
        _utils.wire_pair(self.host, self.client)
        _utils.pump_tcp(self.host, self.client)

    def tearDown(self):
        self.host.close()
        self.client.close()

    def test_host_monitor_connected(self):
        self.assertTrue(self.host.monitor.connected)

    def test_client_monitor_connected(self):
        self.assertTrue(self.client.monitor.connected)

    def test_host_handshake_ack_time_recorded(self):
        self.assertGreater(self.host.monitor.handshake_ack_time, 0.0)

    def test_client_handshake_ack_time_recorded(self):
        self.assertGreater(self.client.monitor.handshake_ack_time, 0.0)

    def test_host_last_received_updated(self):
        self.assertGreater(self.host.monitor.last_received, 0.0)

    def test_client_last_received_updated(self):
        self.assertGreater(self.client.monitor.last_received, 0.0)


# ---------------------------------------------------------------------------
# Reliable events (TCP)
# ---------------------------------------------------------------------------

class TestReliableEvents(unittest.TestCase):
    """Reliable events sent over the TCP connection arrive with correct
    names and payloads in both directions."""

    def setUp(self):
        self.host = NetworkManager()
        self.client = NetworkManager()
        _utils.wire_pair(self.host, self.client)
        _utils.pump_tcp(self.host, self.client)

    def tearDown(self):
        self.host.close()
        self.client.close()

    def _collect(self, net, n=5):
        events = []
        for _ in range(n):
            events += net.process_tcp_messages()
        return events

    # --- host → client ---

    def test_arena_seed_arrives_at_client(self):
        self.host.send_reliable_event("arena_seed", {"seed": 99})
        events = self._collect(self.client)
        self.assertIn("arena_seed", [n for n, _ in events])

    def test_arena_seed_payload_correct(self):
        self.host.send_reliable_event("arena_seed", {"seed": 12345})
        events = self._collect(self.client)
        payload = next(p for n, p in events if n == "arena_seed")
        self.assertEqual(payload["seed"], 12345)

    def test_match_start_arrives_at_client(self):
        self.host.send_reliable_event("match_start")
        events = self._collect(self.client)
        self.assertIn("match_start", [n for n, _ in events])

    def test_two_events_both_arrive(self):
        self.host.send_reliable_event("arena_seed", {"seed": 1})
        self.host.send_reliable_event("match_start")
        events = self._collect(self.client, n=10)
        names = [n for n, _ in events]
        self.assertIn("arena_seed", names)
        self.assertIn("match_start", names)

    # --- client → host ---

    def test_event_arrives_at_host(self):
        self.client.send_reliable_event("round_result", {"winner": 2})
        events = self._collect(self.host)
        self.assertIn("round_result", [n for n, _ in events])

    def test_event_payload_client_to_host(self):
        self.client.send_reliable_event("round_result", {"winner": 2})
        events = self._collect(self.host)
        payload = next(p for n, p in events if n == "round_result")
        self.assertEqual(payload["winner"], 2)


# ---------------------------------------------------------------------------
# UDP player update round-trip
# ---------------------------------------------------------------------------

class TestUDPPlayerUpdate(unittest.TestCase):
    """PlayerUpdatePacket sent over a real UDP socket (ephemeral port) is
    received and deserialized with values intact."""

    def setUp(self):
        self.receiver = _utils.make_udp_socket()
        self.recv_port = self.receiver.getsockname()[1]
        import socket as _socket
        self.sender = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)

    def tearDown(self):
        self.receiver.close()
        self.sender.close()

    def _send_recv(self, packet):
        data = PacketCodec.serialize_player_update(packet)
        self.sender.sendto(data, ("127.0.0.1", self.recv_port))
        raw, _ = self.receiver.recvfrom(constants.MAX_PACKET_SIZE)
        return PacketCodec.deserialize_player_update(raw)

    def test_player_id_preserved(self):
        result = self._send_recv(_make_packet(player_id=2))
        self.assertEqual(result.player_id, 2)

    def test_position_preserved(self):
        result = self._send_recv(_make_packet(x=1234.5, y=678.9))
        self.assertAlmostEqual(result.x, 1234.5, places=1)
        self.assertAlmostEqual(result.y, 678.9, places=1)

    def test_hp_preserved(self):
        result = self._send_recv(_make_packet(hp=3))
        self.assertEqual(result.hp, 3)

    def test_fired_flag_preserved(self):
        result = self._send_recv(_make_packet(fired=True, fire_angle=45.0))
        self.assertTrue(result.fired)
        self.assertAlmostEqual(result.fire_angle, 45.0, places=1)

    def test_mine_dropped_preserved(self):
        result = self._send_recv(_make_packet(
            mine_dropped=True, mine_x=500.0, mine_y=600.0))
        self.assertTrue(result.mine_dropped)
        self.assertAlmostEqual(result.mine_x, 500.0, places=1)

    def test_weapon_preserved(self):
        result = self._send_recv(_make_packet(weapon="rocket"))
        self.assertEqual(result.weapon, "rocket")

    def test_powerup_id_preserved(self):
        result = self._send_recv(_make_packet(powerup_collected_id=7))
        self.assertEqual(result.powerup_collected_id, 7)


# ---------------------------------------------------------------------------
# UDP through NetworkManager — send_player_update → receive_udp
# ---------------------------------------------------------------------------

class TestNetworkManagerUDP(unittest.TestCase):
    """NetworkManager.send_player_update() delivers to receive_udp() on
    the peer, using injected ephemeral UDP sockets."""

    def setUp(self):
        self.host = NetworkManager()
        self.client = NetworkManager()
        _utils.wire_pair(self.host, self.client)
        _utils.wire_udp(self.host, self.client)
        _utils.pump_tcp(self.host, self.client)

    def tearDown(self):
        self.host.close()
        self.client.close()

    def test_client_to_host_arrives(self):
        pkt = _make_packet(player_id=2, x=300.0, y=400.0)
        self.client.send_player_update(pkt)
        updates = []
        for _ in range(5):
            updates += self.host.receive_udp()
        self.assertEqual(len(updates), 1)

    def test_position_preserved_through_manager(self):
        pkt = _make_packet(player_id=2, x=999.0, y=888.0)
        self.client.send_player_update(pkt)
        updates = []
        for _ in range(5):
            updates += self.host.receive_udp()
        self.assertAlmostEqual(updates[0].x, 999.0, places=1)

    def test_host_to_client_arrives(self):
        pkt = _make_packet(player_id=1, x=100.0, y=200.0)
        self.host.send_player_update(pkt)
        updates = []
        for _ in range(5):
            updates += self.client.receive_udp()
        self.assertEqual(len(updates), 1)

    def test_receive_udp_updates_dead_reckoner(self):
        pkt = _make_packet(player_id=2, x=555.0)
        self.client.send_player_update(pkt)
        for _ in range(5):
            self.host.receive_udp()
        self.assertIsNotNone(self.host.last_remote_update)
        self.assertAlmostEqual(self.host.last_remote_update.x, 555.0, places=1)

    def test_update_cadence_honours_interval(self):
        interval = constants.NETWORK_UPDATE_INTERVAL
        now = 0.0
        sent = 0
        for i in range(5):
            now += interval
            if self.client.should_send_update(now):
                self.client.send_player_update(_make_packet(player_id=2, x=float(i * 10)))
                sent += 1
        updates = []
        for _ in range(20):
            updates += self.host.receive_udp()
        self.assertEqual(len(updates), sent)
