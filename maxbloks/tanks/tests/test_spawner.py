# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.tanks import spawner
from maxbloks.tanks import constants


class TestSpawner(unittest.TestCase):

    def setUp(self):
        self.cfg = constants.EnemyConfig()
        self.spawner = spawner.EnemySpawner(2400, 1800, self.cfg)

    def test_spawn_timing_and_limits(self):
        self.assertTrue(self.spawner.should_spawn(5000, 0))
        self.spawner.last_spawn_time = 4990
        self.assertFalse(self.spawner.should_spawn(5000, 0))
        self.assertFalse(self.spawner.should_spawn(999999, self.cfg.max_enemies))

    def test_spawn_enemy(self):
        e = self.spawner.spawn_enemy(1000, 0)
        self.assertIsNotNone(e)
        self.assertGreater(self.spawner.last_spawn_time, 0)
