# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
import random
import math

from maxbloks.tanks import position
from maxbloks.tanks import constants


class Obstacle(pygame.sprite.Sprite):
    """Base class for obstacles that block movement."""

    def __init__(self, pos: position.Position, size: int):
        super().__init__()
        self.world_position = pos
        self.size = size
        self.collision_radius = size / 2

    def get_world_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.world_position.x - self.size / 2),
            int(self.world_position.y - self.size / 2),
            self.size,
            self.size
        )


class Rock(Obstacle):
    """Rock obstacle with irregular, natural-looking shape."""

    def __init__(self, pos: position.Position, config: constants.ObstacleConfig,
                 colors: constants.Colors):
        size = random.randint(config.rock_min_size, config.rock_max_size)
        super().__init__(pos, size)
        self.config = config
        self.colors = colors
        self._create_surface()

    def _create_surface(self):
        padding = 10
        surface_size = self.size + padding * 2
        self.image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

        center = surface_size // 2
        num_points = random.randint(6, 10)
        points = self._generate_irregular_polygon(center, self.size / 2, num_points)

        pygame.draw.polygon(self.image, self.colors.rock_dark, points)

        highlight_points = self._offset_points(points, -3, -3)
        pygame.draw.polygon(self.image, self.colors.rock_light, highlight_points, 3)

        self._add_rock_details(center)

        self.rect = self.image.get_rect(
            center=(int(self.world_position.x), int(self.world_position.y))
        )

    def _generate_irregular_polygon(self, center: int, radius: float, num_points: int) -> list:
        points = []
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            random_radius = radius * random.uniform(0.7, 1.0)
            x = center + math.cos(angle) * random_radius
            y = center + math.sin(angle) * random_radius
            points.append((int(x), int(y)))
        return points

    def _offset_points(self, points: list, offset_x: int, offset_y: int) -> list:
        return [(p[0] + offset_x, p[1] + offset_y) for p in points]

    def _add_rock_details(self, center: int):
        detail_color = pygame.Color(60, 60, 60)
        for _ in range(random.randint(1, 3)):
            start_x = center + random.randint(-self.size // 4, self.size // 4)
            start_y = center + random.randint(-self.size // 4, self.size // 4)
            end_x = start_x + random.randint(-15, 15)
            end_y = start_y + random.randint(-15, 15)
            pygame.draw.line(self.image, detail_color,
                             (start_x, start_y), (end_x, end_y), 2)


class MountainFormation(Obstacle):
    """Larger mountain formation made of multiple connected peaks."""

    def __init__(self, pos: position.Position, config: constants.ObstacleConfig,
                 colors: constants.Colors):
        size = random.randint(config.rock_max_size, config.rock_max_size + 40)
        super().__init__(pos, size)
        self.config = config
        self.colors = colors
        self._create_surface()

    def _create_surface(self):
        padding = 15
        surface_size = self.size + padding * 2
        self.image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

        center = surface_size // 2
        num_peaks = random.randint(2, 4)
        for i in range(num_peaks):
            self._draw_peak(center, i, num_peaks)

        self.rect = self.image.get_rect(
            center=(int(self.world_position.x), int(self.world_position.y))
        )

    def _draw_peak(self, center: int, peak_index: int, total_peaks: int):
        offset_x = (peak_index - total_peaks / 2) * 15
        peak_height = random.randint(self.size // 2, self.size * 2 // 3)
        peak_width = random.randint(self.size // 3, self.size // 2)

        peak_top = (int(center + offset_x), int(center - peak_height // 2))
        peak_left = (int(center + offset_x - peak_width // 2), int(center + peak_height // 2))
        peak_right = (int(center + offset_x + peak_width // 2), int(center + peak_height // 2))

        pygame.draw.polygon(self.image, self.colors.rock_dark, [peak_top, peak_left, peak_right])

        lighter_color = pygame.Color(
            min(255, self.colors.rock_dark.r + 30),
            min(255, self.colors.rock_dark.g + 30),
            min(255, self.colors.rock_dark.b + 30)
        )
        pygame.draw.polygon(self.image, lighter_color,
                            [peak_top, peak_right, (peak_right[0], peak_right[1] - 5)], 0)


class HealthPack(pygame.sprite.Sprite):
    """Health pack that restores tank health when collected."""

    def __init__(self, pos: position.Position, config, colors: constants.Colors):
        super().__init__()
        self.world_position = pos
        self.config = config
        self.colors = colors
        self.active = True
        self.respawn_time = 0

        self._create_surface()
        self.rect = self.image.get_rect(
            center=(int(self.world_position.x), int(self.world_position.y))
        )
        self.collision_radius = config.size / 2

    def _create_surface(self):
        size = self.config.size
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)

        center = size // 2
        pygame.draw.circle(self.image, self.colors.health_pack, (center, center), center)

        cross_thickness = size // 5
        cross_length = size * 2 // 3
        pygame.draw.rect(self.image, self.colors.health_pack_cross,
                         (center - cross_length // 2, center - cross_thickness // 2,
                          cross_length, cross_thickness))
        pygame.draw.rect(self.image, self.colors.health_pack_cross,
                         (center - cross_thickness // 2, center - cross_length // 2,
                          cross_thickness, cross_length))
        pygame.draw.circle(self.image, pygame.Color(180, 40, 40), (center, center), center, 2)

    def collect(self, current_time: int) -> int:
        if not self.active:
            return 0
        self.active = False
        self.respawn_time = current_time + self.config.respawn_time
        return self.config.heal_amount

    def update(self, current_time: int):
        if not self.active and current_time >= self.respawn_time:
            self.active = True

    def get_world_rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.world_position.x - self.config.size / 2),
            int(self.world_position.y - self.config.size / 2),
            self.config.size,
            self.config.size
        )
