# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Keyboard and gamepad input aggregation for TankBattle.

Implements button debounce via rising-edge detection so that held buttons
only register once per press, matching the pattern from the reference
tanks game.
"""

from maxbloks.tankbattle import constants
from maxbloks.tankbattle import utils


class InputState:
    """Aggregated keyboard and gamepad input.

    Continuous (held) fields end in ``_pressed``; edge-detected
    (just-pressed) fields end in ``_just_pressed``.  UI handlers
    should prefer the ``_just_pressed`` variants to avoid bounce.
    """

    def __init__(self):
        # Movement axes (continuous)
        self.drive = 0.0
        self.turn = 0.0
        self.turret_x = 0.0
        self.turret_y = 0.0

        # Continuous (held) button states
        self.fire_primary_pressed = False
        self.fire_secondary_pressed = False
        self.pause_pressed = False
        self.confirm_pressed = False
        self.exit_pressed = False

        # Edge-detected (rising-edge) button states — True only on
        # the frame the button transitions from released to pressed.
        self.fire_primary_just_pressed = False
        self.fire_secondary_just_pressed = False
        self.pause_just_pressed = False
        self.confirm_just_pressed = False
        self.exit_just_pressed = False

        # Navigation — continuous held states for menu up/down.
        # These are used by the rising-edge detector to produce
        # menu_up_just_pressed / menu_down_just_pressed.
        self.menu_up_pressed = False
        self.menu_down_pressed = False

        # Navigation — edge-detected (one position per press).
        self.menu_up_just_pressed = False
        self.menu_down_just_pressed = False

        # Legacy field kept for backward compatibility with hat events
        # that already fire once per press.  Prefer menu_up/down_just_pressed
        # in new code.
        self.menu_y = 0

        self.quit = False


class InputReader:
    """Read keyboard and gamepad state into an InputState.

    Button debounce is implemented by tracking the previous-frame
    held state of each button and computing a rising-edge flag
    (``just_pressed``) that is True only on the first frame a button
    is held.  This prevents rapid re-triggering from controller
    bounce or repeated KEYDOWN events.

    Navigation debounce follows the same pattern: menu_up_pressed
    and menu_down_pressed are continuous held states, and the
    corresponding _just_pressed flags fire only on the rising edge,
    ensuring one menu step per physical press.
    """

    def __init__(self, pygame_module):
        self.pygame = pygame_module
        self._joystick = None
        self._joystick_initialized = False
        # Previous-frame held states for debounce
        self._prev_fire_primary = False
        self._prev_fire_secondary = False
        self._prev_pause = False
        self._prev_confirm = False
        self._prev_exit = False
        self._prev_menu_up = False
        self._prev_menu_down = False
        # Turret input smoothing (low-pass filter)
        self._smooth_turret_x = 0.0
        self._smooth_turret_y = 0.0
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
        """Return current input state with edge-detected buttons."""
        state = InputState()
        self._read_events(state)
        self._read_keyboard_axes(state)
        self._read_joystick(state)
        # Normalize movement axes
        state.drive, state.turn = utils.normalize_input_vector(state.drive, state.turn)
        # Smooth turret input to prevent jitter and cardinal-direction snapping
        state.turret_x, state.turret_y = self._smooth_turret_input(
            utils.normalize_input_vector(state.turret_x, state.turret_y),
        )
        # Compute rising-edge (just_pressed) flags for debounce
        state.fire_primary_just_pressed = (
            state.fire_primary_pressed and not self._prev_fire_primary
        )
        state.fire_secondary_just_pressed = (
            state.fire_secondary_pressed and not self._prev_fire_secondary
        )
        state.pause_just_pressed = (
            state.pause_pressed and not self._prev_pause
        )
        state.confirm_just_pressed = (
            state.confirm_pressed and not self._prev_confirm
        )
        state.exit_just_pressed = (
            state.exit_pressed and not self._prev_exit
        )
        state.menu_up_just_pressed = (
            state.menu_up_pressed and not self._prev_menu_up
        )
        state.menu_down_just_pressed = (
            state.menu_down_pressed and not self._prev_menu_down
        )
        # Store current held states for next frame's edge detection
        self._prev_fire_primary = state.fire_primary_pressed
        self._prev_fire_secondary = state.fire_secondary_pressed
        self._prev_pause = state.pause_pressed
        self._prev_confirm = state.confirm_pressed
        self._prev_exit = state.exit_pressed
        self._prev_menu_up = state.menu_up_pressed
        self._prev_menu_down = state.menu_down_pressed
        return state

    def _smooth_turret_input(self, raw_vector):
        """Apply exponential smoothing to turret input to reduce jitter.

        This prevents the turret from snapping erratically when the
        right stick is near the deadzone boundary or when controller
        noise causes rapid direction changes.
        """
        smoothing = constants.TURRET_INPUT_SMOOTHING
        sx = self._smooth_turret_x * smoothing + raw_vector[0] * (1.0 - smoothing)
        sy = self._smooth_turret_y * smoothing + raw_vector[1] * (1.0 - smoothing)
        self._smooth_turret_x = sx
        self._smooth_turret_y = sy
        return sx, sy

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
            elif event.type == self.pygame.JOYBUTTONUP:
                pass
            elif event.type == self.pygame.JOYDEVICEADDED:
                self._check_joystick_reconnect()
            elif event.type == self.pygame.JOYDEVICEREMOVED:
                self._joystick = None
                self._joystick_initialized = False

    def _read_keydown(self, event, state):
        if event.key == self.pygame.K_ESCAPE:
            state.pause_pressed = True
        if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
            state.confirm_pressed = True
        if event.key == self.pygame.K_SPACE:
            state.fire_primary_pressed = True
        if event.key in (self.pygame.K_LCTRL, self.pygame.K_RCTRL):
            state.fire_secondary_pressed = True
        if event.key in (self.pygame.K_UP, self.pygame.K_w):
            state.menu_up_pressed = True
        if event.key in (self.pygame.K_DOWN, self.pygame.K_s):
            state.menu_down_pressed = True

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
            # Left stick drives the tank via move-toward-stick scheme
            state.turn += left_x
            state.drive += left_y
            if abs(right_x) > 0.0 or abs(right_y) > 0.0:
                state.turret_x += right_x
                state.turret_y += right_y
            # Read joystick button held states via polling
            self._read_joystick_buttons(state)
            self._read_joystick_hat(state)
        except Exception:
            self._joystick = None
            self._joystick_initialized = False

    def _read_joystick_buttons(self, state):
        """Read current held state of joystick buttons via polling.

        Rather than reacting to individual JOYBUTTONDOWN events (which
        can bounce on some controllers), we poll the current held state
        each frame and rely on the rising-edge detection in ``read()``
        to debounce.

        Buttons 8 and 13 are mapped to exit (Back/Select and
        Menu/Home on common controllers), which will quit the game
        via exit_just_pressed in the game's main input handler.
        """
        if not self._joystick_initialized or self._joystick is None:
            return
        try:
            num_buttons = self._joystick.get_numbuttons()
            if num_buttons > 0 and self._joystick.get_button(0):
                state.fire_primary_pressed = True
                state.confirm_pressed = True
            if num_buttons > 1 and self._joystick.get_button(1):
                state.fire_secondary_pressed = True
                state.confirm_pressed = True
            if num_buttons > 4 and self._joystick.get_button(4):
                state.fire_primary_pressed = True
            if num_buttons > 5 and self._joystick.get_button(5):
                state.fire_primary_pressed = True
            if num_buttons > 6 and self._joystick.get_button(6):
                state.fire_secondary_pressed = True
            if num_buttons > 7 and self._joystick.get_button(7):
                state.pause_pressed = True
                state.fire_secondary_pressed = True
            if num_buttons > 8 and self._joystick.get_button(8):
                state.exit_pressed = True
            if num_buttons > 9 and self._joystick.get_button(9):
                state.pause_pressed = True
            if num_buttons > 10 and self._joystick.get_button(10):
                state.pause_pressed = True
            if num_buttons > 11 and self._joystick.get_button(11):
                state.menu_down_pressed = True
            if num_buttons > 12 and self._joystick.get_button(12):
                state.menu_up_pressed = True
            if num_buttons > 13 and self._joystick.get_button(13):
                state.exit_pressed = True
        except Exception:
            pass

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
                        state.menu_down_pressed = True
                    elif hat_y > 0:
                        state.menu_up_pressed = True
        except Exception:
            pass

    def _read_joybutton(self, event, state):
        """Handle JOYBUTTONDOWN events for menu navigation only.

        Continuous button held state is now read via polling in
        ``_read_joystick_buttons``.  This handler only sets
        one-shot navigation events (menu_y) that don't need debounce.
        """
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
