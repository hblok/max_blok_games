# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Input handling for SpellWheels.

Translates keyboard and gamepad events into a semantic ``InputState``
suitable for the game state machine.

Controls (from design spec):
    D-Pad Left/Right   -> move between wheels       (Arrow Left/Right)
    D-Pad Up/Down      -> spin active wheel         (Arrow Up/Down)
    A button           -> submit word               (Space/Enter)
    B button           -> clear/undo active wheel   (Backspace)
    Y button           -> visual hint               (H key)
    Start              -> pause / open menu         (Escape)
    Select             -> world / level map        (Tab)
    Buttons 8/13       -> system exit               (Q or Alt+F4)

The analog-stick deadzone is 0.2; diagonals are normalized by 0.707.
"""

import pygame

from maxbloks.spellwheels import constants


class InputState:
    """Edge-triggered actions for the current frame."""

    __slots__ = (
        "move_left", "move_right",
        "spin_up", "spin_down",
        "submit", "clear", "hint",
        "pause", "map_view",
        "quit_requested",
    )

    def __init__(self):
        self.move_left = False
        self.move_right = False
        self.spin_up = False
        self.spin_down = False
        self.submit = False
        self.clear = False
        self.hint = False
        self.pause = False
        self.map_view = False
        self.quit_requested = False


class InputHandler:
    """Collects events and returns a per-frame InputState."""

    def __init__(self):
        self._joystick = None
        self._init_joystick()
        # Track whether the analog stick was already "held" past the
        # deadzone in the previous frame, so we can emit one event per
        # press rather than one per frame.
        self._axis_x_held = False
        self._axis_y_held = False

    def _init_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()

    # ------------------------------------------------------------------
    def update(self):
        state = InputState()

        for event in pygame.event.get():
            self._handle_event(event, state)

        self._read_joystick_axes(state)
        return state

    # ------------------------------------------------------------------
    def _handle_event(self, event, state):
        if event.type == pygame.QUIT:
            state.quit_requested = True

        elif event.type == pygame.KEYDOWN:
            self._handle_keydown(event, state)

        elif event.type == pygame.JOYBUTTONDOWN:
            self._handle_joybutton(event, state)

        elif event.type == pygame.JOYHATMOTION:
            self._handle_hat(event, state)

        elif event.type == pygame.JOYDEVICEADDED:
            self._init_joystick()
        elif event.type == pygame.JOYDEVICEREMOVED:
            self._joystick = None

    def _handle_keydown(self, event, state):
        key = event.key
        if key in (pygame.K_LEFT, pygame.K_a):
            state.move_left = True
        elif key in (pygame.K_RIGHT, pygame.K_d):
            state.move_right = True
        elif key in (pygame.K_UP, pygame.K_w):
            state.spin_up = True
        elif key in (pygame.K_DOWN, pygame.K_s):
            state.spin_down = True
        elif key in (pygame.K_SPACE, pygame.K_RETURN):
            state.submit = True
        elif key == pygame.K_BACKSPACE:
            state.clear = True
        elif key == pygame.K_h:
            state.hint = True
        elif key == pygame.K_ESCAPE:
            state.pause = True
        elif key == pygame.K_TAB:
            state.map_view = True
        elif key == pygame.K_q:
            state.quit_requested = True
        elif key == pygame.K_F4 and (pygame.key.get_mods() & pygame.KMOD_ALT):
            state.quit_requested = True

    def _handle_joybutton(self, event, state):
        btn = event.button
        if btn == constants.BTN_A:
            state.submit = True
        elif btn == constants.BTN_B:
            state.clear = True
        elif btn == constants.BTN_Y:
            state.hint = True
        elif btn == constants.BTN_START:
            state.pause = True
        elif btn == constants.BTN_SELECT:
            state.map_view = True
        elif btn in (constants.BTN_EXIT_1, constants.BTN_EXIT_2):
            state.quit_requested = True

    def _handle_hat(self, event, state):
        hx, hy = event.value
        if hx < 0:
            state.move_left = True
        elif hx > 0:
            state.move_right = True
        if hy > 0:
            state.spin_up = True
        elif hy < 0:
            state.spin_down = True

    def _read_joystick_axes(self, state):
        js = self._joystick
        if js is None:
            return
        try:
            if js.get_numaxes() < 2:
                return
            ax = js.get_axis(0)
            ay = js.get_axis(1)
        except pygame.error:
            self._joystick = None
            return

        # Horizontal axis (edge-triggered)
        if abs(ax) > constants.JOYSTICK_AXIS_THRESHOLD:
            if not self._axis_x_held:
                self._axis_x_held = True
                if ax < 0:
                    state.move_left = True
                else:
                    state.move_right = True
        elif abs(ax) < constants.JOYSTICK_DEADZONE:
            self._axis_x_held = False

        # Vertical axis (edge-triggered)
        if abs(ay) > constants.JOYSTICK_AXIS_THRESHOLD:
            if not self._axis_y_held:
                self._axis_y_held = True
                if ay < 0:
                    state.spin_up = True
                else:
                    state.spin_down = True
        elif abs(ay) < constants.JOYSTICK_DEADZONE:
            self._axis_y_held = False