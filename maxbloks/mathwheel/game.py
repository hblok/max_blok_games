# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""MathWheelGame — main game class with state machine and rendering."""

import math
import pygame

from maxbloks.mathwheel import compat_sdl
from maxbloks.mathwheel import constants
from maxbloks.mathwheel import utils
from maxbloks.mathwheel import entities
from maxbloks.mathwheel.game_framework import GameFramework


class MathWheelGame(GameFramework):
    """Math practice game with number wheel input."""

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
        self.font_wheel = pygame.font.Font(None, constants.FONT_SIZE_WHEEL)
        self.font_wheel_dim = pygame.font.Font(None, constants.FONT_SIZE_WHEEL_DIM)
        self.font_button = pygame.font.Font(None, constants.FONT_SIZE_BUTTON)
        self.font_hud = pygame.font.Font(None, constants.FONT_SIZE_HUD)
        self.font_menu = pygame.font.Font(None, constants.FONT_SIZE_MENU)
        self.font_menu_small = pygame.font.Font(None, constants.FONT_SIZE_MENU_SMALL)
        self.font_feedback = pygame.font.Font(None, constants.FONT_SIZE_FEEDBACK)

    def _init_surfaces(self):
        """Pre-render static surfaces."""
        self.bg_surface = pygame.Surface(
            (self.screen_width, self.screen_height)
        )
        self._render_gradient_bg(self.bg_surface)

        # Pre-render star shapes
        self.star_surface = self._render_star(
            constants.STAR_SIZE, constants.STAR_COLOR
        )
        self.star_empty_surface = self._render_star(
            constants.STAR_SIZE, constants.STAR_EMPTY_COLOR
        )

    def _init_state(self):
        """Initialize all game state."""
        self.state = self.PLAYING

        # Operations enabled
        self.operations = {
            constants.OP_ADD: True,
            constants.OP_SUB: True,
            constants.OP_MUL: False,
            constants.OP_DIV: False,
        }

        # Core game objects
        self.difficulty = utils.DifficultyManager()
        self.score = utils.ScoreTracker()
        self.wheel = entities.NumberWheel()
        self.feedback = entities.FeedbackEffect()
        self.star_anim = entities.StarAnimation()
        self.focus = entities.UIFocus()

        # Current question
        self.question = None
        self.waiting_for_next = False
        self.can_retry = True
        self._wrong_count = 0

        # Menu state
        self.menu_cursor = constants.MENU_ITEM_PLAY

        # Key repeat tracking for wheel
        self._wheel_repeat_timer = 0
        self._wheel_repeat_dir = 0
        self._wheel_held = False

        # Frame timer
        self._last_ticks = pygame.time.get_ticks()

        # Start first question
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
        self.focus.reset()
        self.waiting_for_next = False
        self.can_retry = True
        self._wrong_count = 0

    def _check_answer(self):
        if self.wheel.value == self.question.answer:
            earned = self.score.award_correct()
            self.difficulty.record_correct()
            self.feedback.trigger_correct(earned)
            self.star_anim.trigger()
            self.waiting_for_next = True
        else:
            self.score.record_wrong()
            self.difficulty.record_wrong()
            self.feedback.trigger_wrong()
            self._wrong_count += 1
            if self._wrong_count >= 3:
                self.can_retry = True
                self.waiting_for_next = False

    def _skip_question(self):
        self.waiting_for_next = True
        self.feedback.trigger_wrong()

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

        if self.back_button_pressed:
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
        if self.back_button_pressed:
            self.state = self.MENU
            return

        if self.waiting_for_next and self.feedback.is_finished:
            if self.shoot_button_pressed or self.movement_y != 0:
                self._next_question()
            return

        if self.feedback.active:
            return

        # Focus navigation with left/right
        if self.movement_x < 0:
            self.focus.move_left()
        elif self.movement_x > 0:
            self.focus.move_right()

        # Wheel scrolling with up/down
        if self.focus.current == entities.UIFocus.WHEEL:
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

        # Action on focused element
        if self.shoot_button_pressed:
            if self.focus.current == entities.UIFocus.SUBMIT:
                self._check_answer()
            elif self.focus.current == entities.UIFocus.SKIP:
                self._skip_question()
            elif self.focus.current == entities.UIFocus.WHEEL:
                self.focus.current = entities.UIFocus.SUBMIT

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

            if (up_held or down_held or joy_held or hat_held) and \
               self.focus.current == entities.UIFocus.WHEEL:
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

        # Title
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

        # Instructions at bottom
        self._draw_centered_text(
            "↑↓ Select   Enter/A Confirm   Esc/B Back",
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

        self._draw_star_bar()
        self._draw_equation()
        self._draw_wheel()
        self._draw_buttons()
        self._draw_feedback()
        self._draw_hud()

    def _draw_star_bar(self):
        x = 10
        y = constants.STAR_BAR_Y
        # Show filled stars
        for i in range(min(self.score.stars, constants.MAX_STARS_DISPLAY)):
            surf = self.star_surface
            if self.star_anim.active and i == self.score.stars - 1:
                scale = self.star_anim.scale
                w = int(constants.STAR_SIZE * scale)
                h = int(constants.STAR_SIZE * scale)
                surf = pygame.transform.scale(self.star_surface, (w, h))
            self.screen.blit(surf, (x + i * constants.STAR_SPACING, y))

        if self.score.stars > constants.MAX_STARS_DISPLAY:
            count_text = f"×{self.score.stars}"
            self._draw_text_at(
                count_text,
                x + constants.MAX_STARS_DISPLAY * constants.STAR_SPACING + 4,
                y + 4,
                self.font_hud,
                constants.STAR_COLOR,
            )

    def _draw_equation(self):
        if self.question is None:
            return

        cx = self.screen_width // 2
        ey = int(self.screen_height * constants.EQUATION_Y_RATIO)

        left, op, right, result = self.question.display_values

        parts = []
        parts.append(self._eq_part(left))
        parts.append(("  " + op + "  ", False))
        parts.append(self._eq_part(right))
        parts.append(("  =  ", False))
        parts.append(self._eq_part(result))

        # Measure total width
        total_w = 0
        rendered = []
        for text, is_blank in parts:
            if is_blank:
                surf = self.font_equation.render("?", True, constants.WHEEL_SELECTED)
            else:
                surf = self.font_equation.render(text, True, constants.WHITE)
            rendered.append((surf, is_blank))
            total_w += surf.get_width()

        # Draw centered
        x = cx - total_w // 2
        for surf, is_blank in rendered:
            rect = surf.get_rect(midleft=(x, ey))
            if is_blank:
                # Draw box behind the question mark
                box = rect.inflate(12, 8)
                pygame.draw.rect(
                    self.screen, constants.EQUATION_BG, box, border_radius=8
                )
                pygame.draw.rect(
                    self.screen, constants.WHEEL_SELECTED, box, 2, border_radius=8
                )
            self.screen.blit(surf, rect)
            x += surf.get_width()

    def _eq_part(self, value):
        """Return (text, is_blank) for an equation part."""
        if value is None:
            return ("?", True)
        return (str(value), False)

    def _draw_wheel(self):
        cx = self.screen_width // 2
        wy = int(self.screen_height * constants.WHEEL_Y_RATIO)
        item_h = 48

        visible = self.wheel.get_visible_numbers()
        is_focused = self.focus.current == entities.UIFocus.WHEEL

        # Background box
        box_w = 120
        box_h = item_h * self.wheel.visible_items + 10
        box_rect = pygame.Rect(
            cx - box_w // 2, wy - box_h // 2, box_w, box_h
        )
        pygame.draw.rect(
            self.screen, constants.WHEEL_BG, box_rect, border_radius=12
        )
        border_color = constants.WHEEL_SELECTED if is_focused else constants.EQUATION_BORDER
        pygame.draw.rect(
            self.screen, border_color, box_rect, 2, border_radius=12
        )

        for num, rel_pos in visible:
            ny = wy + rel_pos * item_h
            if rel_pos == 0:
                # Selected number
                highlight = pygame.Rect(
                    cx - box_w // 2 + 4, ny - item_h // 2 + 2,
                    box_w - 8, item_h - 4,
                )
                pygame.draw.rect(
                    self.screen, constants.WHEEL_HIGHLIGHT, highlight,
                    border_radius=8,
                )
                color = constants.WHEEL_SELECTED
                font = self.font_wheel
            else:
                dist = abs(rel_pos)
                color = constants.WHEEL_DIM_COLOR
                font = self.font_wheel_dim

            text_surf = font.render(str(num), True, color)
            text_rect = text_surf.get_rect(center=(cx, ny))
            self.screen.blit(text_surf, text_rect)

        # Draw scroll arrows
        arrow_color = constants.WHEEL_SELECTED if is_focused else constants.GRAY
        if self.wheel.value > self.wheel.min_val:
            self._draw_arrow_up(cx, wy - box_h // 2 - 14, arrow_color)
        if self.wheel.value < self.wheel.max_val:
            self._draw_arrow_down(cx, wy + box_h // 2 + 14, arrow_color)

    def _draw_buttons(self):
        by = int(self.screen_height * constants.SUBMIT_Y_RATIO)
        cx = self.screen_width // 2

        # Submit button (checkmark)
        submit_x = cx - 50
        submit_focused = self.focus.current == entities.UIFocus.SUBMIT
        self._draw_circle_button(
            submit_x, by, constants.SUBMIT_BUTTON_RADIUS,
            constants.SUBMIT_HOVER if submit_focused else constants.SUBMIT_COLOR,
            submit_focused,
        )
        self._draw_checkmark(submit_x, by, 16, constants.WHITE)

        # Skip button (arrow right)
        skip_x = cx + 50
        skip_focused = self.focus.current == entities.UIFocus.SKIP
        self._draw_circle_button(
            skip_x, by, constants.SKIP_BUTTON_RADIUS,
            constants.SKIP_HOVER if skip_focused else constants.SKIP_COLOR,
            skip_focused,
        )
        self._draw_skip_arrow(skip_x, by, 12, constants.WHITE)

    def _draw_circle_button(self, x, y, radius, color, focused):
        pygame.draw.circle(self.screen, color, (x, y), radius)
        if focused:
            pygame.draw.circle(
                self.screen, constants.WHITE, (x, y), radius + 3, 3
            )

    def _draw_checkmark(self, x, y, size, color):
        points = [
            (x - size // 2, y),
            (x - size // 6, y + size // 2),
            (x + size // 2, y - size // 3),
        ]
        pygame.draw.lines(self.screen, color, False, points, 4)

    def _draw_skip_arrow(self, x, y, size, color):
        points = [
            (x - size // 2, y - size // 2),
            (x + size // 2, y),
            (x - size // 2, y + size // 2),
        ]
        pygame.draw.polygon(self.screen, color, points)
        # Double arrow line
        lx = x + size // 2 + 4
        pygame.draw.line(
            self.screen, color, (lx, y - size // 2), (lx, y + size // 2), 3
        )

    def _draw_feedback(self):
        if not self.feedback.active:
            return

        alpha = self.feedback.alpha
        cx = self.screen_width // 2
        fy = int(self.screen_height * 0.42)

        if self.feedback.correct:
            text = "✓"
            color = constants.CORRECT_COLOR
        else:
            text = "✗"
            color = constants.WRONG_COLOR

        surf = self.font_feedback.render(text, True, color)
        surf.set_alpha(int(alpha * 255))
        rect = surf.get_rect(center=(cx, fy))
        self.screen.blit(surf, rect)

        if self.feedback.correct and self.feedback.earned_stars > 0:
            star_text = f"+{self.feedback.earned_stars} ★"
            star_surf = self.font_hud.render(
                star_text, True, constants.STAR_COLOR
            )
            star_surf.set_alpha(int(alpha * 255))
            sr = star_surf.get_rect(center=(cx, fy + 36))
            self.screen.blit(star_surf, sr)

    def _draw_hud(self):
        """Draw bottom HUD with controls hint and difficulty."""
        y = self.screen_height - 26
        config = constants.DIFFICULTY_CONFIG[self.difficulty.current_level]
        diff_text = f"Level: {config['label']}"
        self._draw_text_at(diff_text, 10, y, self.font_hud, constants.GRAY)

        hint = "↑↓ Scroll  ←→ Focus  Enter ✓  Esc Menu"
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

    def _render_star(self, size, color):
        """Render a 5-pointed star as a surface."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = size // 2
        cy = size // 2
        r_outer = size // 2 - 1
        r_inner = r_outer * 0.4
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = r_outer if i % 2 == 0 else r_inner
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(surf, color, points)
        return surf

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