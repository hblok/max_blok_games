# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from maxbloks.tankbattle import states


class TestGameState(unittest.TestCase):

    def test_menu_value(self):
        self.assertEqual(states.GameState.MENU.value, "menu")

    def test_playing_value(self):
        self.assertEqual(states.GameState.PLAYING.value, "playing")

    def test_countdown_value(self):
        self.assertEqual(states.GameState.COUNTDOWN.value, "countdown")

    def test_has_eight_states(self):
        self.assertEqual(len(list(states.GameState)), 8)

    def test_values_are_unique(self):
        values = [s.value for s in states.GameState]
        self.assertEqual(len(values), len(set(values)))

    def test_all_expected_states_present(self):
        names = {s.name for s in states.GameState}
        expected = {"MENU", "LOBBY", "CONNECTING", "COUNTDOWN", "PLAYING", "PAUSED", "ROUND_OVER", "MATCH_OVER"}
        self.assertEqual(names, expected)
