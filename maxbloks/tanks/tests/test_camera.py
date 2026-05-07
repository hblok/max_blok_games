# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame
from numbers import Real

from maxbloks.tanks import camera
from maxbloks.tanks import position


class TestCamera(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.camera = camera.Camera(640, 480, 2400, 1800)

    def tearDown(self):
        pygame.quit()

    def test_update_and_apply(self):
        self.camera.update(position.Position(320, 240))
        self.assertGreaterEqual(self.camera.x, 0)
        self.assertGreaterEqual(self.camera.y, 0)

        world = position.Position(400, 300)
        screen = self.camera.apply(world)

        self.assertIsInstance(screen, position.Position)
        self.assertEqual(screen.x, 400)
        self.assertEqual(screen.y, 300)
        self.assertIsInstance(screen.x, Real)
        self.assertIsInstance(screen.y, Real)

    def test_rect_visibility(self):
        r = pygame.Rect(100, 100, 50, 50)
        self.camera.update(position.Position(200, 200))
        self.assertTrue(self.camera.is_rect_visible(r))
