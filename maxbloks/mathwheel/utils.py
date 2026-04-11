# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""Question generation and difficulty logic for MathWheel."""

import random

from maxbloks.mathwheel import constants


class Question:
    """Represents a single math question with an equation and missing value."""

    def __init__(self, a, b, result, operation, missing_position):
        self.a = a
        self.b = b
        self.result = result
        self.operation = operation
        self.missing_position = missing_position

    @property
    def answer(self):
        if self.missing_position == constants.MISSING_FIRST:
            return self.a
        elif self.missing_position == constants.MISSING_MIDDLE:
            return self.b
        else:
            return self.result

    @property
    def display_values(self):
        """Return (left, op, right, equals, result) with None for missing."""
        left = None if self.missing_position == constants.MISSING_FIRST else self.a
        right = None if self.missing_position == constants.MISSING_MIDDLE else self.b
        res = None if self.missing_position == constants.MISSING_LAST else self.result
        return left, self.operation, right, res

    @property
    def wheel_range(self):
        """Return (min_val, max_val) for the number wheel."""
        return 0, max(self.result + 5, 20)


def generate_addition(difficulty_level):
    """Generate an addition question for the given difficulty."""
    config = constants.DIFFICULTY_CONFIG[difficulty_level]
    max_num = config["max_number"]
    max_res = config["max_result"]

    for _attempt in range(50):
        a = random.randint(0, max_num)
        b = random.randint(0, max_num)
        result = a + b
        if result <= max_res:
            break
    else:
        a = random.randint(0, min(5, max_num))
        b = random.randint(0, min(5, max_num))
        result = a + b

    missing = _pick_missing_position(config)
    return Question(a, b, result, constants.OP_ADD, missing)


def generate_subtraction(difficulty_level):
    """Generate a subtraction question (no negative results)."""
    config = constants.DIFFICULTY_CONFIG[difficulty_level]
    max_num = config["max_number"]
    max_res = config["max_result"]

    for _attempt in range(50):
        result = random.randint(0, max_res)
        b = random.randint(0, max_num)
        a = result + b
        if a <= max_res:
            break
    else:
        b = random.randint(0, min(3, max_num))
        result = random.randint(0, min(5, max_num))
        a = result + b

    missing = _pick_missing_position(config)
    return Question(a, b, result, constants.OP_SUB, missing)


def generate_multiplication(difficulty_level):
    """Generate a multiplication question."""
    config = constants.DIFFICULTY_CONFIG[difficulty_level]
    max_num = min(config["max_number"], 10)
    max_res = config["max_result"]

    for _attempt in range(50):
        a = random.randint(1, max_num)
        b = random.randint(1, max_num)
        result = a * b
        if result <= max_res:
            break
    else:
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        result = a * b

    missing = _pick_missing_position(config)
    return Question(a, b, result, constants.OP_MUL, missing)


def generate_division(difficulty_level):
    """Generate a division question (no fractional results)."""
    config = constants.DIFFICULTY_CONFIG[difficulty_level]
    max_num = min(config["max_number"], 10)
    max_res = config["max_result"]

    for _attempt in range(50):
        b = random.randint(1, max_num)
        result = random.randint(1, max_num)
        a = b * result
        if a <= max_res:
            break
    else:
        b = random.randint(1, 5)
        result = random.randint(1, 5)
        a = b * result

    missing = _pick_missing_position(config)
    return Question(a, b, result, constants.OP_DIV, missing)


def _pick_missing_position(config):
    """Pick a missing position based on difficulty config."""
    positions = []
    if config["allow_missing_first"]:
        positions.append(constants.MISSING_FIRST)
    if config["allow_missing_middle"]:
        positions.append(constants.MISSING_MIDDLE)
    if config["allow_missing_last"]:
        positions.append(constants.MISSING_LAST)

    if not positions:
        return constants.MISSING_LAST

    # Bias toward MISSING_LAST for easier questions
    if constants.MISSING_LAST in positions:
        weights = []
        for p in positions:
            weights.append(1 if p != constants.MISSING_LAST else 2)
        return random.choices(positions, weights=weights, k=1)[0]

    return random.choice(positions)


def generate_question(difficulty_level, enabled_operations):
    """Generate a question using one of the enabled operations."""
    generators = {}
    if enabled_operations.get(constants.OP_ADD, False):
        generators[constants.OP_ADD] = generate_addition
    if enabled_operations.get(constants.OP_SUB, False):
        generators[constants.OP_SUB] = generate_subtraction
    if enabled_operations.get(constants.OP_MUL, False):
        generators[constants.OP_MUL] = generate_multiplication
    if enabled_operations.get(constants.OP_DIV, False):
        generators[constants.OP_DIV] = generate_division

    if not generators:
        generators[constants.OP_ADD] = generate_addition

    op = random.choice(list(generators.keys()))
    return generators[op](difficulty_level)


class DifficultyManager:
    """Tracks progress and manages difficulty progression."""

    def __init__(self):
        self.current_level = constants.DIFFICULTY_EASY
        self.correct_streak = 0
        self.total_correct = 0
        self.total_questions = 0

    def record_correct(self):
        self.correct_streak += 1
        self.total_correct += 1
        self.total_questions += 1
        self._maybe_advance()

    def record_wrong(self):
        self.correct_streak = max(0, self.correct_streak - 1)
        self.total_questions += 1

    def _maybe_advance(self):
        if self.correct_streak >= constants.QUESTIONS_PER_DIFFICULTY_UP:
            if self.current_level < constants.DIFFICULTY_HARD:
                self.current_level += 1
                self.correct_streak = 0

    def pick_difficulty(self):
        """Pick difficulty for next question, mixing in easier ones."""
        if self.current_level == constants.DIFFICULTY_EASY:
            return constants.DIFFICULTY_EASY

        if random.random() < constants.EASY_MIX_RATIO:
            return random.randint(constants.DIFFICULTY_EASY, self.current_level - 1)

        return self.current_level

    def reset(self):
        self.current_level = constants.DIFFICULTY_EASY
        self.correct_streak = 0
        self.total_correct = 0
        self.total_questions = 0


class ScoreTracker:
    """Tracks stars earned during a session."""

    def __init__(self):
        self.stars = 0
        self.first_try = True

    def award_correct(self):
        earned = constants.STARS_PER_CORRECT
        if self.first_try:
            earned += constants.STAR_BONUS_FIRST_TRY
        self.stars += earned
        return earned

    def record_wrong(self):
        self.first_try = False
        penalty = constants.WRONG_ANSWER_PENALTY
        self.stars = max(0, self.stars - penalty)

    def new_question(self):
        self.first_try = True

    def reset(self):
        self.stars = 0
        self.first_try = True