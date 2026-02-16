# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.dogrider.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    SKY_BLUE, GRASS_GREEN, LIGHT_GREEN, DARK_GREEN, MOUNTAIN_BLUE,
    WHITE, ORANGE, RED_ORANGE, BROWN, LIGHT_BROWN, BLACK, GRAY,
    DARK_GRAY, SILVER, GOLD, PINK, RED, TREE_BROWN, TREE_GREEN,
    YELLOW, BLUE, CHROME,
    GRAVITY, JUMP_POWER, FORWARD_JUMP_BOOST, GROUND_Y,
    MAX_GAME_SPEED, SPEED_INCREASE_RATE, MAX_OBSTACLES,
    JOYSTICK_DEADZONE
)


class TestConstants(unittest.TestCase):

    def test_screen_dimensions(self):
        self.assertEqual(SCREEN_WIDTH, 640)
        self.assertEqual(SCREEN_HEIGHT, 480)

    def test_gravity(self):
        self.assertEqual(GRAVITY, 0.8)

    def test_jump_power(self):
        self.assertEqual(JUMP_POWER, -15)

    def test_forward_jump_boost(self):
        self.assertEqual(FORWARD_JUMP_BOOST, 4)

    def test_ground_y(self):
        self.assertEqual(GROUND_Y, 350)

    def test_max_game_speed(self):
        self.assertEqual(MAX_GAME_SPEED, 6.0)

    def test_speed_increase_rate(self):
        self.assertEqual(SPEED_INCREASE_RATE, 0.0005)

    def test_max_obstacles(self):
        self.assertEqual(MAX_OBSTACLES, 75)

    def test_joystick_deadzone(self):
        self.assertEqual(JOYSTICK_DEADZONE, 0.2)

    def test_color_constants(self):
        self.assertEqual(SKY_BLUE, (135, 206, 235))
        self.assertEqual(GRASS_GREEN, (34, 139, 34))
        self.assertEqual(WHITE, (255, 255, 255))
        self.assertEqual(RED, (255, 0, 0))
        self.assertEqual(BLUE, (0, 0, 255))
        self.assertEqual(GOLD, (255, 215, 0))