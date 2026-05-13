# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Dead-reckoning interpolation for remote tank movement."""

import time

from maxbloks.tankbattle import constants


class DeadReckoner:
    """Predict/interpolate remote tank movement between UDP packets."""

    def __init__(self):
        self.last_packet = None
        self.target_packet = None
        self.last_time = time.monotonic()
        self._vel_x = 0.0
        self._vel_y = 0.0

    def push_update(self, packet, now=None):
        """Record a received remote packet and compute velocity from position delta."""
        if now is None:
            now = time.monotonic()
        dt = now - self.last_time
        if self.target_packet is not None and dt > 0.001:
            self._vel_x = (packet.x - self.target_packet.x) / dt
            self._vel_y = (packet.y - self.target_packet.y) / dt
        else:
            # First packet or near-simultaneous update: fall back to packet fields
            self._vel_x = packet.velocity_x
            self._vel_y = packet.velocity_y
        self.last_packet = self.target_packet
        self.target_packet = packet
        self.last_time = now

    def predicted_position(self, now=None):
        """Return dead-reckoned current position extrapolated by computed velocity."""
        if now is None:
            now = time.monotonic()
        if self.target_packet is None:
            return 0.0, 0.0
        elapsed = min(constants.NETWORK_UPDATE_INTERVAL, max(0.0, now - self.last_time))
        x_value = self.target_packet.x + self._vel_x * elapsed
        y_value = self.target_packet.y + self._vel_y * elapsed
        return x_value, y_value

    def interpolated_position(self, alpha):
        """Interpolate from last to target packet."""
        if self.target_packet is None:
            return 0.0, 0.0
        if self.last_packet is None:
            return self.target_packet.x, self.target_packet.y
        alpha = max(0.0, min(1.0, alpha))
        x_value = self.last_packet.x + (self.target_packet.x - self.last_packet.x) * alpha
        y_value = self.last_packet.y + (self.target_packet.y - self.last_packet.y) * alpha
        return x_value, y_value
