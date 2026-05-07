# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.tanks import game_state


class TestGameState(unittest.TestCase):

    def test_states(self):
        self.assertTrue(hasattr(game_state.GameState, "PLAYING"))
        self.assertTrue(hasattr(game_state.GameState, "GAME_OVER"))
        self.assertTrue(hasattr(game_state.GameState, "VICTORY"))

    def test_stats(self):
        s = game_state.GameStats()
        self.assertEqual(s.score, 0)
        s.enemy_killed()
        self.assertEqual(s.enemies_killed, 1)
        self.assertGreater(s.score, 0)
        s.reset()
        self.assertEqual(s.enemies_killed, 0)
