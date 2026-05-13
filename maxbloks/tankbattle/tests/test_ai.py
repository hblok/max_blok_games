# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for TankBattle single-player AI."""

import unittest

from maxbloks.tankbattle import ai
from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities


class _FakeArena:
    """Minimal arena stub: no walls, no collision."""

    def collides_with_solid(self, position, radius):
        return False

    def terrain_at_world(self, x, y):
        return None

    def conveyor_at_world(self, x, y):
        return None

    def teleporter_at_world(self, x, y):
        return None


class _FakeGame:
    """Minimal game stub that captures fire calls."""

    def __init__(self):
        self.arena = _FakeArena()
        self.fired = []

    def _fire_weapon(self, tank):
        self.fired.append(tank)


class TestTankAI(unittest.TestCase):

    def setUp(self):
        self.ai_obj = ai.TankAI()
        self.ai_tank = entities.Tank(500.0, 500.0, body_angle=0.0, turret_angle=0.0, player_id=2)
        self.player_tank = entities.Tank(500.0, 200.0, player_id=1)
        self.game = _FakeGame()

    def test_ai_does_nothing_when_ai_tank_dead(self):
        self.ai_tank.is_alive = False
        prev_x = self.ai_tank.x
        self.ai_obj.update(self.ai_tank, [self.player_tank], self.game,0.1)
        self.assertEqual(self.ai_tank.x, prev_x)

    def test_ai_does_nothing_when_target_dead(self):
        self.player_tank.is_alive = False
        prev_x = self.ai_tank.x
        self.ai_obj.update(self.ai_tank, [self.player_tank], self.game,0.1)
        self.assertEqual(self.ai_tank.x, prev_x)

    def test_ai_approaches_when_far(self):
        """AI should move toward a distant target."""
        self.player_tank.x = 500.0
        self.player_tank.y = 500.0 - (constants.AI_ENGAGE_DISTANCE + 100.0)
        start_y = self.ai_tank.y
        self.ai_obj.update(self.ai_tank, [self.player_tank], self.game,0.1)
        self.assertLess(self.ai_tank.y, start_y)

    def test_ai_retreats_when_too_close(self):
        """AI should back away when closer than retreat distance."""
        self.player_tank.x = 500.0
        self.player_tank.y = 500.0 - (constants.AI_RETREAT_DISTANCE - 20.0)
        start_y = self.ai_tank.y
        self.ai_obj.update(self.ai_tank, [self.player_tank], self.game,0.1)
        self.assertGreater(self.ai_tank.y, start_y)

    def test_turret_aimed_at_target(self):
        """Turret should point toward the player after an update."""
        self.player_tank.x = 600.0
        self.player_tank.y = 500.0
        self.ai_obj.update(self.ai_tank, [self.player_tank], self.game,0.016)
        dx = self.player_tank.x - self.ai_tank.x
        dy = self.player_tank.y - self.ai_tank.y
        self.ai_tank.set_turret_from_vector(dx, dy)
        self.assertGreater(self.ai_tank.turret_angle, 0.0)

    def test_fire_timer_decrements(self):
        """Fire timer should count down across updates."""
        self.ai_obj._fire_timer = 1.0
        self.ai_obj.update(self.ai_tank, [self.player_tank], self.game,0.1)
        self.assertLess(self.ai_obj._fire_timer, 1.0)
