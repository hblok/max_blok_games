# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import pygame

from maxbloks.tanks import render
from maxbloks.tanks import constants
from maxbloks.tanks import camera as camera_module
from maxbloks.tanks import position


class TestRender(unittest.TestCase):

    def setUp(self):
        pygame.init()
        self.display = constants.DisplayConfig()
        self.colors = constants.Colors()
        self.screen = pygame.Surface((self.display.width, self.display.height))
        self.renderer = render.Renderer(self.display, self.colors, type('UIStub', (), {
            'render_hud': lambda *args, **kwargs: None,
            'render_weapon_info': lambda *args, **kwargs: None,
            'render_game_over': lambda *args, **kwargs: None,
        })())
        self.camera = camera_module.Camera(self.display.width, self.display.height, 2400, 1800)

        class ObstacleStub(pygame.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.world_position = position.Position(x, y)
                self.image = pygame.Surface((20, 20))
                self.image.fill((100, 100, 100))
                self.rect = self.image.get_rect(center=(x, y))

            def get_world_rect(self):
                return self.rect

        class HealthStub(pygame.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.world_position = position.Position(x, y)
                self.image = pygame.Surface((16, 16))
                self.image.fill((0, 255, 0))
                self.rect = self.image.get_rect(center=(x, y))
                self.collision_radius = 8
                self.active = True

            def get_world_rect(self):
                return self.rect

        class PickupStub(pygame.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.world_position = position.Position(x, y)
                self.image = pygame.Surface((16, 16))
                self.image.fill((255, 200, 0))
                self.rect = self.image.get_rect(center=(x, y))
                self.collision_radius = 8

            def get_world_rect(self):
                return self.rect

        class TankStub(pygame.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.world_position = position.Position(x, y)
                self.image = pygame.Surface((32, 32))
                self.image.fill((50, 150, 50))
                self.rect = self.image.get_rect(center=(x, y))

        class EnemyStub(pygame.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.world_position = position.Position(x, y)
                self.image = pygame.Surface((22, 22))
                self.image.fill((200, 50, 50))
                self.rect = self.image.get_rect(center=(x, y))

        self.world = type('WorldStub', (), {
            'obstacles': [ObstacleStub(200, 200)],
            'health_packs': [HealthStub(220, 200)],
            'weapon_pickups': [PickupStub(240, 200)],
        })()

        self.tank = TankStub(260, 200)
        self.enemies = pygame.sprite.Group(EnemyStub(280, 200))
        self.projectiles = pygame.sprite.Group()
        self.camera.update(position.Position(260, 200))

    def tearDown(self):
        pygame.quit()

    def test_render_frame(self):
        self.renderer.render_frame(
            screen=self.screen,
            camera=self.camera,
            world=self.world,
            tank=self.tank,
            enemies=self.enemies,
            projectiles=self.projectiles,
            gs=type('S', (), {'name': 'PLAYING'})(),
            stats=type('ST', (), {'score': 0})(),
            weapon_manager=type('WM', (), {
                'get_weapon_type': lambda *_: 'default',
                'get_time_remaining': lambda *_: 0.0,
            })(),
            current_time=0
        )
