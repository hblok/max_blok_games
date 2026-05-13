# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Simple rule-based AI opponent for single-player mode."""

import logging
import math
import random

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import utils

logger = logging.getLogger(__name__)


class TankAI:
    """Steer an AI tank toward the player and fire when aimed."""

    def __init__(self):
        self._fire_timer = 0.0

    def update(self, ai_tank, targets, game, dt):
        """Apply movement and firing to ai_tank for one frame.

        targets: list of Tank objects to attack; picks the nearest alive one.
        """
        if not ai_tank.is_alive:
            return
        alive = [t for t in targets if t.is_alive]
        if not alive:
            return
        target_tank = min(alive, key=lambda t: math.hypot(t.x - ai_tank.x, t.y - ai_tank.y))
        dx = target_tank.x - ai_tank.x
        dy = target_tank.y - ai_tank.y
        dist = math.hypot(dx, dy)
        target_angle = utils.vector_to_angle(dx, dy)

        self._steer(ai_tank, target_angle, dt)
        self._drive(ai_tank, dist, dt, game.arena)
        self._aim_and_fire(ai_tank, dx, dy, dist, target_angle, game, dt)

    def _steer(self, ai_tank, target_angle, dt):
        delta = utils.shortest_angle_delta(ai_tank.body_angle, target_angle)
        max_step = constants.TANK_ROTATION_SPEED * dt
        if abs(delta) <= max_step:
            ai_tank.body_angle = utils.normalize_angle(target_angle)
        else:
            ai_tank.rotate_body(1.0 if delta > 0 else -1.0, dt)

    def _drive(self, ai_tank, dist, dt, arena):
        if dist > constants.AI_ENGAGE_DISTANCE:
            ai_tank.move(1.0, dt, arena)
        elif dist < constants.AI_RETREAT_DISTANCE:
            ai_tank.move(-1.0, dt, arena)

    def _aim_and_fire(self, ai_tank, dx, dy, dist, target_angle, game, dt):
        if dist > 0:
            ai_tank.set_turret_from_vector(dx / dist, dy / dist)
        self._fire_timer -= dt
        if self._fire_timer > 0.0:
            return
        turret_delta = abs(utils.shortest_angle_delta(ai_tank.turret_angle, target_angle))
        if turret_delta < constants.AI_AIM_TOLERANCE_DEG:
            logger.debug("AI firing (dist=%.0f, turret_delta=%.1f°)", dist, turret_delta)
            game._fire_weapon(ai_tank)
            self._fire_timer = random.uniform(
                constants.AI_FIRE_INTERVAL_MIN, constants.AI_FIRE_INTERVAL_MAX
            )
        else:
            self._fire_timer = 0.1
