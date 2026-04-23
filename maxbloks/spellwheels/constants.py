# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Game constants and configuration for SpellWheels.

All text in this module exists only for internal configuration (e.g. word
lists, theme labels used by the settings menu). Gameplay screens are
strictly icon-based and display no prose text.
"""

# ------------------------------------------------------------------
# Display
# ------------------------------------------------------------------
LOGICAL_WIDTH = 640
LOGICAL_HEIGHT = 480
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FULLSCREEN = False
INTEGER_SCALING = True
TARGET_FPS = 60

# ------------------------------------------------------------------
# Colors (RGB tuples)
# ------------------------------------------------------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (235, 87, 87)
GREEN = (111, 207, 151)
BLUE = (86, 156, 214)
YELLOW = (255, 220, 80)
ORANGE = (255, 165, 50)
PURPLE = (187, 107, 217)
PINK = (255, 150, 200)
BROWN = (150, 100, 60)
GRAY = (160, 160, 160)
DARK_GRAY = (70, 70, 78)
LIGHT_GRAY = (220, 220, 225)

# ------------------------------------------------------------------
# Theme (bright, cartoonish)
# ------------------------------------------------------------------
BG_GRADIENT_TOP = (135, 206, 250)      # sky-blue
BG_GRADIENT_BOTTOM = (176, 224, 230)   # powder-blue
PANEL_BG = (255, 255, 255)
PANEL_BORDER = (80, 80, 100)
PANEL_SHADOW = (40, 40, 60)

WHEEL_BG = (255, 250, 235)
WHEEL_BORDER = (90, 90, 120)
WHEEL_ACTIVE_BORDER = (255, 180, 40)
WHEEL_LETTER_COLOR = (40, 40, 80)
WHEEL_DIM_LETTER_COLOR = (170, 170, 190)

ICON_OUTLINE = (40, 40, 60)
TITLE_COLOR = (40, 50, 120)
CORRECT_COLOR = (90, 200, 110)
WRONG_COLOR = (230, 90, 90)
STAR_COLOR = (255, 210, 60)
STAR_EMPTY_COLOR = (190, 190, 200)
HINT_COLOR = (255, 170, 60)

# Progress bar / footsteps
PROGRESS_DONE = (90, 200, 110)
PROGRESS_CURRENT = (255, 180, 40)
PROGRESS_TODO = (200, 200, 210)

# ------------------------------------------------------------------
# Alphabet (German primary school: A-Z plus umlauts)
# ------------------------------------------------------------------
ALPHABET = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
    "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    "\u00c4", "\u00d6", "\u00dc",   # Ä Ö Ü
]

# Helper set for quick validation
ALPHABET_SET = set(ALPHABET)

# ------------------------------------------------------------------
# Wheel settings
# ------------------------------------------------------------------
WHEEL_VISIBLE_LETTERS = 3      # current + 1 above + 1 below
WHEEL_WIDTH = 60
WHEEL_HEIGHT = 180
WHEEL_SPACING = 10             # horizontal gap between wheels
WHEEL_REPEAT_DELAY = 400       # ms before key repeat starts
WHEEL_REPEAT_INTERVAL = 90     # ms between repeated scrolls
WHEEL_SCROLL_ANIM_MS = 120     # smooth scroll animation time

# ------------------------------------------------------------------
# Icon / layout
# ------------------------------------------------------------------
ICON_Y_RATIO = 0.30            # vertical center of the icon
WHEELS_Y_RATIO = 0.68          # vertical center of the wheel row
PROGRESS_Y = 28                # top margin for progress path
STAR_BAR_Y = 10

# ------------------------------------------------------------------
# Font sizes
# ------------------------------------------------------------------
FONT_SIZE_TITLE = 64
FONT_SIZE_MENU = 36
FONT_SIZE_MENU_SMALL = 24
FONT_SIZE_WHEEL = 56
FONT_SIZE_WHEEL_DIM = 32
FONT_SIZE_HUD = 28
FONT_SIZE_FEEDBACK = 72

# ------------------------------------------------------------------
# Input
# ------------------------------------------------------------------
JOYSTICK_DEADZONE = 0.2
JOYSTICK_AXIS_THRESHOLD = 0.5
# Normalization factor for diagonal movement (1 / sqrt(2))
DIAGONAL_NORMALIZE = 0.707

# Gamepad button mapping (Anbernic style)
BTN_A = 0
BTN_B = 1
BTN_X = 2
BTN_Y = 3
BTN_SELECT = 6
BTN_START = 7
BTN_EXIT_1 = 8
BTN_EXIT_2 = 13

# ------------------------------------------------------------------
# Feedback timing (ms)
# ------------------------------------------------------------------
CORRECT_FEEDBACK_DURATION = 1400
CORRECT_AUTO_ADVANCE_DELAY = 1400
WRONG_SHAKE_DURATION = 600
WRONG_SHAKE_AMPLITUDE = 8     # pixels
STAR_ANIM_DURATION = 700
LEVEL_COMPLETE_DISPLAY = 2500

# ------------------------------------------------------------------
# Scoring
# ------------------------------------------------------------------
MAX_STARS_PER_WORD = 3
# Stars awarded based on number of wrong submissions before success
# 0 wrong => 3 stars, 1 wrong => 2 stars, 2+ wrong => 1 star
STARS_BY_MISTAKES = [3, 2, 1]
MIN_STARS_PER_WORD = 1

# ------------------------------------------------------------------
# Level / theme definitions
# ------------------------------------------------------------------
THEME_ANIMALS = "animals"
THEME_FRUITS = "fruits"
THEME_NATURE = "nature"
THEME_HOUSEHOLD = "household"

# Progress save file (under the user's home directory)
SAVE_FILE_NAME = ".spellwheels_progress.json"

# Menu item indices
MENU_ITEM_PLAY = 0
MENU_ITEM_RESUME = 1
MENU_ITEM_RESET = 2
MENU_ITEM_QUIT = 3
MENU_ITEM_COUNT = 4

# Level complete screen timing
STICKER_SHOW_DELAY = 300