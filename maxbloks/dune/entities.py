# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import math
import pygame

from maxbloks.dune import constants, utils


class Player:
    """Player-controlled character moving across the desert."""

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = 12
        self.color = constants.BLUE

    def update(self, movement_x, movement_y, screen_width, screen_height):
        dx, dy = utils.normalize(movement_x, movement_y)
        self.x += dx * constants.PLAYER_SPEED
        self.y += dy * constants.PLAYER_SPEED
        self.x = utils.clamp(self.x, self.size, screen_width - self.size)
        self.y = utils.clamp(self.y, self.size, screen_height - self.size)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

    def collides_with(self, other):
        return utils.distance(self.x, self.y, other.x, other.y) < self.size + other.size
