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

    def push_update(self, packet, now=None):
        """Record a received remote packet."""
        if now is None:
            now = time.monotonic()
        self.last_packet = self.target_packet
        self.target_packet = packet
        self.last_time = now

    def predicted_position(self, now=None):
        """Return dead-reckoned current position."""
        if now is None:
            now = time.monotonic()
        if self.target_packet is None:
            return 0.0, 0.0
        elapsed = min(constants.NETWORK_UPDATE_INTERVAL, max(0.0, now - self.last_time))
        x_value = self.target_packet.x + self.target_packet.velocity_x * elapsed
        y_value = self.target_packet.y + self.target_packet.velocity_y * elapsed
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
