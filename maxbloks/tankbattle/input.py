# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Keyboard and gamepad input aggregation for TankBattle."""

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

    def read(self):
        """Return current input state."""
        state = InputState()
        self._read_events(state)
        self._read_keyboard_axes(state)
        self._read_joystick_axes(state)
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
            elif event.type == self.pygame.JOYBUTTONDOWN:
                self._read_joybutton(event, state)

    def _read_keydown(self, event, state):
        if event.key == self.pygame.K_ESCAPE:
            state.pause = True
        if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
            state.confirm = True
        if event.key == self.pygame.K_SPACE:
            state.fire_primary = True
        if event.key in (self.pygame.K_LCTRL, self.pygame.K_RCTRL):
            state.fire_secondary = True
        if event.key == self.pygame.K_UP:
            state.menu_y = -1
        if event.key == self.pygame.K_DOWN:
            state.menu_y = 1

    def _read_joybutton(self, event, state):
        if event.button in (0, 1):
            state.confirm = True
        if event.button == 0:
            state.fire_primary = True
        if event.button == 1:
            state.fire_secondary = True
        if event.button in (7, 8, 13):
            state.pause = True

    def _read_keyboard_axes(self, state):
        keys = self.pygame.key.get_pressed()
        state.drive = float(keys[self.pygame.K_s] or keys[self.pygame.K_DOWN])
        state.drive -= float(keys[self.pygame.K_w] or keys[self.pygame.K_UP])
        state.turn = float(keys[self.pygame.K_d] or keys[self.pygame.K_RIGHT])
        state.turn -= float(keys[self.pygame.K_a] or keys[self.pygame.K_LEFT])
        state.turret_x = float(keys[self.pygame.K_l]) - float(keys[self.pygame.K_j])
        state.turret_y = float(keys[self.pygame.K_k]) - float(keys[self.pygame.K_i])

    def _read_joystick_axes(self, state):
        if self.pygame.joystick.get_count() <= 0:
            return
        joystick = self.pygame.joystick.Joystick(0)
        if not joystick.get_init():
            joystick.init()
        state.turn += utils.apply_deadzone(joystick.get_axis(0))
        state.drive += utils.apply_deadzone(joystick.get_axis(1))
        if joystick.get_numaxes() >= 4:
            state.turret_x += utils.apply_deadzone(joystick.get_axis(2))
            state.turret_y += utils.apply_deadzone(joystick.get_axis(3))