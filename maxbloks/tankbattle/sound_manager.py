# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Sound effects manager for TankBattle.

Loads OGG files from assets/sounds/ when present; falls back to
procedurally generated tones so the game has audio without needing
real assets.
"""

import array
import logging
import math
import os
import pathlib
import random

logger = logging.getLogger(__name__)

_ASSETS_DIR = pathlib.Path(__file__).parent / "assets" / "sounds"

_SOUND_NAMES = [
    "shoot",
    "shoot_rocket",
    "hit",
    "explosion",
    "mine_place",
    "mine_explode",
    "powerup",
    "round_start",
    "round_over",
]

# (tone_freq_hz, duration_s, volume, envelope)
_TONE_RECIPES = {
    "shoot":       (900.0,  0.08, 0.40, "decay"),
    "shoot_rocket":(160.0,  0.18, 0.55, "decay"),
    "hit":         (440.0,  0.06, 0.40, "decay"),
    "mine_place":  (1200.0, 0.05, 0.30, "decay"),
    "round_over":  (440.0,  0.30, 0.50, "decay"),
}


class SoundManager:
    """Load and play game sound effects with procedural fallback synthesis."""

    def __init__(self, pygame_module):
        self.pygame = pygame_module
        self._enabled = False
        self._sounds = {}
        self._init_mixer()
        if self._enabled:
            self._load_all()

    # Fallback configs tried in order if the mixer isn't already initialized.
    # compat_sdl.init_audio() normally handles this before pygame.init(),
    # but these configs serve as a safety net if it wasn't called.
    _MIXER_FALLBACK_CONFIGS = [
        (44100, -16, 2, 1024),
        (22050, -16, 2, 512),
        (44100, -16, 1, 512),
    ]

    def _init_mixer(self):
        drv = os.environ.get("SDL_AUDIODRIVER", "(auto)")
        logger.info("SoundManager: SDL_AUDIODRIVER=%s", drv)
        result = self.pygame.mixer.get_init()
        logger.info("SoundManager: mixer state on entry: %s", result)

        if result and result != (0, 0, 0):
            logger.info("SoundManager: mixer already up (%s)", result)
            self._enabled = True
            return

        for freq, size, channels, buf in self._MIXER_FALLBACK_CONFIGS:
            try:
                self.pygame.mixer.init(frequency=freq, size=size, channels=channels, buffer=buf)
                actual = self.pygame.mixer.get_init()
                logger.info("SoundManager: mixer init succeeded: %s", actual)
                self._enabled = True
                return
            except Exception as exc:
                logger.debug("SoundManager: config (%d,%d,%d,%d) failed: %s",
                             freq, size, channels, buf, exc)
                try:
                    self.pygame.mixer.quit()
                except Exception:
                    pass

        logger.warning("SoundManager: audio disabled — all configurations failed")

    def _load_all(self):
        freq, _size, channels = self.pygame.mixer.get_init()
        logger.info("SoundManager: loading sounds (freq=%d channels=%d)", freq, channels)
        for name in _SOUND_NAMES:
            path = _ASSETS_DIR / f"{name}.ogg"
            if path.is_file():
                try:
                    self._sounds[name] = self.pygame.mixer.Sound(str(path))
                    logger.info("SoundManager: loaded %s from disk", name)
                    continue
                except Exception as exc:
                    logger.warning("SoundManager: could not load %s (%s)", path, exc)
            self._sounds[name] = self._synthesize(name, freq, channels)
            logger.debug("SoundManager: synthesized %s", name)

    # ------------------------------------------------------------------
    # Synthesis helpers
    # ------------------------------------------------------------------

    def _synthesize(self, name, freq, channels):
        if name in _TONE_RECIPES:
            tone_freq, duration, volume, env = _TONE_RECIPES[name]
            return self._make_tone(tone_freq, duration, volume, freq, channels, env)
        if name == "explosion":
            return self._make_explosion(freq, channels, duration=0.45, volume=0.70)
        if name == "mine_explode":
            return self._make_explosion(freq, channels, duration=0.55, volume=0.65)
        if name == "powerup":
            return self._make_sweep(400.0, 1200.0, 0.20, 0.45, freq, channels)
        if name == "round_start":
            return self._make_sweep(330.0, 880.0, 0.15, 0.40, freq, channels)
        return self._make_tone(440.0, 0.10, 0.30, freq, channels)

    @staticmethod
    def _apply_envelope(i, n, style):
        if style == "decay":
            return 1.0 - i / n
        if style == "attack_decay":
            half = n // 2
            if i < half:
                return i / max(1, half)
            return 1.0 - (i - half) / max(1, n - half)
        return 1.0

    def _make_tone(self, tone_freq, duration, volume, freq, channels, envelope="decay"):
        n = max(1, int(freq * duration))
        buf = array.array("h")
        for i in range(n):
            t = i / freq
            amp = self._apply_envelope(i, n, envelope)
            sample = max(-32767, min(32767,
                int(amp * volume * 32767 * math.sin(2 * math.pi * tone_freq * t))))
            buf.append(sample)
            if channels == 2:
                buf.append(sample)
        return self.pygame.mixer.Sound(buffer=buf)

    def _make_sweep(self, f_start, f_end, duration, volume, freq, channels):
        """Frequency-modulated ascending or descending tone."""
        n = max(1, int(freq * duration))
        buf = array.array("h")
        phase = 0.0
        for i in range(n):
            f_now = f_start + (f_end - f_start) * (i / n)
            phase += 2 * math.pi * f_now / freq
            env = 1.0 if i < n * 0.7 else (1.0 - (i / n - 0.7) / 0.3)
            sample = max(-32767, min(32767,
                int(math.sin(phase) * 32767 * volume * env)))
            buf.append(sample)
            if channels == 2:
                buf.append(sample)
        return self.pygame.mixer.Sound(buffer=buf)

    def _make_explosion(self, freq, channels, duration, volume):
        """Low rumble mixing a tonal sine with decaying white noise."""
        n = max(1, int(freq * duration))
        buf = array.array("h")
        for i in range(n):
            t = i / freq
            progress = i / n
            env_tonal = math.pow(1.0 - progress, 1.5)
            env_noise = (1.0 - progress) ** 3
            tonal = math.sin(2 * math.pi * 90.0 * t) * env_tonal * 0.4
            noise = random.uniform(-1.0, 1.0) * env_noise * 0.6
            sample = max(-32767, min(32767,
                int((tonal + noise) * 32767 * volume)))
            buf.append(sample)
            if channels == 2:
                buf.append(sample)
        return self.pygame.mixer.Sound(buffer=buf)

    # ------------------------------------------------------------------
    # Public play API
    # ------------------------------------------------------------------

    def _play(self, name):
        if not self._enabled:
            logger.debug("SoundManager: _play(%s) skipped — audio disabled", name)
            return
        sound = self._sounds.get(name)
        if sound:
            logger.debug("SoundManager: playing %s", name)
            sound.play()
        else:
            logger.debug("SoundManager: _play(%s) — sound not found", name)

    def play_shoot(self):
        self._play("shoot")

    def play_shoot_rocket(self):
        self._play("shoot_rocket")

    def play_hit(self):
        self._play("hit")

    def play_explosion(self):
        self._play("explosion")

    def play_mine_place(self):
        self._play("mine_place")

    def play_mine_explode(self):
        self._play("mine_explode")

    def play_powerup(self):
        self._play("powerup")

    def play_round_start(self):
        self._play("round_start")

    def play_round_over(self):
        self._play("round_over")
