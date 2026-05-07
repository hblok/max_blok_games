# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

""" TemplateGame — main game class with state machine and rendering.
"""

import pygame

from maxbloks.template import compat_sdl
from maxbloks.template import constants
from maxbloks.template import input_handler
#from maxbloks.mathwheel import utils
#from maxbloks.mathwheel import entities
from maxbloks.template.game_framework import GameFramework


class TemplateGame(GameFramework):

    # States
    MENU = "menu"
    PLAYING = "playing"

    def __init__(self, title="MathWheel", fps=60):
        screen, display_info = compat_sdl.init_display(
            size=(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
            fullscreen=constants.FULLSCREEN,
            vsync=True,
        )
        
        print("screen: ", str(screen))
        print("display_info: ", str(display_info))

        super().__init__(screen, display_info, title, fps)
        self._init_fonts()
        self._init_surfaces()
        self._init_state()

        self.input = input_handler.InputHandler()

    def handle_input(self):
        self.input.update()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    def _init_fonts(self):
        self.font_title = pygame.font.Font(None, constants.FONT_SIZE_TITLE)
        self.font_equation = pygame.font.Font(None, constants.FONT_SIZE_EQUATION)
        self.font_wheel_inline = pygame.font.Font(
            None, constants.FONT_SIZE_WHEEL_INLINE
        )
        self.font_wheel_inline_dim = pygame.font.Font(
            None, constants.FONT_SIZE_WHEEL_INLINE_DIM
        )
        self.font_hud = pygame.font.Font(None, constants.FONT_SIZE_HUD)
        self.font_score = pygame.font.Font(None, constants.SCORE_FONT_SIZE)
        self.font_menu = pygame.font.Font(None, constants.FONT_SIZE_MENU)
        self.font_menu_small = pygame.font.Font(None, constants.FONT_SIZE_MENU_SMALL)
        self.font_feedback = pygame.font.Font(None, constants.FONT_SIZE_FEEDBACK)

    def _init_surfaces(self):
        """Pre-render static surfaces."""
        self.bg_surface = pygame.Surface(
            (self.screen_width, self.screen_height)
        )
        self._render_gradient_bg(self.bg_surface)

    def _init_state(self):
        """Initialize all game state."""
        self.state = self.PLAYING

        self.operations = {
            constants.OP_ADD: True,
            constants.OP_SUB: True,
            constants.OP_MUL: False,
            constants.OP_DIV: False,
        }

        #self.score = utils.ScoreTracker()

        self._last_ticks = pygame.time.get_ticks()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        now = pygame.time.get_ticks()
        dt = now - self._last_ticks
        self._last_ticks = now

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self):
        self._draw_menu()
        
        if self.state == self.MENU:
            self._draw_menu()
        elif self.state == self.PLAYING:
            self._draw_playing()

        pygame.display.flip()

    # -- Menu drawing --

    def _draw_menu(self):
        self.screen.blit(self.bg_surface, (0, 0))
        cx = self.screen_width // 2
        y = 40

        self._draw_centered_text(
            "MathWheel", cx, y, self.font_title, constants.TITLE_COLOR
        )
        y += 70

        items = [
            ("▶  Play", None),
            ("Addition  " + self._op_label(constants.OP_ADD), constants.OP_ADD),
            ("Subtraction  " + self._op_label(constants.OP_SUB), constants.OP_SUB),
            ("Multiply  " + self._op_label(constants.OP_MUL), constants.OP_MUL),
            ("Division  " + self._op_label(constants.OP_DIV), constants.OP_DIV),
        ]

        for idx, (label, op) in enumerate(items):
            selected = None #idx == self.menu_cursor
            item_y = y + idx * 60
            self._draw_menu_item(cx, item_y, label, selected, op)

        self._draw_centered_text(
            "↑↓ Select   A/Enter Confirm   X/Esc Close",
            cx, self.screen_height - 30,
            self.font_menu_small, constants.GRAY,
        )

    def _draw_menu_item(self, cx, y, label, selected, op):
        w = 360
        h = 46
        rect = pygame.Rect(cx - w // 2, y - h // 2, w, h)
        bg = constants.MENU_ITEM_SELECTED if selected else constants.MENU_ITEM_BG
        pygame.draw.rect(self.screen, bg, rect, border_radius=10)
        pygame.draw.rect(
            self.screen, constants.MENU_ITEM_BORDER, rect, 2, border_radius=10
        )

        color = constants.WHITE
        if op is not None:
            color = constants.TOGGLE_ON if self.operations[op] else constants.TOGGLE_OFF

        self._draw_centered_text(label, cx, y, self.font_menu, color)

    def _op_label(self, op):
        return "[ON]" if self.operations[op] else "[OFF]"

    # -- Playing drawing --

    def _draw_playing(self):
        self.screen.blit(self.bg_surface, (0, 0))

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _render_gradient_bg(self, surface):
        h = surface.get_height()
        w = surface.get_width()
        top = constants.BG_GRADIENT_TOP
        bot = constants.BG_GRADIENT_BOTTOM
        for y in range(h):
            t = y / max(h - 1, 1)
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

    def _draw_arrow_up(self, x, y, color):
        points = [(x, y - 6), (x - 8, y + 4), (x + 8, y + 4)]
        pygame.draw.polygon(self.screen, color, points)

    def _draw_arrow_down(self, x, y, color):
        points = [(x, y + 6), (x - 8, y - 4), (x + 8, y - 4)]
        pygame.draw.polygon(self.screen, color, points)

    def _draw_centered_text(self, text, x, y, font, color):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(x, y))
        self.screen.blit(surf, rect)

    def _draw_text_at(self, text, x, y, font, color):
        surf = font.render(text, True, color)
        self.screen.blit(surf, (x, y))
