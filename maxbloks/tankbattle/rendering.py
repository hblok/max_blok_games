# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Rendering helpers for TankBattle."""

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities
from maxbloks.tankbattle import utils


class Renderer:
    """Draw world, tanks, menus, and state overlays."""

    def __init__(self, pygame_module, screen):
        self.pygame = pygame_module
        self.screen = screen
        self.font_menu = pygame_module.font.Font(None, constants.MENU_FONT_SIZE)
        self.font_big = pygame_module.font.Font(None, constants.BIG_FONT_SIZE)
        self.font_small = pygame_module.font.Font(None, constants.SMALL_FONT_SIZE)
        self.terrain_surface = pygame_module.Surface(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        )
        self.terrain_surface.fill(constants.COLOR_BG)

    def draw_world(self, game):
        """Draw arena and active world entities."""
        self.screen.blit(self.terrain_surface, (0, 0))
        camera = game.arena.clamp_camera(game.local_tank.position)
        for obstacle in game.arena.obstacles:
            self._draw_obstacle(game, obstacle, camera)
        for powerup in game.powerups:
            self._draw_circle_world(game, powerup.position, constants.COLOR_YELLOW, 8, camera)
        for mine in game.mines:
            self._draw_circle_world(game, mine.position, constants.COLOR_ORANGE, 6, camera)
        for bullet in game.bullets:
            self._draw_circle_world(game, bullet.position, constants.COLOR_WHITE, 3, camera)
        self._draw_tank(game, game.tanks[0], constants.COLOR_GREEN, camera)
        self._draw_tank(game, game.tanks[1], constants.COLOR_RED, camera)

    def _draw_obstacle(self, game, obstacle, camera):
        if obstacle.is_destroyed:
            return
        x_value, y_value = game.arena.world_to_screen(
            (
                obstacle.tile_x * constants.TILE_SIZE,
                obstacle.tile_y * constants.TILE_SIZE,
            ),
            camera,
        )
        color = constants.COLOR_HARD
        if obstacle.type == entities.ObstacleType.SOFT:
            color = constants.COLOR_SOFT
        self.pygame.draw.rect(
            self.screen,
            color,
            (x_value, y_value, constants.TILE_SIZE, constants.TILE_SIZE),
        )

    def _draw_circle_world(self, game, position, color, radius, camera):
        screen_pos = game.arena.world_to_screen(position, camera)
        self.pygame.draw.circle(
            self.screen,
            color,
            (int(screen_pos[0]), int(screen_pos[1])),
            radius,
        )

    def _draw_tank(self, game, tank, color, camera):
        screen_pos = game.arena.world_to_screen(tank.position, camera)
        draw_color = constants.COLOR_WHITE if tank.hit_flash_timer > 0.0 else color
        center = (int(screen_pos[0]), int(screen_pos[1]))
        self.pygame.draw.circle(
            self.screen,
            draw_color,
            center,
            int(constants.TANK_HITBOX_RADIUS),
        )
        dx_value, dy_value = utils.angle_to_vector(tank.turret_angle)
        end = (
            int(screen_pos[0] + dx_value * constants.TANK_BODY_HEIGHT),
            int(screen_pos[1] + dy_value * constants.TANK_BODY_HEIGHT),
        )
        self.pygame.draw.line(
            self.screen,
            constants.COLOR_BLACK,
            center,
            end,
            constants.TANK_TURRET_WIDTH,
        )

    def draw_menu(self, menu_index):
        """Draw main menu."""
        self.screen.fill(constants.COLOR_BLACK)
        title = self.font_big.render("Tank Battle", True, constants.COLOR_GREEN)
        self.screen.blit(title, title.get_rect(center=(constants.SCREEN_WIDTH // 2, 120)))
        for index, item in enumerate(constants.MENU_ITEMS):
            color = constants.COLOR_YELLOW if index == menu_index else constants.COLOR_WHITE
            surface = self.font_menu.render(item, True, color)
            self.screen.blit(
                surface,
                surface.get_rect(center=(constants.SCREEN_WIDTH // 2, 220 + index * 44)),
            )

    def draw_center_text(self, message, color=constants.COLOR_WHITE):
        """Draw centered menu-sized text."""
        self.screen.fill(constants.COLOR_BLACK)
        text = self.font_menu.render(message, True, color)
        self.screen.blit(
            text,
            text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2)),
        )

    def draw_countdown(self, game):
        """Draw countdown overlay on top of world."""
        self.draw_world(game)
        value = max(0, int(game.state_timer) + 1)
        label = "GO!" if value == 0 else str(value)
        text = self.font_big.render(label, True, constants.COLOR_YELLOW)
        self.screen.blit(
            text,
            text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2)),
        )

    def draw_paused(self, game):
        """Draw paused overlay."""
        game.draw_playing()
        text = self.font_menu.render("Paused", True, constants.COLOR_YELLOW)
        self.screen.blit(
            text,
            text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2)),
        )

    def draw_round_over(self, game):
        """Draw round-over overlay."""
        self.draw_world(game)
        text = self.font_menu.render("Round Over", True, constants.COLOR_YELLOW)
        self.screen.blit(
            text,
            text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2)),
        )

    def draw_match_over(self, wins):
        """Draw match winner."""
        self.screen.fill(constants.COLOR_BLACK)
        winner = 1 if wins[0] > wins[1] else 2
        message = f"Player {winner} wins the match!"
        text = self.font_menu.render(message, True, constants.COLOR_YELLOW)
        self.screen.blit(
            text,
            text.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2)),
        )