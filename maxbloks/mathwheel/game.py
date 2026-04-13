# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""MathWheelGame — main game class with state machine and rendering.

Controller mapping (console-first):
  D-pad Up/Down     Scroll number wheel
  A button (0/1)    Submit current number as answer (select + confirm in one press)
  D-pad Right       Skip current question
  X button (3)      Open / close in-game menu
  Menu/Start (8/13) Exit game

  Keyboard equivalents:
  Up/Down / W/S     Scroll wheel
  Enter / Space     Submit answer
  Right / D         Skip question
  X                 Open / close menu
  Escape            Close menu / back
"""

import pygame

from maxbloks.mathwheel import compat_sdl
from maxbloks.mathwheel import constants
from maxbloks.mathwheel import utils
from maxbloks.mathwheel import entities
from maxbloks.mathwheel.game_framework import GameFramework


class MathWheelGame(GameFramework):
    """Math practice game with inline number wheel input."""

    # States
    MENU = "menu"
    PLAYING = "playing"

    def __init__(self, title="MathWheel", fps=60):
        screen, display_info = compat_sdl.init_display(
            size=(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
            fullscreen=constants.FULLSCREEN,
            vsync=True,
        )
        super().__init__(screen, display_info, title, fps)
        self._init_fonts()
        self._init_surfaces()
        self._init_state()

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

        self.difficulty = utils.DifficultyManager()
        self.score = utils.ScoreTracker()
        self.wheel = entities.NumberWheel()
        self.feedback = entities.FeedbackEffect()
        self.star_anim = entities.StarAnimation()

        self.question = None
        self._advance_timer = 0
        self._wrong_dismissed = False

        self.menu_cursor = constants.MENU_ITEM_PLAY

        self._wheel_repeat_timer = 0
        self._wheel_repeat_dir = 0
        self._wheel_held = False

        self._last_ticks = pygame.time.get_ticks()

        self._next_question()

    # ------------------------------------------------------------------
    # Question management
    # ------------------------------------------------------------------

    def _next_question(self):
        diff = self.difficulty.pick_difficulty()
        self.question = utils.generate_question(diff, self.operations)
        self.score.new_question()
        self.wheel.set_range(0, max(self.question.result + 10, 20))
        self.wheel.set_value(0)
        self._advance_timer = 0
        self._wrong_dismissed = False
        self.feedback.dismiss()

    def _check_answer(self):
        if self.wheel.value == self.question.answer:
            earned = self.score.award_correct()
            self.difficulty.record_correct()
            self.feedback.trigger_correct(earned)
            self.star_anim.trigger()
            self._advance_timer = constants.CORRECT_AUTO_ADVANCE_DELAY
        else:
            self.score.record_wrong()
            self.difficulty.record_wrong()
            self.feedback.trigger_wrong()
            self._wrong_dismissed = False

    def _skip_question(self):
        """Skip to the next question immediately."""
        self.feedback.dismiss()
        self._next_question()

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def handle_input(self):
        super().handle_input()

        if self.state == self.MENU:
            self._handle_menu_input()
        elif self.state == self.PLAYING:
            self._handle_playing_input()

    def _handle_menu_input(self):
        if self.movement_y < 0:
            self.menu_cursor = max(0, self.menu_cursor - 1)
        elif self.movement_y > 0:
            self.menu_cursor = min(
                constants.MENU_ITEM_COUNT - 1, self.menu_cursor + 1
            )

        if self.shoot_button_pressed:
            self._activate_menu_item()

        # Both X button and Escape/B close the menu
        if self.action_button_pressed or self.back_button_pressed:
            self.state = self.PLAYING

    def _activate_menu_item(self):
        if self.menu_cursor == constants.MENU_ITEM_PLAY:
            self.state = self.PLAYING
        elif self.menu_cursor == constants.MENU_ITEM_ADDITION:
            self._toggle_operation(constants.OP_ADD)
        elif self.menu_cursor == constants.MENU_ITEM_SUBTRACTION:
            self._toggle_operation(constants.OP_SUB)
        elif self.menu_cursor == constants.MENU_ITEM_MULTIPLICATION:
            self._toggle_operation(constants.OP_MUL)
        elif self.menu_cursor == constants.MENU_ITEM_DIVISION:
            self._toggle_operation(constants.OP_DIV)

    def _toggle_operation(self, op):
        enabled_count = sum(1 for v in self.operations.values() if v)
        if self.operations[op] and enabled_count <= 1:
            return
        self.operations[op] = not self.operations[op]

    def _handle_playing_input(self):
        # X button or Escape → open menu
        if self.action_button_pressed or self.back_button_pressed:
            self.state = self.MENU
            return

        # While correct feedback is playing, block all input
        # (auto-advance timer will move to the next question)
        if self.feedback.active and self.feedback.correct:
            return

        # Wrong feedback is persistent — A/Enter or wheel movement dismisses it
        if self.feedback.active and self.feedback.persistent:
            if self.shoot_button_pressed or self.movement_y != 0:
                self.feedback.dismiss()
                self._wrong_dismissed = True
            # Skip is still available during wrong feedback
            if self.skip_button_pressed:
                self._skip_question()
            return

        # D-pad right / keyboard right → skip
        if self.skip_button_pressed:
            self._skip_question()
            return

        # Up/Down → scroll the wheel
        if self.movement_y < 0:
            self.wheel.scroll_up()
            self._wheel_repeat_dir = -1
            self._wheel_repeat_timer = constants.WHEEL_REPEAT_DELAY
            self._wheel_held = True
        elif self.movement_y > 0:
            self.wheel.scroll_down()
            self._wheel_repeat_dir = 1
            self._wheel_repeat_timer = constants.WHEEL_REPEAT_DELAY
            self._wheel_held = True

        # A button / Enter / Space → submit current wheel value as answer
        if self.shoot_button_pressed:
            self._check_answer()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        now = pygame.time.get_ticks()
        dt = now - self._last_ticks
        self._last_ticks = now

        self.wheel.update()
        self.feedback.update(dt)
        self.star_anim.update(dt)

        # Auto-advance after correct answer
        if self._advance_timer > 0:
            self._advance_timer -= dt
            if self._advance_timer <= 0:
                self._advance_timer = 0
                self._next_question()

        # Key repeat for wheel
        if self._wheel_held:
            keys = pygame.key.get_pressed()
            up_held = keys[pygame.K_UP] or keys[pygame.K_w]
            down_held = keys[pygame.K_DOWN] or keys[pygame.K_s]

            joy_held = False
            if self.joystick:
                axis_y = self.joystick.get_axis(1)
                if abs(axis_y) > constants.JOYSTICK_AXIS_THRESHOLD:
                    joy_held = True

            hat_held = False
            if self.joystick and self.joystick.get_numhats() > 0:
                _hx, hy = self.joystick.get_hat(0)
                if hy != 0:
                    hat_held = True

            if up_held or down_held or joy_held or hat_held:
                self._wheel_repeat_timer -= dt
                if self._wheel_repeat_timer <= 0:
                    if self._wheel_repeat_dir < 0:
                        self.wheel.scroll_up()
                    else:
                        self.wheel.scroll_down()
                    self._wheel_repeat_timer = constants.WHEEL_REPEAT_INTERVAL
            else:
                self._wheel_held = False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self):
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
            selected = idx == self.menu_cursor
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

        self._draw_score()
        self._draw_equation_with_wheel()
        self._draw_wrong_feedback()
        self._draw_correct_feedback()
        self._draw_hud()

    def _draw_score(self):
        """Draw numeric score in the top-left corner."""
        score_text = str(self.score.stars)
        if self.star_anim.active:
            scale = self.star_anim.scale
            size = int(constants.SCORE_FONT_SIZE * scale)
            font = pygame.font.Font(None, max(size, 8))
        else:
            font = self.font_score

        surf = font.render(score_text, True, constants.SCORE_COLOR)
        label_surf = self.font_hud.render("pts", True, constants.GRAY)
        x = 12
        y = constants.STAR_BAR_Y
        self.screen.blit(surf, (x, y))
        self.screen.blit(
            label_surf,
            (x + surf.get_width() + 4,
             y + surf.get_height() - label_surf.get_height())
        )

    def _draw_equation_with_wheel(self):
        """Draw the full equation; replace the ? position with the inline wheel."""
        if self.question is None:
            return

        cx = self.screen_width // 2
        ey = int(self.screen_height * constants.EQUATION_Y_RATIO)

        left, op, right, result = self.question.display_values
        parts = self._build_equation_parts(left, op, right, result)

        wheel_slot_w = self._inline_wheel_width()
        total_w = 0
        widths = []
        for text, is_wheel in parts:
            if is_wheel:
                w = wheel_slot_w
            else:
                surf = self.font_equation.render(text, True, constants.WHITE)
                w = surf.get_width()
            widths.append(w)
            total_w += w

        x = cx - total_w // 2
        for idx, (text, is_wheel) in enumerate(parts):
            w = widths[idx]
            if is_wheel:
                self._draw_inline_wheel(x, ey, w)
            else:
                surf = self.font_equation.render(text, True, constants.WHITE)
                rect = surf.get_rect(midleft=(x, ey))
                self.screen.blit(surf, rect)
            x += w

    def _build_equation_parts(self, left, op, right, result):
        """Return list of (text, is_wheel) for each part of the equation."""
        parts = []
        parts.append((str(left) if left is not None else None, left is None))
        parts.append(("  " + op + "  ", False))
        parts.append((str(right) if right is not None else None, right is None))
        parts.append(("  =  ", False))
        parts.append((str(result) if result is not None else None, result is None))
        return parts

    def _inline_wheel_width(self):
        """Width to reserve for the inline wheel slot."""
        sample = self.font_wheel_inline.render("00", True, constants.WHITE)
        return sample.get_width() + 20

    def _draw_inline_wheel(self, slot_x, center_y, slot_w):
        """Draw the vertically scrolling number picker at the ? position."""
        cx = slot_x + slot_w // 2
        item_h = self.font_wheel_inline.size("0")[1] + 6

        visible = self.wheel.get_visible_numbers()

        box_h = item_h * self.wheel.visible_items + 8
        box_rect = pygame.Rect(
            cx - slot_w // 2, center_y - box_h // 2, slot_w, box_h
        )

        if self.feedback.active and self.feedback.correct:
            border_col = constants.CORRECT_COLOR
            bg_col = (20, 80, 30)
        elif self.feedback.active and self.feedback.persistent:
            border_col = (
                constants.WRONG_COLOR if self.feedback.blink_visible
                else constants.EQUATION_BORDER
            )
            bg_col = (
                constants.WRONG_BG_COLOR if self.feedback.blink_visible
                else constants.EQUATION_BG
            )
        else:
            border_col = constants.WHEEL_SELECTED
            bg_col = constants.WHEEL_BG

        pygame.draw.rect(self.screen, bg_col, box_rect, border_radius=10)
        pygame.draw.rect(self.screen, border_col, box_rect, 3, border_radius=10)

        for num, rel_pos in visible:
            ny = center_y + rel_pos * item_h
            if rel_pos == 0:
                hi_rect = pygame.Rect(
                    cx - slot_w // 2 + 3, ny - item_h // 2 + 1,
                    slot_w - 6, item_h - 2,
                )
                pygame.draw.rect(
                    self.screen, constants.WHEEL_HIGHLIGHT, hi_rect, border_radius=7
                )
                color = constants.WHEEL_SELECTED
                font = self.font_wheel_inline
            else:
                color = constants.WHEEL_DIM_COLOR
                font = self.font_wheel_inline_dim

            text_surf = font.render(str(num), True, color)
            text_rect = text_surf.get_rect(center=(cx, ny))
            self.screen.blit(text_surf, text_rect)

        arrow_col = constants.WHEEL_SELECTED
        if self.wheel.value > self.wheel.min_val:
            self._draw_arrow_up(cx, box_rect.top - 10, arrow_col)
        if self.wheel.value < self.wheel.max_val:
            self._draw_arrow_down(cx, box_rect.bottom + 10, arrow_col)

    def _draw_correct_feedback(self):
        """Brief green ✓ and points flash after a correct answer."""
        if not (self.feedback.active and self.feedback.correct):
            return

        alpha = self.feedback.alpha
        cx = self.screen_width // 2
        fy = int(self.screen_height * 0.78)

        surf = self.font_feedback.render("✓", True, constants.CORRECT_COLOR)
        surf.set_alpha(int(alpha * 255))
        rect = surf.get_rect(center=(cx, fy))
        self.screen.blit(surf, rect)

        if self.feedback.earned_stars > 0:
            star_text = f"+{self.feedback.earned_stars}"
            star_surf = self.font_score.render(star_text, True, constants.STAR_COLOR)
            star_surf.set_alpha(int(alpha * 255))
            sr = star_surf.get_rect(center=(cx, fy + 46))
            self.screen.blit(star_surf, sr)

    def _draw_wrong_feedback(self):
        """Persistent blinking red ✗ with retry hint until player dismisses it."""
        if not (self.feedback.active and self.feedback.persistent):
            return

        if not self.feedback.blink_visible:
            return

        cx = self.screen_width // 2
        fy = int(self.screen_height * 0.78)

        surf = self.font_feedback.render("✗", True, constants.WRONG_COLOR)
        rect = surf.get_rect(center=(cx, fy))
        self.screen.blit(surf, rect)

        hint = self.font_hud.render(
            "A/Enter to retry   →/D to skip", True, constants.WRONG_COLOR
        )
        hr = hint.get_rect(center=(cx, fy + 44))
        self.screen.blit(hint, hr)

    def _draw_hud(self):
        """Draw bottom HUD: difficulty level (left) and controls hint (right)."""
        y = self.screen_height - 26
        config = constants.DIFFICULTY_CONFIG[self.difficulty.current_level]
        diff_text = f"Level: {config['label']}"
        self._draw_text_at(diff_text, 10, y, self.font_hud, constants.GRAY)

        hint = "↑↓ Scroll  A Submit  → Skip  X Menu"
        hw = self.font_hud.render(hint, True, constants.GRAY).get_width()
        self._draw_text_at(
            hint, self.screen_width - hw - 10, y,
            self.font_hud, constants.GRAY,
        )

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