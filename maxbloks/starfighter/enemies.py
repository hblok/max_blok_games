# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
enemies.py — Enemy classes: Drifter, Gunner, Kamikaze, Boss.

Each enemy type has its own update logic.  Spawning and tier
management live in game.py.
"""

from __future__ import annotations

import math
import random

from starfighter.settings import (
    LOGICAL_WIDTH, LOGICAL_HEIGHT, COLORS,
    DRIFTER_RADIUS, DRIFTER_SPEED, DRIFTER_HP, DRIFTER_SCORE,
    DRIFTER_DROP_CHANCE, DRIFTER_DRIFT_INTERVAL,
    GUNNER_RADIUS, GUNNER_SPEED, GUNNER_TURN_RATE,
    GUNNER_SCORE_BASE, GUNNER_SCORE_PER_HP, GUNNER_DROP_CHANCE,
    GUNNER_BULLET_SPEED, GUNNER_BULLET_RADIUS,
    KAMIKAZE_RADIUS, KAMIKAZE_SPEED, KAMIKAZE_ACCEL,
    KAMIKAZE_MAX_SPEED, KAMIKAZE_HP, KAMIKAZE_SCORE,
    KAMIKAZE_DROP_CHANCE,
    BOSS_RADIUS, BOSS_SPEED, BOSS_TURN_RATE, BOSS_HP, BOSS_SCORE,
    BOSS_DROP_CHANCE, BOSS_DROPS, BOSS_FIRE_RATE,
    BOSS_BULLET_SPEED, BOSS_BULLET_RADIUS, BOSS_SPREAD,
    SAFE_SPAWN_RADIUS, TIER_MAX_ENEMIES,
)
from starfighter.entities import Bullet
from starfighter.utils import (
    wrap_position, clamp_magnitude, normalize_angle,
    random_range, distance,
)


# ======================================================================
# Base Enemy
# ======================================================================

class Enemy:
    """Base class for all enemy types."""

    enemy_type: str = "unknown"

    def __init__(self, x: float, y: float, hp: int, radius: float,
                 score: int, drop_chance: float, speed: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.hp = hp
        self.max_hp = hp
        self.radius = radius
        self.score = score
        self.drop_chance = drop_chance
        self.speed = speed
        self.angle = random.random() * math.pi * 2
        self.flash_timer = 0
        self.fire_timer = 0
        self.boss_drops = 1      # overridden by Boss

    def take_hit(self) -> bool:
        """Apply one hit. Returns True if enemy is destroyed."""
        self.hp -= 1
        self.flash_timer = 6
        return self.hp <= 0

    def base_update(self) -> None:
        """Common per-frame work (movement + wrapping + flash)."""
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position(self.x, self.y,
                                       LOGICAL_WIDTH, LOGICAL_HEIGHT)
        if self.flash_timer > 0:
            self.flash_timer -= 1

    # Subclasses override this
    def update(self, player_x: float, player_y: float,
               enemy_bullets: list) -> None:
        raise NotImplementedError


# ======================================================================
# Drifter
# ======================================================================

class Drifter(Enemy):
    enemy_type = "drifter"

    def __init__(self, x: float, y: float):
        super().__init__(
            x, y,
            hp=DRIFTER_HP,
            radius=DRIFTER_RADIUS,
            score=DRIFTER_SCORE,
            drop_chance=DRIFTER_DROP_CHANCE,
            speed=DRIFTER_SPEED,
        )
        self.drift_angle = random.random() * math.pi * 2
        self.drift_timer = 0

    def update(self, player_x: float, player_y: float,
               enemy_bullets: list) -> None:
        self.drift_timer += 1
        if self.drift_timer > DRIFTER_DRIFT_INTERVAL:
            self.drift_angle += random_range(-0.5, 0.5)
            self.drift_timer = 0

        self.vx = math.cos(self.drift_angle) * self.speed
        self.vy = math.sin(self.drift_angle) * self.speed
        self.base_update()


# ======================================================================
# Gunner
# ======================================================================

class Gunner(Enemy):
    enemy_type = "gunner"

    def __init__(self, x: float, y: float, tier: int):
        if tier >= 3:
            hp = random.randint(2, 3)
        elif tier >= 2:
            hp = 2
        else:
            hp = 1
        score = GUNNER_SCORE_BASE + (hp - 1) * GUNNER_SCORE_PER_HP
        super().__init__(
            x, y,
            hp=hp,
            radius=GUNNER_RADIUS,
            score=score,
            drop_chance=GUNNER_DROP_CHANCE,
            speed=GUNNER_SPEED,
        )
        self.fire_rate = random.randint(120, 180)

    def update(self, player_x: float, player_y: float,
               enemy_bullets: list) -> None:
        # Slowly rotate toward player
        desired = math.atan2(player_y - self.y, player_x - self.x)
        diff = normalize_angle(desired - self.angle)
        self.angle += max(-GUNNER_TURN_RATE, min(GUNNER_TURN_RATE, diff))

        # Slow movement toward player
        self.vx = math.cos(self.angle) * self.speed * 0.3
        self.vy = math.sin(self.angle) * self.speed * 0.3

        # Firing
        self.fire_timer += 1
        if self.fire_timer >= self.fire_rate:
            self.fire_timer = 0
            a = math.atan2(player_y - self.y, player_x - self.x)
            enemy_bullets.append(Bullet(
                self.x, self.y,
                math.cos(a) * GUNNER_BULLET_SPEED,
                math.sin(a) * GUNNER_BULLET_SPEED,
                life=300,
                radius=GUNNER_BULLET_RADIUS,
                color=COLORS["gunner"],
            ))

        self.base_update()


# ======================================================================
# Kamikaze
# ======================================================================

class Kamikaze(Enemy):
    enemy_type = "kamikaze"

    def __init__(self, x: float, y: float):
        super().__init__(
            x, y,
            hp=KAMIKAZE_HP,
            radius=KAMIKAZE_RADIUS,
            score=KAMIKAZE_SCORE,
            drop_chance=KAMIKAZE_DROP_CHANCE,
            speed=KAMIKAZE_SPEED,
        )

    def update(self, player_x: float, player_y: float,
               enemy_bullets: list) -> None:
        a = math.atan2(player_y - self.y, player_x - self.x)
        self.angle = a
        self.vx += math.cos(a) * KAMIKAZE_ACCEL
        self.vy += math.sin(a) * KAMIKAZE_ACCEL
        self.vx, self.vy = clamp_magnitude(self.vx, self.vy,
                                           KAMIKAZE_MAX_SPEED)
        self.base_update()


# ======================================================================
# Boss
# ======================================================================

class Boss(Enemy):
    enemy_type = "boss"

    def __init__(self, x: float, y: float):
        super().__init__(
            x, y,
            hp=BOSS_HP,
            radius=BOSS_RADIUS,
            score=BOSS_SCORE,
            drop_chance=BOSS_DROP_CHANCE,
            speed=BOSS_SPEED,
        )
        self.fire_rate = BOSS_FIRE_RATE
        self.boss_drops = BOSS_DROPS

    def update(self, player_x: float, player_y: float,
               enemy_bullets: list) -> None:
        # Slowly rotate toward player
        desired = math.atan2(player_y - self.y, player_x - self.x)
        diff = normalize_angle(desired - self.angle)
        self.angle += max(-BOSS_TURN_RATE, min(BOSS_TURN_RATE, diff))

        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed

        # Spread fire
        self.fire_timer += 1
        if self.fire_timer >= self.fire_rate:
            self.fire_timer = 0
            a = math.atan2(player_y - self.y, player_x - self.x)
            for offset in (-1, 0, 1):
                enemy_bullets.append(Bullet(
                    self.x, self.y,
                    math.cos(a + offset * BOSS_SPREAD) * BOSS_BULLET_SPEED,
                    math.sin(a + offset * BOSS_SPREAD) * BOSS_BULLET_SPEED,
                    life=300,
                    radius=BOSS_BULLET_RADIUS,
                    color=COLORS["boss"],
                ))

        self.base_update()


# ======================================================================
# Spawning helpers
# ======================================================================

def get_tier(game_time_frames: int) -> int:
    """Return the current difficulty tier (1–4)."""
    sec = game_time_frames / 60.0
    if sec < 30:
        return 1
    if sec < 60:
        return 2
    if sec < 90:
        return 3
    return 4


def get_max_enemies(tier: int) -> int:
    """Max enemies allowed on screen for a given tier."""
    if 1 <= tier <= 4:
        return TIER_MAX_ENEMIES[tier]
    return TIER_MAX_ENEMIES[-1]


def available_types(tier: int) -> list[str]:
    """Weighted list of enemy types available at a tier."""
    if tier == 1:
        return ["drifter"]
    if tier == 2:
        return ["drifter", "drifter", "gunner"]
    if tier == 3:
        return ["drifter", "gunner", "gunner", "kamikaze"]
    return ["drifter", "gunner", "kamikaze", "kamikaze", "boss"]


def safe_spawn_position(player_x: float, player_y: float,
                        w: float = LOGICAL_WIDTH,
                        h: float = LOGICAL_HEIGHT) -> tuple[float, float]:
    """Find a random position at least SAFE_SPAWN_RADIUS from the player."""
    for _ in range(50):
        x = random.random() * w
        y = random.random() * h
        if distance(x, y, player_x, player_y) > SAFE_SPAWN_RADIUS:
            return x, y
    # Fallback — corner
    return 0.0, 0.0


def create_enemy(enemy_type: str, x: float, y: float,
                 tier: int) -> Enemy:
    """Factory: create an enemy of the given type."""
    if enemy_type == "drifter":
        return Drifter(x, y)
    if enemy_type == "gunner":
        return Gunner(x, y, tier)
    if enemy_type == "kamikaze":
        return Kamikaze(x, y)
    if enemy_type == "boss":
        return Boss(x, y)
    return Drifter(x, y)