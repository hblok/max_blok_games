# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import MagicMock, patch

import pygame

from maxbloks.dune import entities, constants


class TestPlayer(unittest.TestCase):

    def setUp(self):
        self.player = entities.Player(100, 150)

    def test_initial_position(self):
        self.assertEqual(self.player.x, 100.0)
        self.assertEqual(self.player.y, 150.0)

    def test_movement_right(self):
        self.player.update(1, 0, constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT)
        self.assertGreater(self.player.x, 100.0)
        self.assertAlmostEqual(self.player.y, 150.0)

    def test_movement_up(self):
        self.player.update(0, -1, constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT)
        self.assertAlmostEqual(self.player.x, 100.0)
        self.assertLess(self.player.y, 150.0)

    def test_no_movement(self):
        self.player.update(0, 0, constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT)
        self.assertAlmostEqual(self.player.x, 100.0)
        self.assertAlmostEqual(self.player.y, 150.0)

    def test_clamped_to_screen_right(self):
        for _ in range(300):
            self.player.update(1, 0, constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT)
        self.assertLessEqual(self.player.x, constants.LOGICAL_WIDTH - self.player.size)

    def test_clamped_to_screen_left(self):
        for _ in range(300):
            self.player.update(-1, 0, constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT)
        self.assertGreaterEqual(self.player.x, self.player.size)

    def test_collides_with_nearby(self):
        other = entities.Player(100 + self.player.size, 150)
        self.assertTrue(self.player.collides_with(other))

    def test_no_collision_with_distant(self):
        other = entities.Player(400, 400)
        self.assertFalse(self.player.collides_with(other))

    @patch("pygame.draw.circle")
    def test_draw_does_not_raise(self, mock_circle):
        surface = MagicMock()
        self.player.draw(surface)
        mock_circle.assert_called_once()
