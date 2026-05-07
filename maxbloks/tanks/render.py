# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame

from maxbloks.tanks import game_state
from maxbloks.tanks import position


class Renderer:
    """Responsible for rendering the entire frame."""

    def __init__(self, display_config, colors, ui):
        self.display_config = display_config
        self.colors = colors
        self.ui = ui

    def render_frame(
        self,
        screen: pygame.Surface,
        camera,
        world,
        tank,
        enemies: pygame.sprite.Group,
        projectiles: pygame.sprite.Group,
        gs: game_state.GameState,
        stats,
        weapon_manager,
        current_time: int,
    ):
        """Draw one frame to the screen."""
        screen.fill(self.colors.background)
        self._draw_grid(screen, camera)

        self._draw_obstacles(screen, camera, world)
        self._draw_health_packs(screen, camera, world)
        self._draw_weapon_pickups(screen, camera, world)

        self._draw_enemies(screen, camera, enemies)
        self._draw_projectiles(screen, camera, projectiles)
        self._draw_tank(screen, camera, tank)

        self._draw_ui(screen, gs, stats, tank, weapon_manager, current_time)

        disp_surface = pygame.display.get_surface()
        if disp_surface is not None and screen is disp_surface:
            pygame.display.flip()

    def _draw_grid(self, screen: pygame.Surface, camera):
        viewport = camera.get_viewport_rect()
        grid_size = 50

        start_x = (viewport.x // grid_size) * grid_size
        start_y = (viewport.y // grid_size) * grid_size

        for x in range(start_x, viewport.x + viewport.width + grid_size, grid_size):
            screen_x = x - viewport.x
            pygame.draw.line(screen, self.colors.grid,
                             (screen_x, 0), (screen_x, self.display_config.height), 1)

        for y in range(start_y, viewport.y + viewport.height + grid_size, grid_size):
            screen_y = y - viewport.y
            pygame.draw.line(screen, self.colors.grid,
                             (0, screen_y), (self.display_config.width, screen_y), 1)

    def _draw_obstacles(self, screen: pygame.Surface, camera, world):
        for obstacle in world.obstacles:
            if camera.is_rect_visible(obstacle.get_world_rect()):
                screen_pos = camera.apply(obstacle.world_position)
                rect = obstacle.image.get_rect(center=screen_pos.to_tuple())
                screen.blit(obstacle.image, rect)

    def _draw_health_packs(self, screen: pygame.Surface, camera, world):
        for health_pack in world.health_packs:
            if health_pack.active and camera.is_rect_visible(health_pack.get_world_rect()):
                screen_pos = camera.apply(health_pack.world_position)
                rect = health_pack.image.get_rect(center=screen_pos.to_tuple())
                screen.blit(health_pack.image, rect)

    def _draw_weapon_pickups(self, screen: pygame.Surface, camera, world):
        for pickup in world.weapon_pickups:
            if camera.is_rect_visible(pickup.get_world_rect()):
                screen_pos = camera.apply(pickup.world_position)
                rect = pickup.image.get_rect(center=screen_pos.to_tuple())
                screen.blit(pickup.image, rect)

    def _draw_enemies(self, screen: pygame.Surface, camera, enemies: pygame.sprite.Group):
        for enemy in enemies:
            if camera.is_visible(enemy.world_position):
                screen_pos = camera.apply(enemy.world_position)
                rect = enemy.image.get_rect(center=screen_pos.to_tuple())
                screen.blit(enemy.image, rect)

    def _draw_projectiles(self, screen: pygame.Surface, camera, projectiles: pygame.sprite.Group):
        """Draw all projectiles including laser beams."""
        for proj in projectiles:
            if hasattr(proj, 'start') and hasattr(proj, 'end'):
                if camera.is_visible(proj.start) or camera.is_visible(proj.end):
                    world_center = position.Position(proj.rect.centerx, proj.rect.centery)
                    screen_pos = camera.apply(world_center)
                    rect = proj.image.get_rect(center=screen_pos.to_tuple())
                    screen.blit(proj.image, rect)
            else:
                if camera.is_visible(proj.world_position):
                    screen_pos = camera.apply(proj.world_position)
                    rect = proj.image.get_rect(center=screen_pos.to_tuple())
                    screen.blit(proj.image, rect)

    def _draw_tank(self, screen: pygame.Surface, camera, tank):
        if camera.is_visible(tank.world_position):
            screen_pos = camera.apply(tank.world_position)
            rect = tank.image.get_rect(center=screen_pos.to_tuple())
            screen.blit(tank.image, rect)

    def _draw_ui(self, screen: pygame.Surface, gs: game_state.GameState, stats, tank,
                 weapon_manager, current_time: int):
        if gs == game_state.GameState.PLAYING:
            self.ui.render_hud(screen, stats.score, tank)
            self.ui.render_weapon_info(
                screen,
                weapon_manager.get_weapon_type(),
                weapon_manager.get_time_remaining(current_time),
            )
        elif gs == game_state.GameState.GAME_OVER:
            self.ui.render_hud(screen, stats.score, tank)
            self.ui.render_game_over(screen, False, stats.score)
        elif gs == game_state.GameState.VICTORY:
            self.ui.render_hud(screen, stats.score, tank)
            self.ui.render_game_over(screen, True, stats.score)
