# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
settings.py — All tuning constants and configuration for Starfighter.

All positions, sizes, speeds, and radii are expressed in the logical
coordinate system (LOGICAL_WIDTH × LOGICAL_HEIGHT).  The display layer
scales the logical surface to the actual screen resolution.
"""

import os
import json

# ------------------------------------------------------------------
# Display
# ------------------------------------------------------------------
LOGICAL_WIDTH = 640
LOGICAL_HEIGHT = 480
FULLSCREEN = False          # Set True for handheld / kiosk
INTEGER_SCALING = True      # Prefer integer multiples when scaling
TARGET_FPS = 60

# ------------------------------------------------------------------
# Player ship
# ------------------------------------------------------------------
FRICTION = 0.98
ROTATION_SPEED = 0.05       # radians per frame (~3°)
THRUST_POWER = 0.12
MAX_SPEED = 5.0
PLAYER_RADIUS = 18
INVINCIBILITY_FRAMES = 120  # ~2 seconds at 60 FPS

# ------------------------------------------------------------------
# Bullets
# ------------------------------------------------------------------
BULLET_SPEED = 7.0
MAX_BULLETS = 5
BULLET_LIFETIME = 60        # frames (~1 second)
BULLET_RADIUS = 4
HOMING_SPEED = 3.5
HOMING_STEER = 0.06
HOMING_LIFETIME = 180
HOMING_MAX = 2
BIGSHOT_SPEED = 3.5
BIGSHOT_RADIUS = 12
BIGSHOT_LIFETIME = 120
BIGSHOT_MAX = 2

# ------------------------------------------------------------------
# Firing
# ------------------------------------------------------------------
FIRE_COOLDOWN_NORMAL = 15   # frames between shots
FIRE_COOLDOWN_RAPID = 5
RAPID_MAX_BULLETS = 10
SPREAD_ANGLE = 0.17         # ~10° half-cone

# ------------------------------------------------------------------
# Enemies
# ------------------------------------------------------------------
SAFE_SPAWN_RADIUS = 150
SPAWN_INTERVAL = 40         # frames between spawn attempts

# Drifter
DRIFTER_RADIUS = 12
DRIFTER_SPEED = 0.8
DRIFTER_HP = 1
DRIFTER_SCORE = 100
DRIFTER_DROP_CHANCE = 0.20
DRIFTER_DRIFT_INTERVAL = 120

# Gunner
GUNNER_RADIUS = 16
GUNNER_SPEED = 0.5
GUNNER_TURN_RATE = 0.02
GUNNER_SCORE_BASE = 200
GUNNER_SCORE_PER_HP = 50
GUNNER_DROP_CHANCE = 0.35
GUNNER_BULLET_SPEED = 3.0
GUNNER_BULLET_RADIUS = 3

# Kamikaze
KAMIKAZE_RADIUS = 10
KAMIKAZE_SPEED = 0.6
KAMIKAZE_ACCEL = 0.04
KAMIKAZE_MAX_SPEED = 4.0
KAMIKAZE_HP = 1
KAMIKAZE_SCORE = 150
KAMIKAZE_DROP_CHANCE = 0.25

# Boss
BOSS_RADIUS = 35
BOSS_SPEED = 0.3
BOSS_TURN_RATE = 0.01
BOSS_HP = 10
BOSS_SCORE = 1000
BOSS_DROP_CHANCE = 1.0
BOSS_DROPS = 2
BOSS_FIRE_RATE = 90         # frames
BOSS_BULLET_SPEED = 2.5
BOSS_BULLET_RADIUS = 4
BOSS_SPREAD = 0.2           # radians between spread bullets

# ------------------------------------------------------------------
# Difficulty tiers  (game_time in seconds)
# ------------------------------------------------------------------
TIER_THRESHOLDS = [0, 30, 60, 90]   # tier 1/2/3/4 boundaries
TIER_MAX_ENEMIES = [0, 3, 5, 6, 8]  # index = tier

# ------------------------------------------------------------------
# Power-ups
# ------------------------------------------------------------------
POWERUP_LIFETIME = 900      # frames (~15 s)
POWERUP_COLLECT_RADIUS = 20
POWERUP_RADIUS = 10

POWERUP_DURATION = {
    "shield":    900,   # 15 s
    "rapidfire": 600,   # 10 s
    "spreadshot": 600,
    "speedboost": 600,
    "homing":    600,
    "bigshot":   600,
}

SHIELD_HITS = 3
SHIELD_INVINCIBILITY = 30   # frames after absorbing a hit
SPEED_BOOST_MULT = 1.5

# ------------------------------------------------------------------
# Particles
# ------------------------------------------------------------------
PARTICLE_LIFETIME = 40
PARTICLE_SPEED_MIN = 1.0
PARTICLE_SPEED_MAX = 4.0
PARTICLE_FRICTION = 0.97
EXPLOSION_COUNT_ENEMY = 10
EXPLOSION_COUNT_PLAYER = 16

# ------------------------------------------------------------------
# Starfield
# ------------------------------------------------------------------
STAR_COUNT = 60

# ------------------------------------------------------------------
# Colors  (R, G, B tuples for Pygame)
# ------------------------------------------------------------------
COLORS = {
    "player":     (0, 255, 255),
    "bullet":     (255, 255, 255),
    "drifter":    (255, 0, 255),
    "gunner":     (255, 102, 0),
    "kamikaze":   (255, 0, 51),
    "boss":       (255, 215, 0),
    "shield":     (0, 136, 255),
    "rapidfire":  (255, 255, 0),
    "spreadshot": (0, 255, 136),
    "speedboost": (255, 136, 255),
    "homing":     (255, 68, 0),
    "bigshot":    (204, 0, 255),
    "hud":        (0, 255, 255),
    "menu_sub":   (255, 0, 255),
    "gameover":   (255, 0, 51),
    "thrust":     (255, 102, 0),
    "white":      (255, 255, 255),
    "black":      (0, 0, 0),
}

# ------------------------------------------------------------------
# Input  (joystick mappings — adjust for your controller)
# ------------------------------------------------------------------
JOYSTICK_DEADZONE = 0.25
JOYSTICK_FIRE_BUTTONS = [0, 1]       # A / B on most controllers
JOYSTICK_PAUSE_BUTTONS = [7, 6]      # Start / Select

# ------------------------------------------------------------------
# High-score persistence
# ------------------------------------------------------------------
HIGHSCORE_FILE = "highscore.json"


def load_highscore() -> int:
    """Load the persisted high score, returning 0 on any failure."""
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            data = json.load(f)
            return int(data.get("highscore", 0))
    except Exception:
        return 0


def save_highscore(score: int) -> None:
    """Persist a new high score to disk."""
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"highscore": score}, f)
    except Exception:
        pass