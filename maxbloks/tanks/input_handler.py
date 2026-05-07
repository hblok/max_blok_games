# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
from dataclasses import dataclass


@dataclass
class InputState:
    """Current state of all inputs."""
    axis_x: float = 0.0
    axis_y: float = 0.0
    fire_pressed: bool = False
    fire_just_pressed: bool = False
    restart_pressed: bool = False
    restart_just_pressed: bool = False
    exit_pressed: bool = False


class InputHandler:
    """Handles joystick and keyboard input."""

    def __init__(self, game_config):
        self.config = game_config
        self.joystick = None
        self.previous_fire_state = False
        self.previous_restart_state = False
        self._initialize_joystick()

    def _initialize_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick initialized: {self.joystick.get_name()}")
        else:
            print("No joystick detected")

    def get_input_state(self) -> InputState:
        """Get current input state from joystick or keyboard."""
        if self.joystick:
            state = self._get_joystick_input()
        else:
            state = self._get_keyboard_input()

        state.fire_just_pressed = state.fire_pressed and not self.previous_fire_state
        state.restart_just_pressed = state.restart_pressed and not self.previous_restart_state

        self.previous_fire_state = state.fire_pressed
        self.previous_restart_state = state.restart_pressed

        return state

    def _get_joystick_input(self) -> InputState:
        state = InputState()

        if self.joystick.get_numaxes() >= 2:
            state.axis_x = self.joystick.get_axis(0)
            state.axis_y = self.joystick.get_axis(1)

        if self.joystick.get_numbuttons() > self.config.button_fire:
            state.fire_pressed = bool(self.joystick.get_button(self.config.button_fire))

        if self.joystick.get_numbuttons() > self.config.button_restart:
            state.restart_pressed = bool(self.joystick.get_button(self.config.button_restart))

        if self.joystick.get_numbuttons() > self.config.button_exit_1:
            if self.joystick.get_button(self.config.button_exit_1):
                state.exit_pressed = True
        if self.joystick.get_numbuttons() > self.config.button_exit_2:
            if self.joystick.get_button(self.config.button_exit_2):
                state.exit_pressed = True

        dz = getattr(self.config, "joystick_deadzone", 0.15)
        if abs(state.axis_x) < dz:
            state.axis_x = 0.0
        if abs(state.axis_y) < dz:
            state.axis_y = 0.0

        return state

    def _get_keyboard_input(self) -> InputState:
        state = InputState()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            state.axis_x = -1.0
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            state.axis_x = 1.0

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            state.axis_y = -1.0
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            state.axis_y = 1.0

        state.fire_pressed = keys[pygame.K_SPACE]
        state.restart_pressed = keys[pygame.K_b]

        return state
