# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Connection quality and handshake state tracking."""

import time

from maxbloks.tankbattle import constants


class ConnectionMonitor:
    """Track bidirectional connection state and quality.

    Maintains timestamps of the last received message from the peer,
    the last sent ping, and round-trip latency estimates.  The
    *quality* property returns a float in [0, 1] representing recent
    message throughput.
    """

    def __init__(self):
        self.last_received = 0.0          # monotonic timestamp of last peer message
        self.last_ping_sent = 0.0         # monotonic timestamp of last ping we sent
        self.last_ping_recv = 0.0         # monotonic timestamp of last ping we received
        self.latency_samples = []         # recent RTT samples (seconds)
        self._max_samples = 10
        self.connected = False            # True once welcome handshake completes
        self.handshake_sent_time = 0.0    # when we sent our welcome
        self.handshake_ack_time = 0.0     # when we received the welcome-ack

    def mark_received(self, now=None):
        """Record that a message was received from the peer."""
        if now is None:
            now = time.monotonic()
        self.last_received = now

    def mark_ping_sent(self, now=None):
        """Record that a ping was sent."""
        if now is None:
            now = time.monotonic()
        self.last_ping_sent = now

    def record_pong(self, send_ts, now=None):
        """Record a received pong (ping reply).  *send_ts* is the
        timestamp the peer echoed back from our original ping."""
        if now is None:
            now = time.monotonic()
        self.last_ping_recv = now
        rtt = now - send_ts
        if rtt > 0:
            self.latency_samples.append(rtt)
            if len(self.latency_samples) > self._max_samples:
                self.latency_samples.pop(0)

    @property
    def avg_latency(self):
        """Average round-trip latency in seconds."""
        if not self.latency_samples:
            return 0.0
        return sum(self.latency_samples) / len(self.latency_samples)

    @property
    def quality(self):
        """Connection quality as a float in [0, 1].

        Based on how recently we received a message from the peer.
        Returns 1.0 if the last message was within one ping interval,
        decaying linearly to 0.0 over three ping intervals.
        """
        if not self.connected or self.last_received == 0.0:
            return 0.0
        now = time.monotonic()
        elapsed = now - self.last_received
        threshold = constants.PING_INTERVAL * 3
        if elapsed >= threshold:
            return 0.0
        return max(0.0, 1.0 - elapsed / threshold)

    @property
    def is_connected(self):
        """Whether the bidirectional handshake has completed and the
        peer is still responsive."""
        if not self.connected:
            return False
        now = time.monotonic()
        # Consider disconnected if no message for 3x the ping interval
        if self.last_received > 0 and (now - self.last_received) > constants.PING_INTERVAL * 3:
            return False
        return True
