# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import random
import pygame

from maxbloks.tanks import position
from maxbloks.tanks import enemy
from maxbloks.tanks import constants


class EnemySpawner:
    """Handles spawning of enemies at world edges with difficulty progression."""

    def __init__(self, world_width: int, world_height: int, config: constants.EnemyConfig):
        self.world_width = world_width
        self.world_height = world_height
        self.config = config
        self.last_spawn_time = 0
        self.colors = constants.Colors()

    def should_spawn(self, current_time: int, current_count: int) -> bool:
        time_elapsed = current_time - self.last_spawn_time >= self.config.spawn_interval
        under_limit = current_count < self.config.max_enemies
        return time_elapsed and under_limit

    def spawn_enemy(self, current_time: int, enemies_killed: int) -> enemy.Enemy:
        self.last_spawn_time = current_time
        pos = self._get_random_edge_position()
        speed_multiplier = self._calculate_speed_multiplier(enemies_killed)
        return enemy.Enemy(pos, self.config, self.colors.enemy, speed_multiplier)

    def _calculate_speed_multiplier(self, enemies_killed: int) -> float:
        raw_multiplier = 1.0 + (enemies_killed * self.config.speed_increase_per_kill)
        max_multiplier = self.config.max_speed / self.config.base_speed
        return min(raw_multiplier, max_multiplier)

    def get_current_enemy_speed(self, enemies_killed: int) -> float:
        multiplier = self._calculate_speed_multiplier(enemies_killed)
        return self.config.base_speed * multiplier

    def _get_random_edge_position(self) -> position.Position:
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        margin = 50

        if edge == 'top':
            return position.Position(random.randint(margin, self.world_width - margin), margin)
        elif edge == 'bottom':
            return position.Position(random.randint(margin, self.world_width - margin),
                                     self.world_height - margin)
        elif edge == 'left':
            return position.Position(margin, random.randint(margin, self.world_height - margin))
        else:
            return position.Position(self.world_width - margin,
                                     random.randint(margin, self.world_height - margin))
