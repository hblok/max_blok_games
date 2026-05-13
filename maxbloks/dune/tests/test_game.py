# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import MagicMock, patch

import pygame


class TestGameState(unittest.TestCase):

    def test_game_states_distinct(self):
        from maxbloks.dune.game import GameState
        states = list(GameState)
        self.assertEqual(len(states), len(set(states)))
        self.assertIn(GameState.MENU, states)
        self.assertIn(GameState.PLAYING, states)
        self.assertIn(GameState.PAUSED, states)
        self.assertIn(GameState.GAME_OVER, states)


class TestDuneGame(unittest.TestCase):

    def setUp(self):
        mock_surface = MagicMock(spec=pygame.Surface)
        mock_info = MagicMock()
        self._patch = patch(
            "maxbloks.dune.compat_sdl.init_display",
            return_value=(mock_surface, mock_info),
        )
        self._patch.start()
        pygame.init()
        from maxbloks.dune import game
        self.game = game.DuneGame()

    def tearDown(self):
        self._patch.stop()

    def test_initial_state_is_menu(self):
        from maxbloks.dune.game import GameState
        self.assertEqual(self.game.state, GameState.MENU)

    def test_confirm_transitions_menu_to_playing(self):
        from maxbloks.dune.game import GameState
        self.game._on_confirm()
        self.assertEqual(self.game.state, GameState.PLAYING)

    def test_confirm_transitions_paused_to_playing(self):
        from maxbloks.dune.game import GameState
        self.game.state = GameState.PAUSED
        self.game._on_confirm()
        self.assertEqual(self.game.state, GameState.PLAYING)

    def test_confirm_transitions_game_over_to_menu(self):
        from maxbloks.dune.game import GameState
        self.game.state = GameState.GAME_OVER
        self.game._on_confirm()
        self.assertEqual(self.game.state, GameState.MENU)

    def test_reset_game_resets_score(self):
        self.game.score = 99
        self.game._reset_game()
        self.assertEqual(self.game.score, 0)
