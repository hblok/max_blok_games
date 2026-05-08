# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Keyboard and gamepad input aggregation for TankBattle."""

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import utils


class InputState:
    """Aggregated keyboard and gamepad input."""

    def __init__(self):
        self.drive = 0.0
        self.turn = 0.0
        self.turret_x = 0.0
        self.turret_y = 0.0
        self.fire_primary = False
        self.fire_secondary = False
        self.pause = False
        self.confirm = False
        self.menu_y = 0
        self.quit = False


class InputReader:
    """Read keyboard and gamepad state into an InputState."""

    def __init__(self, pygame_module):
        self.pygame = pygame_module
        self._joystick = None
        self._joystick_initialized = False
        self._init_joystick()

    def _init_joystick(self):
        """Initialize the first available joystick."""
        try:
            self.pygame.joystick.init()
            if self.pygame.joystick.get_count() > 0:
                self._joystick = self.pygame.joystick.Joystick(0)
                self._joystick.init()
                self._joystick_initialized = True
        except Exception:
            self._joystick = None
            self._joystick_initialized = False

    def _check_joystick_reconnect(self):
        """Check if a joystick has been connected and initialize it."""
        if self._joystick_initialized and self._joystick is not None:
            try:
                _ = self._joystick.get_axis(0)
                return
            except Exception:
                self._joystick = None
                self._joystick_initialized = False
        try:
            if self.pygame.joystick.get_count() > 0:
                self._joystick = self.pygame.joystick.Joystick(0)
                self._joystick.init()
                self._joystick_initialized = True
        except Exception:
            self._joystick = None
            self._joystick_initialized = False

    def read(self):
        """Return current input state."""
        state = InputState()
        self._read_events(state)
        self._read_keyboard_axes(state)
        self._read_joystick(state)
        state.drive, state.turn = utils.normalize_input_vector(state.drive, state.turn)
        state.turret_x, state.turret_y = utils.normalize_input_vector(
            state.turret_x,
            state.turret_y,
        )
        return state

    def _read_events(self, state):
        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                state.quit = True
            elif event.type == self.pygame.KEYDOWN:
                self._read_keydown(event, state)
            elif event.type == self.pygame.KEYUP:
                pass
            elif event.type == self.pygame.JOYBUTTONDOWN:
                self._read_joybutton(event, state)
            elif event.type == self.pygame.JOYDEVICEADDED:
                self._check_joystick_reconnect()
            elif event.type == self.pygame.JOYDEVICEREMOVED:
                self._joystick = None
                self._joystick_initialized = False

    def _read_keydown(self, event, state):
        if event.key == self.pygame.K_ESCAPE:
            state.pause = True
        if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
            state.confirm = True
        if event.key == self.pygame.K_SPACE:
            state.fire_primary = True
        if event.key in (self.pygame.K_LCTRL, self.pygame.K_RCTRL):
            state.fire_secondary = True
        if event.key in (self.pygame.K_UP, self.pygame.K_w):
            state.menu_y = -1
        if event.key in (self.pygame.K_DOWN, self.pygame.K_s):
            state.menu_y = 1

    def _read_keyboard_axes(self, state):
        keys = self.pygame.key.get_pressed()
        up = keys[self.pygame.K_UP] or keys[self.pygame.K_w]
        down = keys[self.pygame.K_DOWN] or keys[self.pygame.K_s]
        left = keys[self.pygame.K_LEFT] or keys[self.pygame.K_a]
        right = keys[self.pygame.K_RIGHT] or keys[self.pygame.K_d]
        if up and not down:
            state.drive = -1.0
        elif down and not up:
            state.drive = 1.0
        if left and not right:
            state.turn = -1.0
        elif right and not left:
            state.turn = 1.0
        state.turret_x = float(keys[self.pygame.K_l]) - float(keys[self.pygame.K_j])
        state.turret_y = float(keys[self.pygame.K_k]) - float(keys[self.pygame.K_i])

    def _read_joystick(self, state):
        self._check_joystick_reconnect()
        if not self._joystick_initialized or self._joystick is None:
            return
        try:
            left_x = 0.0
            left_y = 0.0
            right_x = 0.0
            right_y = 0.0
            num_axes = self._joystick.get_numaxes()
            if num_axes >= 2:
                left_x = utils.apply_deadzone(self._joystick.get_axis(0))
                left_y = utils.apply_deadzone(self._joystick.get_axis(1))
            if num_axes >= 4:
                right_x = utils.apply_deadzone(self._joystick.get_axis(2))
                right_y = utils.apply_deadzone(self._joystick.get_axis(3))
            elif num_axes >= 6:
                right_x = utils.apply_deadzone(self._joystick.get_axis(3))
                right_y = utils.apply_deadzone(self._joystick.get_axis(4))
            state.turn += left_x
            state.drive += left_y
            if abs(right_x) > 0.0 or abs(right_y) > 0.0:
                state.turret_x += right_x
                state.turret_y += right_y
            self._read_joystick_hat(state)
        except Exception:
            self._joystick = None
            self._joystick_initialized = False

    def _read_joystick_hat(self, state):
        if not self._joystick_initialized or self._joystick is None:
            return
        try:
            num_hats = self._joystick.get_numhats()
            if num_hats > 0:
                hat_x, hat_y = self._joystick.get_hat(0)
                if hat_x != 0 or hat_y != 0:
                    state.turn += float(hat_x)
                    state.drive -= float(hat_y)
                    if hat_y < 0:
                        state.menu_y = -1
                    elif hat_y > 0:
                        state.menu_y = 1
        except Exception:
            pass

    def _read_joybutton(self, event, state):
        if event.button in (0, 1):
            state.confirm = True
        if event.button == 0:
            state.fire_primary = True
        if event.button == 1:
            state.fire_secondary = True
        if event.button in (6, 7):
            state.fire_secondary = True
        if event.button in (4, 5):
            state.fire_primary = True
        if event.button in (7, 8, 13, 9, 10):
            state.pause = True
        if event.button in (11, 12):
            if event.button == 11:
                state.menu_y = -1
            else:
                state.menu_y = 1

    def cleanup(self):
        """Clean up joystick resources."""
        if self._joystick is not None:
            try:
                self._joystick.quit()
            except Exception:
                pass
            self._joystick = None
            self._joystick_initialized = False
