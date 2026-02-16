# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import pygame
from maxbloks.dogrider import compat_sdl
from maxbloks.dogrider.game_framework import GameFramework
from maxbloks.dogrider.dog_rider import DogRider
from maxbloks.dogrider.obstacles import ObstacleManager
from maxbloks.dogrider.background import BackgroundManager
from maxbloks.dogrider.constants import *

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DogRiderGame(GameFramework):
    def __init__(self, title="Dog Rider - Motorbike Adventure", fps=60):
        screen, display_info = compat_sdl.init_display(
            size=(640, 480),
            fullscreen=True,
            vsync=True
        )
        logger.info(f"screen: {str(screen)}")
        logger.info(f"display_info: {str(display_info)}")

        super().__init__(screen, display_info, title, fps)
        self.init_game()

    def init_game(self):
        """Initialize game state and entities"""
        # Game state
        self.game_state = "start"  # "start", "playing", "game_over"

        # Game objects
        self.dog = DogRider(self.screen_width, self.screen_height)
        self.obstacle_manager = ObstacleManager(self.screen_width, self.screen_height)
        self.background_manager = BackgroundManager(self.screen_width, self.screen_height)

        # Game variables
        self.score = 0
        self.game_speed = 2.0
        self.frame_count = 0

        # Input handling
        self.jump_pressed = False
        self.last_jump_state = False

    def handle_input(self):
        """Handle player input"""
        super().handle_input()

        # Handle jump input (frame-based)
        current_jump_pressed = self.shoot_button_pressed  # SPACE/A button

        # Detect jump press (not hold)
        self.jump_pressed = current_jump_pressed and not self.last_jump_state
        self.last_jump_state = current_jump_pressed

        # Handle game state transitions
        if self.game_state == "start":
            if self.jump_pressed:
                self.game_state = "playing"
                self.reset_game()

        elif self.game_state == "game_over":
            if self.jump_pressed:
                self.game_state = "start"

    def reset_game(self):
        """Reset game to initial state"""
        self.dog.reset()
        self.obstacle_manager.reset()
        self.background_manager.reset()
        self.score = 0
        self.game_speed = 2.0
        self.frame_count = 0

    def update(self):
        """Update game state"""
        if self.game_state == "playing":
            # Update game speed
            if self.game_speed < MAX_GAME_SPEED:
                self.game_speed += SPEED_INCREASE_RATE

            # Update game objects
            self.dog.update(self.movement_x, self.movement_y, self.jump_pressed, self.game_speed)
            self.obstacle_manager.update(self.game_speed)
            self.background_manager.update(self.game_speed)

            # Check collisions
            if self.obstacle_manager.check_collisions(self.dog):
                self.game_state = "game_over"

            # Check win condition
            if self.obstacle_manager.is_complete():
                self.game_state = "game_over"

            # Update score
            self.frame_count += 1
            if self.frame_count % 60 == 0:  # Every second
                self.score += int(self.game_speed * 10)

    def draw(self):
        """Draw game elements"""
        # Draw background
        self.background_manager.draw(self.screen, self.game_speed)

        # Draw game objects
        self.obstacle_manager.draw(self.screen)
        self.dog.draw(self.screen)

        # Draw UI based on game state
        if self.game_state == "start":
            self.draw_start_screen()
        elif self.game_state == "playing":
            self.draw_ui()
        elif self.game_state == "game_over":
            self.draw_ui()
            self.draw_game_over_screen()

        pygame.display.flip()

    def draw_ui(self):
        """Draw the game UI"""
        self.draw_text(f"Score: {self.score}", 10, 10, 24, self.WHITE)
        self.draw_text(f"Speed: {self.game_speed:.1f}", 10, 40, 24, self.WHITE)
        obstacles_text = f"Obstacles: {self.obstacle_manager.obstacles_cleared}/{MAX_OBSTACLES}"
        self.draw_text(obstacles_text, 10, 70, 24, self.WHITE)

    def draw_start_screen(self):
        """Draw start screen"""
        self.screen.fill(SKY_BLUE)

        # Title
        self.draw_text("DOG RIDER", self.screen_width // 2, self.screen_height // 2 - 60,
                       48, BROWN, center=True)
        self.draw_text("Motorbike Adventure", self.screen_width // 2, self.screen_height // 2 - 20,
                       24, DARK_GRAY, center=True)

        # Instructions
        instructions = [
            "Use arrow keys or joystick to move",
            "Press SPACE or A button to jump",
            "Avoid rocks, use ramps to jump higher!",
            "Clear all obstacles to win!",
            "",
            "Press SPACE or A to start"
        ]

        y_offset = 20
        for i, instruction in enumerate(instructions):
            color = YELLOW if "Press SPACE" in instruction else WHITE
            self.draw_text(instruction, self.screen_width // 2,
                           self.screen_height // 2 + y_offset + i * 25,
                           24, color, center=True)

    def draw_game_over_screen(self):
        """Draw game over screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        won = self.obstacle_manager.is_complete()

        # Title
        if won:
            self.draw_text("CONGRATULATIONS! YOU WON!", self.screen_width // 2,
                           self.screen_height // 2 - 60, 36, GOLD, center=True)
            self.draw_text("You cleared all obstacles!", self.screen_width // 2,
                           self.screen_height // 2 - 20, 24, WHITE, center=True)
        else:
            self.draw_text("GAME OVER", self.screen_width // 2,
                           self.screen_height // 2 - 60, 48, RED, center=True)
            self.draw_text("You crashed!", self.screen_width // 2,
                           self.screen_height // 2 - 20, 24, WHITE, center=True)

        # Stats
        self.draw_text(f"Final Score: {self.score}", self.screen_width // 2,
                       self.screen_height // 2 + 20, 24, WHITE, center=True)
        obstacles_text = f"Obstacles Cleared: {self.obstacle_manager.obstacles_cleared}/{MAX_OBSTACLES}"
        self.draw_text(obstacles_text, self.screen_width // 2,
                       self.screen_height // 2 + 50, 24, WHITE, center=True)

        # Instructions
        self.draw_text("Press SPACE or A to play again", self.screen_width // 2,
                       self.screen_height // 2 + 100, 24, YELLOW, center=True)
        self.draw_text("Press ESC or B to quit", self.screen_width // 2,
                       self.screen_height // 2 + 130, 24, YELLOW, center=True)