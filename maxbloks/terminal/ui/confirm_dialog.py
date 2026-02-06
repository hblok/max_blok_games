# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
from typing import List, Dict, Optional, Tuple, Callable

from maxbloks.terminal.config.config import (
    COLORS, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    LIST_ITEM_HEIGHT, SCROLL_SPEED, PAGE_SCROLL_ITEMS
)
from maxbloks.terminal.ui.font_manager import FontManager


class ConfirmDialog:
    """
    Confirmation dialog for dangerous commands
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize the dialog
        
        Args:
            screen_width, screen_height: Screen dimensions
        """
        self.width = 500
        self.height = 200
        self.rect = pygame.Rect(
            (screen_width - self.width) // 2,
            (screen_height - self.height) // 2,
            self.width,
            self.height
        )
        self.visible = False
        self.command = ""
        self.warning = ""
        self.selected_option = 0  # 0 = Cancel, 1 = Confirm
        self.font_manager = FontManager.get_instance()
        self.callback: Optional[Callable[[bool], None]] = None
    
    def show(self, command: str, warning: str, callback: Callable[[bool], None]):
        """
        Show the dialog
        
        Args:
            command: The command to confirm
            warning: Warning message
            callback: Function to call with result (True = confirm, False = cancel)
        """
        self.command = command
        self.warning = warning
        self.callback = callback
        self.selected_option = 0
        self.visible = True
    
    def hide(self):
        """Hide the dialog"""
        self.visible = False
        self.callback = None
    
    def move_selection(self, direction: int):
        """Move selection between options"""
        self.selected_option = (self.selected_option + direction) % 2
    
    def confirm(self):
        """Confirm the current selection"""
        if self.callback:
            self.callback(self.selected_option == 1)
        self.hide()
    
    def cancel(self):
        """Cancel the dialog"""
        if self.callback:
            self.callback(False)
        self.hide()
    
    def draw(self, surface: pygame.Surface):
        """Draw the dialog"""
        if not self.visible:
            return
        
        # Draw overlay
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw dialog background
        pygame.draw.rect(surface, COLORS['panel_bg'], self.rect, border_radius=8)
        pygame.draw.rect(surface, COLORS['warning'], self.rect, 2, border_radius=8)
        
        font_large = self.font_manager.get('large_bold')
        font_medium = self.font_manager.get('medium')
        font_small = self.font_manager.get('small')
        
        # Draw title
        title = font_large.render("⚠ Confirm Action", True, COLORS['warning'])
        surface.blit(title, (self.rect.x + 20, self.rect.y + 15))
        
        # Draw warning
        warning_text = font_small.render(self.warning, True, COLORS['error'])
        surface.blit(warning_text, (self.rect.x + 20, self.rect.y + 50))
        
        # Draw command
        cmd_text = font_medium.render(f"Command: {self.command[:50]}", True, COLORS['text'])
        surface.blit(cmd_text, (self.rect.x + 20, self.rect.y + 80))
        
        # Draw buttons
        button_y = self.rect.y + 130
        button_width = 120
        button_height = 40
        
        # Cancel button
        cancel_rect = pygame.Rect(
            self.rect.x + self.width // 2 - button_width - 20,
            button_y,
            button_width,
            button_height
        )
        cancel_color = COLORS['highlight'] if self.selected_option == 0 else COLORS['border']
        pygame.draw.rect(surface, cancel_color, cancel_rect, border_radius=4)
        cancel_text = font_medium.render("Cancel", True, COLORS['text'])
        cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
        surface.blit(cancel_text, cancel_text_rect)
        
        # Confirm button
        confirm_rect = pygame.Rect(
            self.rect.x + self.width // 2 + 20,
            button_y,
            button_width,
            button_height
        )
        confirm_color = COLORS['error'] if self.selected_option == 1 else COLORS['border']
        pygame.draw.rect(surface, confirm_color, confirm_rect, border_radius=4)
        confirm_text = font_medium.render("Execute", True, COLORS['text'])
        confirm_text_rect = confirm_text.get_rect(center=confirm_rect.center)
        surface.blit(confirm_text, confirm_text_rect)
        
        # Draw hint
        hint = font_small.render("A: Select  |  B: Cancel", True, COLORS['text_dim'])
        hint_rect = hint.get_rect(centerx=self.rect.centerx, bottom=self.rect.bottom - 10)
        surface.blit(hint, hint_rect)
