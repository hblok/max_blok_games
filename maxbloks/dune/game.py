# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import enum
import logging
import pygame

from maxbloks.dune import compat_sdl, constants, entities

logger = logging.getLogger(__name__)


class GameState(enum.Enum):
    MENU = enum.auto()
    PLAYING = enum.auto()
    PAUSED = enum.auto()
    GAME_OVER = enum.auto()


class DuneGame:
    """Desert survival game with state machine architecture."""

    def __init__(self):
        self.screen, self.display_info = compat_sdl.init_display(
            size=(constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT),
            fullscreen=constants.FULLSCREEN,
            vsync=True,
        )
        pygame.display.set_caption("Dune")
        self._font = None
        self._clock = pygame.time.Clock()
        self.state = GameState.MENU
        self._reset_game()

    def _reset_game(self):
        self.score = 0
        self.player = entities.Player(
            constants.LOGICAL_WIDTH // 2,
            constants.LOGICAL_HEIGHT // 2,
        )

    def run(self):
        running = True
        while running:
            running = self._handle_events()
            self._update()
            self._draw()
            pygame.display.flip()
            self._clock.tick(constants.TARGET_FPS)
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state in (GameState.PAUSED, GameState.MENU, GameState.GAME_OVER):
                        return False
                elif event.key == pygame.K_RETURN:
                    self._on_confirm()
        return True

    def _on_confirm(self):
        if self.state == GameState.MENU:
            self.state = GameState.PLAYING
            self._reset_game()
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
        elif self.state == GameState.GAME_OVER:
            self.state = GameState.MENU

    def _update(self):
        if self.state != GameState.PLAYING:
            return
        keys = pygame.key.get_pressed()
        mx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        my = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.player.update(mx, my, constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT)

    def _draw(self):
        self.screen.fill(constants.SAND)
        if self.state == GameState.MENU:
            self._draw_menu()
        elif self.state == GameState.PLAYING:
            self._draw_playing()
        elif self.state == GameState.PAUSED:
            self._draw_playing()
            self._draw_overlay("PAUSED", "Press Enter to resume")
        elif self.state == GameState.GAME_OVER:
            self._draw_overlay("GAME OVER", f"Score: {self.score}  |  Enter to continue")

    def _draw_playing(self):
        self.player.draw(self.screen)
        self._draw_text(f"Score: {self.score}", 8, 8, 20, constants.BLACK)

    def _draw_menu(self):
        self._draw_text("DUNE", constants.LOGICAL_WIDTH // 2 - 40, constants.LOGICAL_HEIGHT // 2 - 40, 48, constants.DARK_SAND)
        self._draw_text("Press Enter to start", constants.LOGICAL_WIDTH // 2 - 100, constants.LOGICAL_HEIGHT // 2 + 20, 20, constants.BLACK)

    def _draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        self._draw_text(title, constants.LOGICAL_WIDTH // 2 - 60, constants.LOGICAL_HEIGHT // 2 - 30, 36, constants.WHITE)
        self._draw_text(subtitle, constants.LOGICAL_WIDTH // 2 - 120, constants.LOGICAL_HEIGHT // 2 + 20, 18, constants.WHITE)

    def _draw_text(self, text, x, y, size, color):
        if self._font is None or self._font.size != size:
            self._font = pygame.font.SysFont(None, size)
        surface = self._font.render(text, True, color)
        self.screen.blit(surface, (x, y))
