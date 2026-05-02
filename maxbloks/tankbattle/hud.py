# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Heads-up display drawing for TankBattle."""

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import entities


class Hud:
    """Draw screen-space HUD elements."""

    def __init__(self, pygame_module):
        self.pygame = pygame_module
        self.font = pygame_module.font.Font(None, constants.HUD_FONT_SIZE)
        self.small_font = pygame_module.font.Font(None, constants.SMALL_FONT_SIZE)
        self.minimap_surface = pygame_module.Surface(
            (constants.HUD_MINIMAP_WIDTH, constants.HUD_MINIMAP_HEIGHT),
            pygame_module.SRCALPHA,
        )

    def draw(self, screen, game):
        """Draw all HUD elements."""
        self._draw_hp(screen, game.local_tank)
        self._draw_weapon(screen, game.local_tank)
        self._draw_round_pips(screen, game.round_wins)
        self._draw_timer(screen, game)
        self._draw_minimap(screen, game)

    def _draw_hp(self, screen, tank):
        for index in range(constants.TANK_MAX_HP):
            x_value = constants.HUD_HP_X + index * (
                constants.HUD_HP_SEGMENT_WIDTH + constants.HUD_HP_SEGMENT_GAP
            )
            rect = (
                x_value,
                constants.HUD_HP_Y,
                constants.HUD_HP_SEGMENT_WIDTH,
                constants.HUD_HP_SEGMENT_HEIGHT,
            )
            color = constants.COLOR_GREEN if index < tank.hp else constants.COLOR_DARK_GREY
            self.pygame.draw.rect(screen, color, rect)
            self.pygame.draw.rect(screen, constants.COLOR_WHITE, rect, 1)

    def _draw_weapon(self, screen, tank):
        text = tank.active_weapon.value.replace("_", " ").upper()
        surface = self.small_font.render(text, True, constants.COLOR_WHITE)
        rect = surface.get_rect(center=(constants.HUD_WEAPON_X, constants.HUD_WEAPON_Y))
        screen.blit(surface, rect)
        if tank.active_weapon != entities.WeaponType.PRIMARY:
            width = int(80 * (tank.weapon_timer / constants.WEAPON_DURATION))
            self.pygame.draw.rect(screen, constants.COLOR_DARK_GREY, (constants.HUD_WEAPON_X - 40, constants.HUD_WEAPON_Y + 12, 80, 5))
            self.pygame.draw.rect(screen, constants.COLOR_YELLOW, (constants.HUD_WEAPON_X - 40, constants.HUD_WEAPON_Y + 12, width, 5))
            if tank.weapon_shots > 0:
                shots = self.small_font.render(str(tank.weapon_shots), True, constants.COLOR_WHITE)
                screen.blit(shots, (constants.HUD_WEAPON_X + 48, constants.HUD_WEAPON_Y + 4))

    def _draw_round_pips(self, screen, wins):
        for player in range(2):
            for pip in range(constants.ROUNDS_TO_WIN):
                x_value = constants.HUD_ROUND_X + pip * constants.HUD_PIP_RADIUS * 3
                y_value = constants.HUD_ROUND_Y + player * constants.HUD_PIP_RADIUS * 3
                color = constants.COLOR_GREEN if player == 0 else constants.COLOR_RED
                if pip >= wins[player]:
                    color = constants.COLOR_DARK_GREY
                self.pygame.draw.circle(screen, color, (x_value, y_value), constants.HUD_PIP_RADIUS)

    def _draw_timer(self, screen, game):
        text = str(int(max(0.0, game.round_time_remaining)))
        if game.sudden_death:
            text = "SUDDEN DEATH"
        surface = self.small_font.render(text, True, constants.COLOR_WHITE)
        rect = surface.get_rect(center=(constants.HUD_WEAPON_X, constants.HUD_TIMER_Y))
        screen.blit(surface, rect)

    def _draw_minimap(self, screen, game):
        self.minimap_surface.fill((0, 0, 0, 130))
        self.pygame.draw.rect(
            self.minimap_surface,
            constants.COLOR_WHITE,
            (0, 0, constants.HUD_MINIMAP_WIDTH - 1, constants.HUD_MINIMAP_HEIGHT - 1),
            1,
        )
        for tile_x, tile_y in game.arena.hard_tiles:
            x_value = int(tile_x * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_X)
            y_value = int(tile_y * constants.TILE_SIZE * constants.HUD_MINIMAP_SCALE_Y)
            self.minimap_surface.set_at((min(x_value, constants.HUD_MINIMAP_WIDTH - 1), min(y_value, constants.HUD_MINIMAP_HEIGHT - 1)), constants.COLOR_DARK_GREY)
        self._draw_tank_dot(game.tanks[0], constants.COLOR_GREEN)
        self._draw_tank_dot(game.tanks[1], constants.COLOR_RED)
        screen.blit(self.minimap_surface, (constants.HUD_MINIMAP_X, constants.HUD_MINIMAP_Y))

    def _draw_tank_dot(self, tank, color):
        x_value = int(tank.x * constants.HUD_MINIMAP_SCALE_X)
        y_value = int(tank.y * constants.HUD_MINIMAP_SCALE_Y)
        self.pygame.draw.circle(self.minimap_surface, color, (x_value, y_value), 2)
