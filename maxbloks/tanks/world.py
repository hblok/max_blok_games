# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
import random
from typing import Set

from maxbloks.tanks import position
from maxbloks.tanks import obstacles
from maxbloks.tanks import weapons


class World:
    """Game world with obstacles, items, and weapon pickups."""

    def __init__(self, world_config, obstacle_config, health_pack_config,
                 weapon_pickup_config, colors):
        self.config = world_config
        self.obstacle_config = obstacle_config
        self.health_pack_config = health_pack_config
        self.weapon_pickup_config = weapon_pickup_config
        self.colors = colors

        self.obstacles: Set = set()
        self.health_packs: Set = set()
        self.weapon_pickups: Set = set()

        self._generate_world()

    def _generate_world(self):
        self._generate_border_rocks()
        self._generate_rock_clusters()
        self._generate_mountains()
        self._generate_health_packs()
        self._generate_weapon_pickups()

    def _generate_border_rocks(self):
        border_margin = 50
        spacing = 100

        for x in range(0, self.config.width, spacing):
            if random.random() > 0.3:
                pos = position.Position(x, border_margin)
                self.obstacles.add(obstacles.Rock(pos, self.obstacle_config, self.colors))
            if random.random() > 0.3:
                pos = position.Position(x, self.config.height - border_margin)
                self.obstacles.add(obstacles.Rock(pos, self.obstacle_config, self.colors))

        for y in range(0, self.config.height, spacing):
            if random.random() > 0.3:
                pos = position.Position(border_margin, y)
                self.obstacles.add(obstacles.Rock(pos, self.obstacle_config, self.colors))
            if random.random() > 0.3:
                pos = position.Position(self.config.width - border_margin, y)
                self.obstacles.add(obstacles.Rock(pos, self.obstacle_config, self.colors))

    def _generate_rock_clusters(self):
        center_x = self.config.width // 2
        center_y = self.config.height // 2
        safe_radius = 200

        for _ in range(self.config.num_rock_clusters):
            cluster_x = random.randint(100, self.config.width - 100)
            cluster_y = random.randint(100, self.config.height - 100)

            dist_to_center = ((cluster_x - center_x) ** 2 + (cluster_y - center_y) ** 2) ** 0.5
            if dist_to_center < safe_radius:
                continue

            for _ in range(self.obstacle_config.rocks_per_cluster):
                offset_x = random.randint(-self.obstacle_config.cluster_spread,
                                          self.obstacle_config.cluster_spread)
                offset_y = random.randint(-self.obstacle_config.cluster_spread,
                                          self.obstacle_config.cluster_spread)
                pos = position.Position(cluster_x + offset_x, cluster_y + offset_y)
                self.obstacles.add(obstacles.Rock(pos, self.obstacle_config, self.colors))

    def _generate_mountains(self):
        for _ in range(self.config.num_mountains):
            x = random.randint(200, self.config.width - 200)
            y = random.randint(200, self.config.height - 200)
            pos = position.Position(x, y)
            self.obstacles.add(obstacles.MountainFormation(pos, self.obstacle_config, self.colors))

    def _generate_health_packs(self):
        for _ in range(self.config.num_health_packs):
            x = random.randint(100, self.config.width - 100)
            y = random.randint(100, self.config.height - 100)
            pos = position.Position(x, y)
            self.health_packs.add(obstacles.HealthPack(pos, self.health_pack_config, self.colors))

    def _generate_weapon_pickups(self):
        weapon_types = [
            weapons.WeaponType.FASTER_SHOOTER,
            weapons.WeaponType.LASER,
            weapons.WeaponType.SPRAY_SHOOTER,
            weapons.WeaponType.BOMBS,
        ]
        for i in range(self.config.num_weapon_pickups):
            x = random.randint(100, self.config.width - 100)
            y = random.randint(100, self.config.height - 100)
            pos = position.Position(x, y)
            weapon_type = weapon_types[i % len(weapon_types)]
            self.weapon_pickups.add(
                weapons.WeaponPickup(pos, weapon_type, self.weapon_pickup_config, self.colors)
            )

    def check_collision_with_obstacles(self, pos: position.Position, radius: float) -> bool:
        """Check if a position overlaps with any obstacle."""
        for obstacle in self.obstacles:
            dist = pos.distance_to(obstacle.world_position)
            if dist < radius + obstacle.collision_radius:
                return True
        return False

    def get_collision_pushback(self, pos: position.Position, radius: float) -> position.Position:
        """Return a pushback vector if pos overlaps an obstacle, else (0, 0)."""
        for obstacle in self.obstacles:
            dist = pos.distance_to(obstacle.world_position)
            overlap = radius + obstacle.collision_radius - dist
            if overlap > 0 and dist > 0:
                dx = pos.x - obstacle.world_position.x
                dy = pos.y - obstacle.world_position.y
                return position.Position(
                    (dx / dist) * overlap,
                    (dy / dist) * overlap
                )
        return position.Position(0, 0)
