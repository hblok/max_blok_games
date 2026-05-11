# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for ConnectionMonitor quality and handshake tracking."""

import time
import unittest

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import network


class TestConnectionMonitor(unittest.TestCase):

    def test_initial_state(self):
        monitor = network.ConnectionMonitor()
        self.assertFalse(monitor.connected)
        self.assertEqual(monitor.quality, 0.0)
        self.assertFalse(monitor.is_connected)

    def test_quality_after_mark_received(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = True
        monitor.mark_received(now=time.monotonic())
        self.assertGreater(monitor.quality, 0.9)

    def test_quality_decays_over_time(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = True
        old_time = time.monotonic() - constants.PING_INTERVAL
        monitor.mark_received(now=old_time)
        quality = monitor.quality
        self.assertLess(quality, 1.0)
        self.assertGreater(quality, 0.0)

    def test_quality_zero_when_stale(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = True
        stale_time = time.monotonic() - constants.PING_INTERVAL * 4
        monitor.mark_received(now=stale_time)
        self.assertEqual(monitor.quality, 0.0)

    def test_is_connected_false_when_not_handshaken(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = False
        self.assertFalse(monitor.is_connected)

    def test_is_connected_false_when_stale(self):
        monitor = network.ConnectionMonitor()
        monitor.connected = True
        stale_time = time.monotonic() - constants.PING_INTERVAL * 4
        monitor.mark_received(now=stale_time)
        self.assertFalse(monitor.is_connected)

    def test_latency_tracking(self):
        monitor = network.ConnectionMonitor()
        now = time.monotonic()
        send_ts = now - 0.025  # 25ms RTT
        monitor.record_pong(send_ts, now=now)
        self.assertGreater(monitor.avg_latency, 0.0)
        self.assertLess(monitor.avg_latency, 0.1)

    def test_handshake_timing(self):
        monitor = network.ConnectionMonitor()
        self.assertEqual(monitor.handshake_sent_time, 0.0)
        self.assertEqual(monitor.handshake_ack_time, 0.0)
        now = time.monotonic()
        monitor.handshake_sent_time = now
        monitor.handshake_ack_time = now + 0.05
        self.assertGreater(monitor.handshake_ack_time, monitor.handshake_sent_time)
