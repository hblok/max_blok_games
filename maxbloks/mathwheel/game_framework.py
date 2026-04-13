# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Base game framework for MathWheel, adapted from the fish game."""

import sys
import pygame


class GameFramework:
    """Base class for games with common functionality."""

    def __init__(self, screen, display_info, title="Game", fps=60):
        pygame.init()
        pygame.joystick.init()

        self.screen = screen
        self.screen_width = display_info["width"]
        self.screen_height = display_info["height"]
        self.FPS = fps

        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()

        # Joystick setup
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        # Game state
        self.running = True

        # Input state
        self.keys_pressed = set()
        self.keys_just_pressed = set()

        # shoot_button  = A button (joystick 0/1) / Space / Enter
        #                 → select number AND submit answer in one press
        self.shoot_button_pressed = False

        # action_button = X button (joystick 3) / keyboard X
        #                 → open in-game menu
        self.action_button_pressed = False

        # back_button   = keyboard Escape only
        #                 → close menu / navigate back
        self.back_button_pressed = False

        # skip_button   = D-pad right (hat 0, x=+1) / keyboard Right arrow
        #                 → skip current question
        self.skip_button_pressed = False

        self.movement_x = 0
        self.movement_y = 0

        # Joystick axis tracking for digital-style input
        self._joy_axis_y_held = False
        self._joy_axis_x_held = False

    def handle_input(self):
        """Handle common input from keyboard and gamepad."""
        self.keys_just_pressed.clear()
        self.shoot_button_pressed = False
        self.action_button_pressed = False
        self.back_button_pressed = False
        self.skip_button_pressed = False
        self.movement_x = 0
        self.movement_y = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                self.keys_just_pressed.add(event.key)
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.shoot_button_pressed = True
                if event.key == pygame.K_x:
                    self.action_button_pressed = True
                if event.key == pygame.K_ESCAPE:
                    self.back_button_pressed = True

            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)

            elif event.type == pygame.JOYBUTTONDOWN:
                # Buttons 8 / 13 = Menu/Start → exit game
                if event.button in (8, 13):
                    self.running = False
                # Buttons 0 / 1 = A / B → submit answer
                elif event.button in (0, 1):
                    self.shoot_button_pressed = True
                # Button 3 = X → open in-game menu
                elif event.button == 3:
                    self.action_button_pressed = True

            elif event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = event.value
                # Hat up/down → scroll wheel
                if hat_y != 0:
                    self.movement_y = -hat_y
                # Hat right → skip question  (hat_x == +1)
                # Hat left  → scroll left / nothing special in this game
                if hat_x == 1:
                    self.skip_button_pressed = True
                elif hat_x == -1:
                    self.movement_x = -1

        # Keyboard directional just-pressed
        if pygame.K_UP in self.keys_just_pressed or pygame.K_w in self.keys_just_pressed:
            self.movement_y = -1
        if pygame.K_DOWN in self.keys_just_pressed or pygame.K_s in self.keys_just_pressed:
            self.movement_y = 1
        if pygame.K_LEFT in self.keys_just_pressed or pygame.K_a in self.keys_just_pressed:
            self.movement_x = -1
        # Keyboard Right / D also triggers skip (mirrors D-pad right)
        if pygame.K_RIGHT in self.keys_just_pressed or pygame.K_d in self.keys_just_pressed:
            self.skip_button_pressed = True

        # Joystick axis as digital input (with edge detection)
        if self.joystick:
            axis_y = self.joystick.get_axis(1)
            axis_x = self.joystick.get_axis(0)
            threshold = 0.5

            if abs(axis_y) > threshold:
                if not self._joy_axis_y_held:
                    self._joy_axis_y_held = True
                    self.movement_y = 1 if axis_y > 0 else -1
            else:
                self._joy_axis_y_held = False

            if abs(axis_x) > threshold:
                if not self._joy_axis_x_held:
                    self._joy_axis_x_held = True
                    # Axis right is NOT skip — only hat right is skip.
                    # Axis is used for UI navigation in menus only.
                    self.movement_x = 1 if axis_x > 0 else -1
            else:
                self._joy_axis_x_held = False

    def update(self):
        """Override with game logic."""
        pass

    def draw(self):
        """Override with drawing code."""
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def draw_text(self, text, x, y, size=24, color=None, center=False):
        """Helper to draw text on screen."""
        if color is None:
            color = (255, 255, 255)
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, (x, y))

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()