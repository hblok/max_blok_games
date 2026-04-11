# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Game constants and configuration for MathWheel."""

# Screen settings
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FULLSCREEN = True
TARGET_FPS = 60

# Colors (RGB tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 80, 80)
GREEN = (80, 200, 80)
BLUE = (80, 130, 220)
YELLOW = (255, 220, 60)
ORANGE = (255, 165, 50)
GRAY = (160, 160, 160)
DARK_GRAY = (80, 80, 80)
LIGHT_GRAY = (210, 210, 210)

# Theme colors
BG_COLOR = (40, 44, 82)
BG_GRADIENT_TOP = (40, 44, 82)
BG_GRADIENT_BOTTOM = (25, 28, 60)
EQUATION_BG = (55, 60, 110)
EQUATION_BORDER = (100, 110, 180)
WHEEL_BG = (50, 55, 100)
WHEEL_HIGHLIGHT = (90, 100, 180)
WHEEL_SELECTED = (255, 220, 60)
WHEEL_NUMBER_COLOR = WHITE
WHEEL_DIM_COLOR = (120, 125, 160)
SUBMIT_COLOR = (80, 200, 80)
SUBMIT_HOVER = (100, 230, 100)
SKIP_COLOR = (180, 130, 60)
SKIP_HOVER = (210, 160, 80)
STAR_COLOR = (255, 220, 60)
STAR_EMPTY_COLOR = (80, 85, 120)
CORRECT_COLOR = (80, 220, 120)
WRONG_COLOR = (255, 100, 100)
MENU_BG = (35, 40, 75)
MENU_ITEM_BG = (55, 60, 110)
MENU_ITEM_SELECTED = (80, 90, 160)
MENU_ITEM_BORDER = (100, 110, 180)
TOGGLE_ON = (80, 200, 80)
TOGGLE_OFF = (160, 60, 60)
TITLE_COLOR = (255, 220, 60)

# Difficulty levels
DIFFICULTY_EASY = 0
DIFFICULTY_MEDIUM = 1
DIFFICULTY_HARD = 2

# Difficulty settings: (max_number, max_result, allow_missing_middle)
DIFFICULTY_CONFIG = {
    DIFFICULTY_EASY: {
        "max_number": 10,
        "max_result": 10,
        "allow_missing_first": True,
        "allow_missing_middle": False,
        "allow_missing_last": True,
        "label": "Easy",
    },
    DIFFICULTY_MEDIUM: {
        "max_number": 9,
        "max_result": 18,
        "allow_missing_first": True,
        "allow_missing_middle": True,
        "allow_missing_last": True,
        "label": "Medium",
    },
    DIFFICULTY_HARD: {
        "max_number": 20,
        "max_result": 30,
        "allow_missing_first": True,
        "allow_missing_middle": True,
        "allow_missing_last": True,
        "label": "Hard",
    },
}

# Operations
OP_ADD = "+"
OP_SUB = "-"
OP_MUL = "×"
OP_DIV = "÷"

# Missing position in equation
MISSING_FIRST = 0
MISSING_MIDDLE = 1
MISSING_LAST = 2

# Scoring
STARS_PER_CORRECT = 1
STAR_BONUS_FIRST_TRY = 1
MAX_STARS_DISPLAY = 50
WRONG_ANSWER_PENALTY = 0

# Progression
QUESTIONS_PER_DIFFICULTY_UP = 5
EASY_MIX_RATIO = 0.25

# Wheel settings
WHEEL_VISIBLE_ITEMS = 5
WHEEL_MIN_VALUE = 0
WHEEL_MAX_VALUE = 30
WHEEL_REPEAT_DELAY = 400
WHEEL_REPEAT_INTERVAL = 80

# Animation timings (milliseconds)
FEEDBACK_DURATION = 1200
FEEDBACK_FADE_START = 800
STAR_ANIM_DURATION = 600
TRANSITION_DURATION = 400

# Layout constants (relative to screen)
EQUATION_Y_RATIO = 0.25
WHEEL_Y_RATIO = 0.55
SUBMIT_Y_RATIO = 0.80
STAR_BAR_Y = 10
STAR_SIZE = 24
STAR_SPACING = 28

# Font sizes
FONT_SIZE_TITLE = 64
FONT_SIZE_EQUATION = 72
FONT_SIZE_WHEEL = 56
FONT_SIZE_WHEEL_DIM = 40
FONT_SIZE_BUTTON = 36
FONT_SIZE_HUD = 28
FONT_SIZE_MENU = 36
FONT_SIZE_MENU_SMALL = 24
FONT_SIZE_FEEDBACK = 48

# Input
JOYSTICK_DEADZONE = 0.3
JOYSTICK_AXIS_THRESHOLD = 0.5

# Menu items
MENU_ITEM_PLAY = 0
MENU_ITEM_ADDITION = 1
MENU_ITEM_SUBTRACTION = 2
MENU_ITEM_MULTIPLICATION = 3
MENU_ITEM_DIVISION = 4
MENU_ITEM_COUNT = 5

# UI element sizes
SUBMIT_BUTTON_RADIUS = 36
SKIP_BUTTON_RADIUS = 28