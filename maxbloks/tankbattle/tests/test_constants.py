# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.tankbattle import constants


class TestDisplayConstants(unittest.TestCase):

    def test_screen_dimensions_positive(self):
        self.assertGreater(constants.SCREEN_WIDTH, 0)
        self.assertGreater(constants.SCREEN_HEIGHT, 0)

    def test_fps_positive(self):
        self.assertGreater(constants.FPS, 0)

    def test_world_larger_than_screen(self):
        self.assertGreater(constants.WORLD_WIDTH, constants.SCREEN_WIDTH)
        self.assertGreater(constants.WORLD_HEIGHT, constants.SCREEN_HEIGHT)


class TestWorldConstants(unittest.TestCase):

    def test_tile_size_positive(self):
        self.assertGreater(constants.TILE_SIZE, 0)

    def test_world_tiles_match_dimensions(self):
        self.assertEqual(constants.WORLD_TILES_X, constants.WORLD_WIDTH // constants.TILE_SIZE)
        self.assertEqual(constants.WORLD_TILES_Y, constants.WORLD_HEIGHT // constants.TILE_SIZE)

    def test_world_width_divisible_by_tile(self):
        self.assertEqual(constants.WORLD_WIDTH % constants.TILE_SIZE, 0)

    def test_world_height_divisible_by_tile(self):
        self.assertEqual(constants.WORLD_HEIGHT % constants.TILE_SIZE, 0)


class TestTankConstants(unittest.TestCase):

    def test_tank_speed_positive(self):
        self.assertGreater(constants.TANK_SPEED, 0)

    def test_tank_max_hp_positive(self):
        self.assertGreater(constants.TANK_MAX_HP, 0)

    def test_tank_hitbox_radius_positive(self):
        self.assertGreater(constants.TANK_HITBOX_RADIUS, 0)

    def test_hitbox_smaller_than_collision(self):
        self.assertLessEqual(constants.TANK_HITBOX_RADIUS, constants.TANK_COLLISION_RADIUS + 1)

    def test_spawn_coords_within_world(self):
        for x, y in [
            (constants.SPAWN_ONE_X, constants.SPAWN_ONE_Y),
            (constants.SPAWN_TWO_X, constants.SPAWN_TWO_Y),
        ]:
            self.assertGreater(x, 0)
            self.assertLess(x, constants.WORLD_WIDTH)
            self.assertGreater(y, 0)
            self.assertLess(y, constants.WORLD_HEIGHT)


class TestNetworkConstants(unittest.TestCase):

    def test_ports_in_valid_range(self):
        for port in [constants.HOST_PORT, constants.DISCOVERY_PORT, constants.GAME_DATA_PORT]:
            self.assertGreater(port, 1023)
            self.assertLess(port, 65536)

    def test_ports_distinct(self):
        ports = [constants.HOST_PORT, constants.DISCOVERY_PORT, constants.GAME_DATA_PORT]
        self.assertEqual(len(ports), len(set(ports)))

    def test_ping_interval_positive(self):
        self.assertGreater(constants.PING_INTERVAL, 0)

    def test_network_update_hz_positive(self):
        self.assertGreater(constants.NETWORK_UPDATE_HZ, 0)


class TestHazardConstants(unittest.TestCase):

    def test_landmine_damage_positive(self):
        self.assertGreater(constants.LANDMINE_DAMAGE, 0)

    def test_landmine_arm_time_positive(self):
        self.assertGreater(constants.LANDMINE_ARM_TIME, 0)

    def test_turret_fire_interval_positive(self):
        self.assertGreater(constants.TURRET_FIRE_INTERVAL, 0)

    def test_turret_engage_distance_positive(self):
        self.assertGreater(constants.TURRET_ENGAGE_DISTANCE, 0)

    def test_ice_friction_between_zero_and_one(self):
        self.assertGreater(constants.ICE_FRICTION, 0)
        self.assertLessEqual(constants.ICE_FRICTION, 1.0)

    def test_mud_speed_modifier_between_zero_and_one(self):
        self.assertGreater(constants.MUD_SPEED_MODIFIER, 0)
        self.assertLessEqual(constants.MUD_SPEED_MODIFIER, 1.0)

    def test_teleporter_cooldown_positive(self):
        self.assertGreater(constants.TELEPORTER_COOLDOWN, 0)


class TestRoundConstants(unittest.TestCase):

    def test_rounds_to_win_positive(self):
        self.assertGreater(constants.ROUNDS_TO_WIN, 0)

    def test_round_time_positive(self):
        self.assertGreater(constants.ROUND_TIME_LIMIT, 0)
