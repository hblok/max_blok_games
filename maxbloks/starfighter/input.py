# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
input.py — Keyboard and joystick input mapping.

Exposes a simple InputState that the game loop reads each frame.
"""

import pygame
from maxbloks.starfighter.settings import (
    JOYSTICK_DEADZONE,
    JOYSTICK_FIRE_BUTTONS,
    JOYSTICK_PAUSE_BUTTONS,
)


class InputState:
    """Logical game actions — updated once per frame."""

    __slots__ = (
        "rotate_left", "rotate_right", "thrust",
        "fire", "pause_pressed", "confirm", "back",
        "quit_requested",
    )

    def __init__(self):
        self.rotate_left = False
        self.rotate_right = False
        self.thrust = False
        self.fire = False
        self.pause_pressed = False   # edge-triggered (single press)
        self.confirm = False         # edge-triggered
        self.back = False            # edge-triggered
        self.quit_requested = False


class InputHandler:
    """
    Reads Pygame events + held-key / joystick state and produces
    an InputState each frame.
    """

    def __init__(self):
        self._joystick = None
        self._init_joystick()
        # Track previous frame for edge detection
        self._prev_pause = False
        self._prev_fire = False

    # ------------------------------------------------------------------
    def _init_joystick(self):
        """Attempt to open the first available joystick."""
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()

    # ------------------------------------------------------------------
    def update(self) -> InputState:
        """
        Call once per frame **after** pygame.event.pump() / get().
        Returns a fresh InputState.
        """
        state = InputState()

        # --- Process event queue (edge-triggered actions) -------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state.quit_requested = True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    state.pause_pressed = True
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    state.confirm = True
                if event.key == pygame.K_BACKSPACE:
                    state.back = True

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button in JOYSTICK_PAUSE_BUTTONS:
                    state.pause_pressed = True
                if event.button in JOYSTICK_FIRE_BUTTONS:
                    state.confirm = True

            # Hot-plug joystick support
            elif event.type == pygame.JOYDEVICEADDED:
                self._init_joystick()
            elif event.type == pygame.JOYDEVICEREMOVED:
                self._joystick = None

        # --- Held keys (continuous actions) ---------------------------
        keys = pygame.key.get_pressed()
        state.rotate_left = keys[pygame.K_LEFT]
        state.rotate_right = keys[pygame.K_RIGHT]
        state.thrust = keys[pygame.K_UP]
        state.fire = keys[pygame.K_SPACE]

        # --- Joystick (continuous) ------------------------------------
        js = self._joystick
        if js is not None:
            try:
                # D-pad via hat
                if js.get_numhats() > 0:
                    hx, hy = js.get_hat(0)
                    if hx < 0:
                        state.rotate_left = True
                    elif hx > 0:
                        state.rotate_right = True
                    if hy > 0:          # hat Y is inverted on many pads
                        state.thrust = True

                # Analog stick
                if js.get_numaxes() >= 2:
                    ax = js.get_axis(0)
                    ay = js.get_axis(1)
                    if ax < -JOYSTICK_DEADZONE:
                        state.rotate_left = True
                    elif ax > JOYSTICK_DEADZONE:
                        state.rotate_right = True
                    if ay < -JOYSTICK_DEADZONE:
                        state.thrust = True

                # Fire button (held)
                for btn in JOYSTICK_FIRE_BUTTONS:
                    if btn < js.get_numbuttons() and js.get_button(btn):
                        state.fire = True
            except pygame.error:
                self._joystick = None

        return state