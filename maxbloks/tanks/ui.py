# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame

from maxbloks.tanks import weapons
from maxbloks.tanks import constants


class UI:
    """Handles all UI rendering."""

    def __init__(self, display_config):
        self.display_config = display_config
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

    def render_hud(self, screen: pygame.Surface, score: int, tank):
        """Render the HUD: score (top-left), health bar (bottom-left)."""
        margin = 10
        score_text = self.font_medium.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (margin, margin))
        self._draw_health_bar(screen, tank, margin)

    def _draw_health_bar(self, screen: pygame.Surface, tank, margin: int):
        bar_width = 200
        bar_height = 20
        bar_x = margin
        bar_y = self.display_config.height - margin - bar_height

        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))

        health_ratio = max(0, tank.health / tank.config.max_health)
        current_width = int(bar_width * health_ratio)

        health_color = (0, 200, 0) if health_ratio > 0.3 else (200, 0, 0)
        if current_width > 0:
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, current_width, bar_height))

        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

    def render_weapon_info(self, screen: pygame.Surface, weapon_type: str, time_remaining: float):
        """Render weapon icon (top-right) and duration bar."""
        margin = 10
        icon_size = 40
        icon_x = self.display_config.width - margin - icon_size
        icon_y = margin
        self._draw_weapon_icon(screen, weapon_type, icon_x, icon_y, icon_size)

        if weapon_type != weapons.WeaponType.DEFAULT and time_remaining > 0:
            self._draw_weapon_bar(screen, time_remaining, margin, icon_y + icon_size + 10)

    def _draw_weapon_icon(self, screen: pygame.Surface, weapon_type: str,
                          x: int, y: int, size: int):
        pygame.draw.rect(screen, (40, 40, 40), (x, y, size, size))
        pygame.draw.rect(screen, (255, 255, 255), (x, y, size, size), 2)

        center_x = x + size // 2
        center_y = y + size // 2

        if weapon_type == weapons.WeaponType.DEFAULT:
            pygame.draw.circle(screen, (255, 255, 100), (center_x, center_y), size // 4)

        elif weapon_type == weapons.WeaponType.FASTER_SHOOTER:
            offset = size // 5
            pygame.draw.circle(screen, (255, 255, 0), (center_x - offset, center_y), size // 8)
            pygame.draw.circle(screen, (255, 255, 0), (center_x, center_y), size // 8)
            pygame.draw.circle(screen, (255, 255, 0), (center_x + offset, center_y), size // 8)

        elif weapon_type == weapons.WeaponType.LASER:
            line_y = center_y
            line_start_x = x + size // 6
            line_end_x = x + size - size // 6
            pygame.draw.line(screen, (255, 50, 50), (line_start_x, line_y), (line_end_x, line_y), 4)
            pygame.draw.line(screen, (255, 150, 150), (line_start_x, line_y), (line_end_x, line_y), 2)

        elif weapon_type == weapons.WeaponType.SPRAY_SHOOTER:
            fan_base_x = center_x
            fan_base_y = y + size - size // 6
            fan_tip_y = y + size // 6
            pygame.draw.line(screen, (0, 255, 255), (fan_base_x, fan_base_y), (center_x - size // 4, fan_tip_y), 2)
            pygame.draw.line(screen, (0, 255, 255), (fan_base_x, fan_base_y), (center_x, fan_tip_y), 2)
            pygame.draw.line(screen, (0, 255, 255), (fan_base_x, fan_base_y), (center_x + size // 4, fan_tip_y), 2)

        elif weapon_type == weapons.WeaponType.BOMBS:
            pygame.draw.circle(screen, (50, 50, 50), (center_x, center_y + 2), size // 3)
            pygame.draw.circle(screen, (255, 100, 0), (center_x, center_y + 2), size // 3 - 2)
            pygame.draw.line(screen, (200, 200, 0),
                             (center_x, center_y - size // 3), (center_x, y + 4), 2)

    def _draw_weapon_bar(self, screen: pygame.Surface, time_remaining_sec: float,
                         margin: int, start_y: int):
        game_config = constants.GameConfig()
        max_duration_ms = getattr(game_config, "weapon_duration", 15000)
        max_duration_sec = max(0.001, max_duration_ms / 1000.0)

        bar_width = 20
        bar_height = 150
        bar_x = self.display_config.width - margin - bar_width
        bar_y = start_y

        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))

        time_ratio = max(0.0, min(1.0, time_remaining_sec / max_duration_sec))
        current_height = int(bar_height * time_ratio)
        if current_height > 0:
            fill_y = bar_y + bar_height - current_height
            pygame.draw.rect(screen, (100, 150, 255), (bar_x, fill_y, bar_width, current_height))

        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

    def render_game_over(self, screen: pygame.Surface, victory: bool, score: int):
        overlay = pygame.Surface((self.display_config.width, self.display_config.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        if victory:
            message = "VICTORY!"
            color = (0, 255, 0)
        else:
            message = "GAME OVER"
            color = (255, 0, 0)

        text = self.font_large.render(message, True, color)
        text_rect = text.get_rect(center=(self.display_config.width // 2,
                                          self.display_config.height // 2 - 50))
        screen.blit(text, text_rect)

        score_text = self.font_medium.render(f"Final Score: {score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.display_config.width // 2,
                                                  self.display_config.height // 2 + 20))
        screen.blit(score_text, score_rect)

        restart_text = self.font_small.render("Press B to restart", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(self.display_config.width // 2,
                                                      self.display_config.height // 2 + 80))
        screen.blit(restart_text, restart_rect)
