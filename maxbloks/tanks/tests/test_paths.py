# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from pathlib import Path

from maxbloks.tanks import paths


class TestPaths(unittest.TestCase):

    def test_paths_exist(self):
        p = paths.GamePaths()
        self.assertIsInstance(p.root, Path)
        self.assertIsInstance(p.assets, Path)
        self.assertIsInstance(p.sprites, Path)
        self.assertIsInstance(p.sounds, Path)
        self.assertIsInstance(p.fonts, Path)

    def test_build_paths(self):
        p = paths.GamePaths()
        self.assertEqual(p.get_sprite_path("a.png").name, "a.png")
        self.assertEqual(p.get_sound_path("b.wav").name, "b.wav")
        self.assertEqual(p.get_font_path("c.ttf").name, "c.ttf")
