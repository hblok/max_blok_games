# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
import pygame

from maxbloks.tankbattle import sound_manager as _sm


class TestSoundManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.mgr = _sm.SoundManager(pygame)

    # --- Initialisation ---

    def test_enabled_with_dummy_driver(self):
        self.assertTrue(self.mgr._enabled)

    def test_all_sounds_loaded(self):
        for name in _sm._SOUND_NAMES:
            self.assertIn(name, self.mgr._sounds, f"Missing sound: {name}")

    def test_all_sounds_are_sound_objects(self):
        for name, snd in self.mgr._sounds.items():
            self.assertIsInstance(snd, pygame.mixer.Sound, f"Bad type for: {name}")

    # --- Play methods do not raise ---

    def test_play_shoot(self):
        self.mgr.play_shoot()

    def test_play_shoot_rocket(self):
        self.mgr.play_shoot_rocket()

    def test_play_hit(self):
        self.mgr.play_hit()

    def test_play_explosion(self):
        self.mgr.play_explosion()

    def test_play_mine_place(self):
        self.mgr.play_mine_place()

    def test_play_mine_explode(self):
        self.mgr.play_mine_explode()

    def test_play_powerup(self):
        self.mgr.play_powerup()

    def test_play_round_start(self):
        self.mgr.play_round_start()

    def test_play_round_over(self):
        self.mgr.play_round_over()

    # --- Synthesis helpers produce non-empty Sound objects ---

    def _get_mixer_params(self):
        freq, _size, channels = pygame.mixer.get_init()
        return freq, channels

    def test_make_tone_returns_sound(self):
        freq, channels = self._get_mixer_params()
        snd = self.mgr._make_tone(440.0, 0.1, 0.5, freq, channels)
        self.assertIsInstance(snd, pygame.mixer.Sound)

    def test_make_tone_stereo_returns_sound(self):
        freq, _ = self._get_mixer_params()
        snd = self.mgr._make_tone(440.0, 0.1, 0.5, freq, 2)
        self.assertIsInstance(snd, pygame.mixer.Sound)

    def test_make_sweep_returns_sound(self):
        freq, channels = self._get_mixer_params()
        snd = self.mgr._make_sweep(400.0, 1200.0, 0.1, 0.4, freq, channels)
        self.assertIsInstance(snd, pygame.mixer.Sound)

    def test_make_explosion_returns_sound(self):
        freq, channels = self._get_mixer_params()
        snd = self.mgr._make_explosion(freq, channels, 0.2, 0.5)
        self.assertIsInstance(snd, pygame.mixer.Sound)

    # --- Disabled manager is silent ---

    def test_disabled_manager_does_not_crash_on_play(self):
        mgr = _sm.SoundManager(pygame)
        mgr._enabled = False
        mgr.play_shoot()
        mgr.play_explosion()

    # --- Envelope helper ---

    def test_envelope_decay_starts_full(self):
        self.assertAlmostEqual(_sm.SoundManager._apply_envelope(0, 100, "decay"), 1.0)

    def test_envelope_decay_ends_near_zero(self):
        self.assertAlmostEqual(_sm.SoundManager._apply_envelope(99, 100, "decay"), 0.01)

    def test_envelope_attack_decay_peaks_at_midpoint(self):
        val = _sm.SoundManager._apply_envelope(50, 100, "attack_decay")
        self.assertAlmostEqual(val, 1.0, places=1)

    def test_envelope_flat_always_one(self):
        for i in [0, 50, 99]:
            self.assertAlmostEqual(_sm.SoundManager._apply_envelope(i, 100, "flat"), 1.0)
