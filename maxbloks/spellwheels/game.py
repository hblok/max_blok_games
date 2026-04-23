# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""SpellWheels game controller.

State machine:

    MENU ---start--> PLAYING <---resume--- PAUSED
                        |   \\
                        |    ---pause---> PAUSED
                        |
                        v
                  LEVEL_COMPLETE ---auto---> PLAYING  (next level)
                        |
                        +----all levels done--> GAME_OVER
                        |
                   GAME_OVER ---confirm---> MENU

All gameplay screens are strictly icon-based; text is only rendered on
the options/pause menu where legibility trumps the icon-only rule.
"""

import enum
import math
import pygame

from maxbloks.spellwheels import constants
from maxbloks.spellwheels import entities
from maxbloks.spellwheels import utils


class GameState(enum.Enum):
    """High-level game states."""

    MENU = enum.auto()
    PLAYING = enum.auto()
    PAUSED = enum.auto()
    LEVEL_COMPLETE = enum.auto()
    GAME_OVER = enum.auto()


class SpellWheelsGame:
    """Main game controller with state machine, update and draw loops."""

    def __init__(self, surface_size=None):
        size = surface_size or (constants.LOGICAL_WIDTH, constants.LOGICAL_HEIGHT)
        self.screen_width, self.screen_height = size
        self.state = GameState.MENU

        self._init_fonts()
        self._init_surfaces()
        self._init_state()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def _init_fonts(self):
        self.font_title = pygame.font.Font(None, constants.FONT_SIZE_TITLE)
        self.font_menu = pygame.font.Font(None, constants.FONT_SIZE_MENU)
        self.font_menu_small = pygame.font.Font(
            None, constants.FONT_SIZE_MENU_SMALL
        )
        self.font_wheel = pygame.font.Font(None, constants.FONT_SIZE_WHEEL)
        self.font_wheel_dim = pygame.font.Font(
            None, constants.FONT_SIZE_WHEEL_DIM
        )
        self.font_hud = pygame.font.Font(None, constants.FONT_SIZE_HUD)
        self.font_feedback = pygame.font.Font(
            None, constants.FONT_SIZE_FEEDBACK
        )
        # Try to enable bold for the wheels (block-letter style).
        self.font_wheel.set_bold(True)
        self.font_title.set_bold(True)
        self.font_feedback.set_bold(True)

    def _init_surfaces(self):
        self.bg_surface = pygame.Surface(
            (self.screen_width, self.screen_height)
        )
        self._render_gradient_bg(self.bg_surface)

    def _init_state(self):
        self.levels = utils.build_default_levels()
        self.score = utils.ScoreTracker()
        self.saver = utils.ProgressSaver()
        self.feedback = entities.FeedbackEffect()
        self.star_anim = entities.StarAnimation()

        saved = self.saver.load()
        self.level_index = utils.clamp(
            saved["last_level"], 0, len(self.levels) - 1
        )
        word_start = utils.clamp(
            saved["last_word_index"], 0, self.levels[self.level_index].word_count - 1
        )
        self.score.total_stars = saved["total_stars"]
        self.runner = entities.LevelRunner(
            self.levels[self.level_index], word_start
        )

        self._advance_timer = 0
        self._menu_cursor = constants.MENU_ITEM_PLAY
        self._has_saved_game = saved["total_stars"] > 0 or saved["last_word_index"] > 0

        self._last_ticks = pygame.time.get_ticks()
        # Key-repeat bookkeeping for held buttons on gameplay screen
        self._repeat_dir_x = 0
        self._repeat_dir_y = 0
        self._repeat_timer = 0

        # Stars awarded for the most recent word (shown during feedback)
        self._last_stars_awarded = 0

        # Cached per-word wheel layout
        self._wheel_rects = []
        self._build_wheel_layout()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update(self, input_state):
        """Advance the game by one frame. Return False to request quit."""
        if input_state.quit_requested:
            self._save_progress()
            return False

        now = pygame.time.get_ticks()
        dt = now - self._last_ticks
        self._last_ticks = now

        # Always update timed animations
        self.feedback.update(dt)
        self.star_anim.update(dt)

        if self.state == GameState.MENU:
            self._update_menu(input_state)
        elif self.state == GameState.PLAYING:
            self._update_playing(input_state, dt)
        elif self.state == GameState.PAUSED:
            self._update_paused(input_state)
        elif self.state == GameState.LEVEL_COMPLETE:
            self._update_level_complete(input_state, dt)
        elif self.state == GameState.GAME_OVER:
            self._update_game_over(input_state)

        return True

    def draw(self, screen):
        if self.state == GameState.MENU:
            self._draw_menu(screen)
        elif self.state == GameState.PLAYING:
            self._draw_playing(screen)
        elif self.state == GameState.PAUSED:
            self._draw_playing(screen)
            self._draw_pause_overlay(screen)
        elif self.state == GameState.LEVEL_COMPLETE:
            self._draw_level_complete(screen)
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over(screen)

    # ------------------------------------------------------------------
    # State updates
    # ------------------------------------------------------------------
    def _update_menu(self, inp):
        if inp.spin_up:
            self._menu_cursor = (self._menu_cursor - 1) % constants.MENU_ITEM_COUNT
        if inp.spin_down:
            self._menu_cursor = (self._menu_cursor + 1) % constants.MENU_ITEM_COUNT

        if inp.submit:
            self._activate_menu_item()

        if inp.pause:
            # Escape from the main menu starts the game immediately
            self.state = GameState.PLAYING

    def _activate_menu_item(self):
        if self._menu_cursor == constants.MENU_ITEM_PLAY:
            # New game from the beginning
            self.score.reset()
            self.level_index = 0
            self.runner = entities.LevelRunner(self.levels[0], 0)
            self._build_wheel_layout()
            self.state = GameState.PLAYING
        elif self._menu_cursor == constants.MENU_ITEM_RESUME:
            if self._has_saved_game:
                self.state = GameState.PLAYING
        elif self._menu_cursor == constants.MENU_ITEM_RESET:
            self.saver.clear()
            self.score.reset()
            self.level_index = 0
            self.runner = entities.LevelRunner(self.levels[0], 0)
            self._has_saved_game = False
            self._build_wheel_layout()
        elif self._menu_cursor == constants.MENU_ITEM_QUIT:
            # Request quit via a sentinel -- the main loop picks this up
            # by observing update() returning False next call.
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _update_playing(self, inp, dt):
        # Global transitions first
        if inp.pause:
            self.state = GameState.PAUSED
            return

        if inp.map_view:
            # Level/world map currently just returns to menu
            self.state = GameState.MENU
            return

        # Feedback in progress: only allow pause
        if self.feedback.active:
            self._advance_timer -= dt
            if self._advance_timer <= 0:
                self._after_correct_advance()
            return

        puzzle = self.runner.puzzle
        puzzle.update(dt)

        # Cursor movement
        if inp.move_left:
            puzzle.move_left()
        if inp.move_right:
            puzzle.move_right()

        # Wheel spinning
        if inp.spin_up:
            puzzle.spin_up()
        if inp.spin_down:
            puzzle.spin_down()

        # Clear / undo
        if inp.clear:
            puzzle.clear_active()

        # Hint
        if inp.hint:
            puzzle.trigger_hint()

        # Submit
        if inp.submit:
            self._submit_word()

    def _update_paused(self, inp):
        # Any of: pause, submit, clear -> resume
        if inp.pause or inp.submit:
            self.state = GameState.PLAYING
        elif inp.map_view:
            self.state = GameState.MENU

    def _update_level_complete(self, inp, dt):
        # Auto-advance after the display duration, or on submit
        if inp.submit or inp.pause or not self.feedback.active:
            self._begin_next_level_or_finish()

    def _update_game_over(self, inp):
        if inp.submit or inp.pause:
            self.state = GameState.MENU

    # ------------------------------------------------------------------
    # Word / level progression
    # ------------------------------------------------------------------
    def _submit_word(self):
        puzzle = self.runner.puzzle
        if puzzle.is_correct():
            stars = self.score.award_for_correct()
            self._last_stars_awarded = stars
            self.star_anim.trigger()
            self.feedback.trigger_correct()
            self._advance_timer = constants.CORRECT_AUTO_ADVANCE_DELAY
        else:
            self.score.record_wrong()
            puzzle.trigger_wrong_shake()

    def _after_correct_advance(self):
        self.feedback.dismiss()
        if self.runner.is_last_word:
            self._finish_level()
        else:
            self.runner.advance()
            self.score.start_word()
            self._save_progress()

    def _finish_level(self):
        self.state = GameState.LEVEL_COMPLETE
        self.feedback.trigger_level_complete()
        self._save_progress(level_completed=True)

    def _begin_next_level_or_finish(self):
        self.feedback.dismiss()
        if self.level_index >= len(self.levels) - 1:
            self.state = GameState.GAME_OVER
            return
        self.level_index += 1
        self.runner = entities.LevelRunner(self.levels[self.level_index], 0)
        self._build_wheel_layout()
        self.score.start_word()
        self._save_progress()
        self.state = GameState.PLAYING

    def _save_progress(self, level_completed=False):
        data = {
            "levels_completed": self.level_index + (1 if level_completed else 0),
            "total_stars": self.score.total_stars,
            "last_level": self.level_index,
            "last_word_index": self.runner.word_index,
        }
        self.saver.save(data)
        self._has_saved_game = True

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _build_wheel_layout(self):
        """Recompute rectangles for each wheel in the current word."""
        word = self.runner.puzzle.target
        n = len(word)
        total_w = n * constants.WHEEL_WIDTH + (n - 1) * constants.WHEEL_SPACING
        start_x = (self.screen_width - total_w) // 2
        y = int(self.screen_height * constants.WHEELS_Y_RATIO)
        rects = []
        for i in range(n):
            x = start_x + i * (constants.WHEEL_WIDTH + constants.WHEEL_SPACING)
            rect = pygame.Rect(
                x,
                y - constants.WHEEL_HEIGHT // 2,
                constants.WHEEL_WIDTH,
                constants.WHEEL_HEIGHT,
            )
            rects.append(rect)
        self._wheel_rects = rects

    # ------------------------------------------------------------------
    # Drawing -- menu
    # ------------------------------------------------------------------
    def _draw_menu(self, screen):
        screen.blit(self.bg_surface, (0, 0))

        cx = self.screen_width // 2
        self._draw_centered_text(
            screen, "SpellWheels", cx, 70,
            self.font_title, constants.TITLE_COLOR,
        )
        self._draw_centered_text(
            screen, "A handheld spelling game",
            cx, 120, self.font_menu_small, constants.DARK_GRAY,
        )

        items = [
            "\u25b6  New Game",
            "Continue",
            "Reset Progress",
            "Quit",
        ]

        for idx, label in enumerate(items):
            y = 200 + idx * 55
            selected = idx == self._menu_cursor
            disabled = (idx == constants.MENU_ITEM_RESUME
                        and not self._has_saved_game)
            self._draw_menu_item(screen, cx, y, label, selected, disabled)

        self._draw_centered_text(
            screen,
            "UP/DOWN select  -  ENTER confirm  -  ESC start",
            cx, self.screen_height - 30,
            self.font_menu_small, constants.DARK_GRAY,
        )

    def _draw_menu_item(self, screen, cx, y, label, selected, disabled):
        w, h = 300, 44
        rect = pygame.Rect(cx - w // 2, y - h // 2, w, h)
        bg = constants.YELLOW if selected else constants.PANEL_BG
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(
            screen, constants.PANEL_BORDER, rect, 3, border_radius=10
        )
        color = constants.GRAY if disabled else constants.DARK_GRAY
        self._draw_centered_text(screen, label, cx, y, self.font_menu, color)

    # ------------------------------------------------------------------
    # Drawing -- playing
    # ------------------------------------------------------------------
    def _draw_playing(self, screen):
        screen.blit(self.bg_surface, (0, 0))

        self._draw_progress_bar(screen)
        self._draw_stars_hud(screen)
        self._draw_icon(screen)
        self._draw_wheels(screen)
        self._draw_hud_icons(screen)

        if self.feedback.active and self.feedback.kind == "correct":
            self._draw_correct_feedback(screen)

    def _draw_progress_bar(self, screen):
        """Icon-based footstep path across the top of the screen."""
        n = self.runner.level.word_count
        if n <= 0:
            return
        step_spacing = 40
        total_w = step_spacing * (n - 1)
        start_x = (self.screen_width - total_w) // 2
        y = constants.PROGRESS_Y + 12
        for i in range(n):
            x = start_x + i * step_spacing
            if i < self.runner.word_index:
                color = constants.PROGRESS_DONE
                radius = 12
            elif i == self.runner.word_index:
                color = constants.PROGRESS_CURRENT
                radius = 14
            else:
                color = constants.PROGRESS_TODO
                radius = 10
            pygame.draw.circle(screen, color, (x, y), radius)
            pygame.draw.circle(
                screen, constants.PANEL_BORDER, (x, y), radius, 2
            )

    def _draw_stars_hud(self, screen):
        """Render the running star total as star icons + a small number.

        The number uses block digits and is the only non-settings text
        rendered during gameplay; we limit it to the session total so it
        never dominates the screen.
        """
        x = 12
        y = constants.STAR_BAR_Y
        star_cx = x + 16
        star_cy = y + 16
        scale = 1.0
        if self.star_anim.active:
            scale = self.star_anim.scale
        self._draw_star_icon(screen, star_cx, star_cy, 14 * scale,
                             constants.STAR_COLOR)
        count_surf = self.font_hud.render(
            str(self.score.total_stars), True, constants.DARK_GRAY
        )
        screen.blit(count_surf, (star_cx + 18, y + 4))

    def _draw_icon(self, screen):
        """Draw the big cartoon icon representing the word."""
        cx = self.screen_width // 2
        cy = int(self.screen_height * constants.ICON_Y_RATIO)
        icon_tag = self.runner.current_word_entry.icon_tag
        drawer = _ICON_DRAWERS.get(icon_tag, _draw_icon_default)
        drawer(screen, cx, cy)

    def _draw_wheels(self, screen):
        puzzle = self.runner.puzzle
        now = pygame.time.get_ticks()
        for idx, rect in enumerate(self._wheel_rects):
            wheel = puzzle.wheels[idx]
            active = idx == puzzle.active_index
            shake = puzzle.shake_offset(idx, now)
            self._draw_single_wheel(screen, rect, wheel, active, shake, puzzle, idx)

        # Hint: highlight the first letter of the target above wheel 0
        if puzzle.hint_active and len(self._wheel_rects) > 0:
            self._draw_hint_bubble(screen, puzzle.hint_letter)

    def _draw_single_wheel(self, screen, rect, wheel, active, shake_offset,
                           puzzle, idx):
        drum_rect = rect.move(shake_offset, 0)
        border = (
            constants.WHEEL_ACTIVE_BORDER if active
            else constants.WHEEL_BORDER
        )
        border_width = 4 if active else 3
        pygame.draw.rect(screen, constants.WHEEL_BG, drum_rect,
                         border_radius=12)
        pygame.draw.rect(screen, border, drum_rect, border_width,
                         border_radius=12)

        # Glow effect on active wheel
        if active:
            glow = drum_rect.inflate(8, 8)
            pygame.draw.rect(screen, constants.WHEEL_ACTIVE_BORDER, glow,
                             2, border_radius=14)

        cx = drum_rect.centerx
        cy = drum_rect.centery
        item_h = constants.WHEEL_HEIGHT // 3

        for letter, rel_pos in wheel.visible_letters():
            ny = cy + rel_pos * item_h
            if rel_pos == 0:
                color = constants.WHEEL_LETTER_COLOR
                font = self.font_wheel
            else:
                color = constants.WHEEL_DIM_LETTER_COLOR
                font = self.font_wheel_dim
            surf = font.render(letter, True, color)
            screen.blit(surf, surf.get_rect(center=(cx, ny)))

        # Little arrow glyphs above/below the active wheel
        if active:
            self._draw_arrow(screen, cx, drum_rect.top - 8, up=True)
            self._draw_arrow(screen, cx, drum_rect.bottom + 8, up=False)

    def _draw_hint_bubble(self, screen, letter):
        rect = self._wheel_rects[0]
        bubble = pygame.Rect(rect.left, rect.top - 56, rect.width, 44)
        pygame.draw.rect(screen, constants.HINT_COLOR, bubble,
                         border_radius=10)
        pygame.draw.rect(screen, constants.PANEL_BORDER, bubble, 2,
                         border_radius=10)
        surf = self.font_wheel_dim.render(letter, True, constants.WHITE)
        screen.blit(surf, surf.get_rect(center=bubble.center))

    def _draw_hud_icons(self, screen):
        """Tiny icon hints at the bottom for submit/clear/hint."""
        y = self.screen_height - 28
        icon_size = 18
        gap = 60
        cx = self.screen_width // 2
        # Submit (A) -- green check
        self._draw_icon_button(screen, cx - gap, y,
                               constants.CORRECT_COLOR, "check")
        # Clear (B) -- red cross
        self._draw_icon_button(screen, cx, y, constants.WRONG_COLOR, "x")
        # Hint (Y) -- yellow bulb
        self._draw_icon_button(screen, cx + gap, y, constants.HINT_COLOR,
                               "bulb")

    def _draw_icon_button(self, screen, cx, cy, color, glyph):
        r = 14
        pygame.draw.circle(screen, color, (cx, cy), r)
        pygame.draw.circle(screen, constants.PANEL_BORDER, (cx, cy), r, 2)
        if glyph == "check":
            pts = [(cx - 6, cy), (cx - 1, cy + 5), (cx + 7, cy - 5)]
            pygame.draw.lines(screen, constants.WHITE, False, pts, 3)
        elif glyph == "x":
            pygame.draw.line(screen, constants.WHITE,
                             (cx - 5, cy - 5), (cx + 5, cy + 5), 3)
            pygame.draw.line(screen, constants.WHITE,
                             (cx - 5, cy + 5), (cx + 5, cy - 5), 3)
        elif glyph == "bulb":
            pygame.draw.circle(screen, constants.WHITE, (cx, cy - 1), 5)
            pygame.draw.rect(screen, constants.WHITE,
                             pygame.Rect(cx - 3, cy + 3, 6, 4))

    def _draw_correct_feedback(self, screen):
        cx = self.screen_width // 2
        cy = int(self.screen_height * 0.50)
        alpha = self.feedback.alpha
        # Large check-mark
        check = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(check, (*constants.CORRECT_COLOR, int(220 * alpha)),
                           (60, 60), 50)
        pts = [(30, 62), (50, 82), (90, 40)]
        pygame.draw.lines(
            check, (*constants.WHITE, int(255 * alpha)), False, pts, 8
        )
        screen.blit(check, check.get_rect(center=(cx, cy)))
        # Stars earned flash below
        self._draw_stars_row(screen, cx, cy + 90, self._last_stars_awarded,
                             alpha=alpha)

    def _draw_stars_row(self, screen, cx, cy, count, alpha=1.0):
        gap = 40
        total_w = gap * (constants.MAX_STARS_PER_WORD - 1)
        start_x = cx - total_w // 2
        for i in range(constants.MAX_STARS_PER_WORD):
            color = constants.STAR_COLOR if i < count else constants.STAR_EMPTY_COLOR
            self._draw_star_icon(screen, start_x + i * gap, cy, 18, color,
                                 alpha=alpha)

    # ------------------------------------------------------------------
    # Drawing -- pause / level complete / game over
    # ------------------------------------------------------------------
    def _draw_pause_overlay(self, screen):
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        self._draw_centered_text(
            screen, "Paused", cx, cy - 30,
            self.font_title, constants.WHITE,
        )
        self._draw_centered_text(
            screen, "Press Start / Enter to resume",
            cx, cy + 30, self.font_menu_small, constants.LIGHT_GRAY,
        )

    def _draw_level_complete(self, screen):
        screen.blit(self.bg_surface, (0, 0))
        cx = self.screen_width // 2

        # Big sticker/icon representing the level theme
        cy = int(self.screen_height * 0.35)
        _draw_sticker(screen, cx, cy, 90, constants.YELLOW)

        # Stars row celebrating performance
        self._draw_stars_row(screen, cx, cy + 130, constants.MAX_STARS_PER_WORD)

        # Confetti-like dots
        import random
        random.seed(self.level_index)
        for _ in range(40):
            rx = random.randint(20, self.screen_width - 20)
            ry = random.randint(20, self.screen_height - 20)
            color = random.choice([
                constants.RED, constants.BLUE, constants.GREEN,
                constants.YELLOW, constants.PINK, constants.PURPLE,
            ])
            pygame.draw.circle(screen, color, (rx, ry), 3)

    def _draw_game_over(self, screen):
        screen.blit(self.bg_surface, (0, 0))
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        # A giant trophy icon (stacked rects + circle = cup)
        pygame.draw.circle(screen, constants.YELLOW, (cx, cy - 40), 48)
        pygame.draw.circle(
            screen, constants.ICON_OUTLINE, (cx, cy - 40), 48, 4
        )
        pygame.draw.rect(screen, constants.YELLOW,
                         pygame.Rect(cx - 30, cy, 60, 30))
        pygame.draw.rect(screen, constants.ICON_OUTLINE,
                         pygame.Rect(cx - 30, cy, 60, 30), 4)
        pygame.draw.rect(screen, constants.BROWN,
                         pygame.Rect(cx - 40, cy + 30, 80, 14))
        pygame.draw.rect(screen, constants.ICON_OUTLINE,
                         pygame.Rect(cx - 40, cy + 30, 80, 14), 4)

        # Final star total
        self._draw_stars_row(screen, cx, cy + 90, constants.MAX_STARS_PER_WORD)

    # ------------------------------------------------------------------
    # Low-level drawing helpers
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

    def _draw_centered_text(self, screen, text, x, y, font, color):
        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=(x, y)))

    def _draw_arrow(self, screen, cx, cy, up):
        if up:
            pts = [(cx, cy - 6), (cx - 7, cy + 4), (cx + 7, cy + 4)]
        else:
            pts = [(cx, cy + 6), (cx - 7, cy - 4), (cx + 7, cy - 4)]
        pygame.draw.polygon(screen, constants.WHEEL_ACTIVE_BORDER, pts)

    def _draw_star_icon(self, screen, cx, cy, size, color, alpha=1.0):
        """Draw a 5-point star."""
        pts = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            r = size if i % 2 == 0 else size * 0.45
            pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        if alpha >= 1.0:
            pygame.draw.polygon(screen, color, pts)
            pygame.draw.polygon(screen, constants.ICON_OUTLINE, pts, 2)
        else:
            a = int(255 * alpha)
            surf = pygame.Surface(
                (int(size * 2 + 6), int(size * 2 + 6)), pygame.SRCALPHA
            )
            local_pts = [
                (p[0] - cx + size + 3, p[1] - cy + size + 3) for p in pts
            ]
            pygame.draw.polygon(surf, (*color, a), local_pts)
            pygame.draw.polygon(
                surf, (*constants.ICON_OUTLINE, a), local_pts, 2
            )
            screen.blit(surf, (cx - size - 3, cy - size - 3))


# ----------------------------------------------------------------------
# Icon drawers -- simple cartoon shapes for each word.
#
# These are separate module-level functions so they can be registered in
# the _ICON_DRAWERS table below and easily extended with new words.
# ----------------------------------------------------------------------

_ICON_RADIUS = 70


def _fill_circle(surface, cx, cy, radius, color):
    pygame.draw.circle(surface, color, (cx, cy), radius)
    pygame.draw.circle(surface, constants.ICON_OUTLINE, (cx, cy), radius, 3)


def _fill_rect(surface, rect, color):
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, constants.ICON_OUTLINE, rect, 3, border_radius=8)


def _draw_icon_default(surface, cx, cy):
    _fill_circle(surface, cx, cy, _ICON_RADIUS, constants.LIGHT_GRAY)
    q = surface.subsurface  # noqa: F841 placeholder


def _draw_icon_dog(surface, cx, cy):
    # Body
    _fill_circle(surface, cx, cy + 10, 60, constants.BROWN)
    # Ears
    pygame.draw.ellipse(
        surface, constants.BROWN,
        pygame.Rect(cx - 60, cy - 50, 34, 50)
    )
    pygame.draw.ellipse(
        surface, constants.BROWN,
        pygame.Rect(cx + 26, cy - 50, 34, 50)
    )
    pygame.draw.ellipse(
        surface, constants.ICON_OUTLINE,
        pygame.Rect(cx - 60, cy - 50, 34, 50), 3
    )
    pygame.draw.ellipse(
        surface, constants.ICON_OUTLINE,
        pygame.Rect(cx + 26, cy - 50, 34, 50), 3
    )
    # Eyes
    pygame.draw.circle(surface, constants.BLACK, (cx - 18, cy), 5)
    pygame.draw.circle(surface, constants.BLACK, (cx + 18, cy), 5)
    # Nose
    pygame.draw.circle(surface, constants.BLACK, (cx, cy + 20), 6)


def _draw_icon_cat(surface, cx, cy):
    _fill_circle(surface, cx, cy + 10, 58, constants.GRAY)
    # Triangle ears
    pygame.draw.polygon(
        surface, constants.GRAY,
        [(cx - 50, cy - 20), (cx - 30, cy - 60), (cx - 10, cy - 20)]
    )
    pygame.draw.polygon(
        surface, constants.GRAY,
        [(cx + 50, cy - 20), (cx + 30, cy - 60), (cx + 10, cy - 20)]
    )
    pygame.draw.polygon(
        surface, constants.ICON_OUTLINE,
        [(cx - 50, cy - 20), (cx - 30, cy - 60), (cx - 10, cy - 20)], 3
    )
    pygame.draw.polygon(
        surface, constants.ICON_OUTLINE,
        [(cx + 50, cy - 20), (cx + 30, cy - 60), (cx + 10, cy - 20)], 3
    )
    pygame.draw.circle(surface, constants.GREEN, (cx - 18, cy + 4), 6)
    pygame.draw.circle(surface, constants.GREEN, (cx + 18, cy + 4), 6)
    pygame.draw.circle(surface, constants.BLACK, (cx - 18, cy + 4), 2)
    pygame.draw.circle(surface, constants.BLACK, (cx + 18, cy + 4), 2)
    pygame.draw.polygon(
        surface, constants.PINK,
        [(cx - 5, cy + 20), (cx + 5, cy + 20), (cx, cy + 28)]
    )


def _draw_icon_fish(surface, cx, cy):
    # Body
    pygame.draw.ellipse(
        surface, constants.BLUE,
        pygame.Rect(cx - 70, cy - 35, 120, 70)
    )
    pygame.draw.ellipse(
        surface, constants.ICON_OUTLINE,
        pygame.Rect(cx - 70, cy - 35, 120, 70), 3
    )
    # Tail
    pygame.draw.polygon(
        surface, constants.BLUE,
        [(cx + 40, cy), (cx + 80, cy - 30), (cx + 80, cy + 30)]
    )
    pygame.draw.polygon(
        surface, constants.ICON_OUTLINE,
        [(cx + 40, cy), (cx + 80, cy - 30), (cx + 80, cy + 30)], 3
    )
    pygame.draw.circle(surface, constants.WHITE, (cx - 30, cy - 8), 10)
    pygame.draw.circle(surface, constants.BLACK, (cx - 30, cy - 8), 5)


def _draw_icon_apple(surface, cx, cy):
    _fill_circle(surface, cx, cy + 10, 55, constants.RED)
    # Stem
    pygame.draw.rect(
        surface, constants.BROWN,
        pygame.Rect(cx - 3, cy - 50, 6, 18)
    )
    # Leaf
    pygame.draw.ellipse(
        surface, constants.GREEN,
        pygame.Rect(cx + 3, cy - 52, 28, 14)
    )
    pygame.draw.ellipse(
        surface, constants.ICON_OUTLINE,
        pygame.Rect(cx + 3, cy - 52, 28, 14), 2
    )


def _draw_icon_sun(surface, cx, cy):
    # Rays
    for i in range(12):
        angle = i * (math.pi * 2 / 12)
        x1 = cx + math.cos(angle) * 50
        y1 = cy + math.sin(angle) * 50
        x2 = cx + math.cos(angle) * 80
        y2 = cy + math.sin(angle) * 80
        pygame.draw.line(surface, constants.ORANGE, (x1, y1), (x2, y2), 6)
    _fill_circle(surface, cx, cy, 45, constants.YELLOW)
    pygame.draw.circle(surface, constants.BLACK, (cx - 12, cy - 5), 4)
    pygame.draw.circle(surface, constants.BLACK, (cx + 12, cy - 5), 4)
    pygame.draw.arc(
        surface, constants.BLACK,
        pygame.Rect(cx - 14, cy, 28, 16), math.pi, 2 * math.pi, 3
    )


def _draw_icon_moon(surface, cx, cy):
    _fill_circle(surface, cx, cy, 55, constants.LIGHT_GRAY)
    # Crescent cut-out
    pygame.draw.circle(
        surface, constants.BG_GRADIENT_TOP, (cx + 20, cy - 5), 45
    )
    pygame.draw.circle(
        surface, constants.ICON_OUTLINE, (cx + 20, cy - 5), 45, 3
    )


def _draw_icon_star(surface, cx, cy):
    size = 65
    pts = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = size if i % 2 == 0 else size * 0.45
        pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    pygame.draw.polygon(surface, constants.YELLOW, pts)
    pygame.draw.polygon(surface, constants.ICON_OUTLINE, pts, 3)


def _draw_icon_tree(surface, cx, cy):
    # Trunk
    pygame.draw.rect(
        surface, constants.BROWN,
        pygame.Rect(cx - 10, cy + 20, 20, 50)
    )
    pygame.draw.rect(
        surface, constants.ICON_OUTLINE,
        pygame.Rect(cx - 10, cy + 20, 20, 50), 3
    )
    # Foliage as three overlapping circles
    pygame.draw.circle(surface, constants.GREEN, (cx, cy - 20), 40)
    pygame.draw.circle(surface, constants.GREEN, (cx - 28, cy), 32)
    pygame.draw.circle(surface, constants.GREEN, (cx + 28, cy), 32)
    pygame.draw.circle(surface, constants.ICON_OUTLINE, (cx, cy - 20), 40, 3)
    pygame.draw.circle(
        surface, constants.ICON_OUTLINE, (cx - 28, cy), 32, 3
    )
    pygame.draw.circle(
        surface, constants.ICON_OUTLINE, (cx + 28, cy), 32, 3
    )


def _draw_icon_house(surface, cx, cy):
    body = pygame.Rect(cx - 55, cy, 110, 70)
    _fill_rect(surface, body, constants.YELLOW)
    roof = [(cx - 70, cy), (cx, cy - 55), (cx + 70, cy)]
    pygame.draw.polygon(surface, constants.RED, roof)
    pygame.draw.polygon(surface, constants.ICON_OUTLINE, roof, 3)
    door = pygame.Rect(cx - 15, cy + 25, 30, 45)
    _fill_rect(surface, door, constants.BROWN)
    # Window
    win = pygame.Rect(cx - 48, cy + 12, 20, 20)
    _fill_rect(surface, win, constants.BLUE)


def _draw_icon_car(surface, cx, cy):
    body = pygame.Rect(cx - 70, cy - 5, 140, 40)
    _fill_rect(surface, body, constants.RED)
    cabin = pygame.Rect(cx - 45, cy - 35, 70, 35)
    _fill_rect(surface, cabin, constants.BLUE)
    # Wheels
    _fill_circle(surface, cx - 40, cy + 40, 16, constants.DARK_GRAY)
    _fill_circle(surface, cx + 40, cy + 40, 16, constants.DARK_GRAY)


def _draw_sticker(surface, cx, cy, size, color):
    """Big celebratory sticker used on level-complete screen."""
    pts = []
    for i in range(20):
        angle = i * (math.pi * 2 / 20)
        r = size if i % 2 == 0 else size * 0.75
        pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, constants.ICON_OUTLINE, pts, 3)
    # Smiley face
    pygame.draw.circle(surface, constants.BLACK, (cx - 20, cy - 10), 6)
    pygame.draw.circle(surface, constants.BLACK, (cx + 20, cy - 10), 6)
    pygame.draw.arc(
        surface, constants.BLACK,
        pygame.Rect(cx - 25, cy, 50, 30), math.pi, 2 * math.pi, 4
    )


_ICON_DRAWERS = {
    "dog": _draw_icon_dog,
    "cat": _draw_icon_cat,
    "fish": _draw_icon_fish,
    "apple": _draw_icon_apple,
    "sun": _draw_icon_sun,
    "moon": _draw_icon_moon,
    "star": _draw_icon_star,
    "tree": _draw_icon_tree,
    "house": _draw_icon_house,
    "car": _draw_icon_car,
}