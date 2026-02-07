# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
from typing import List, Dict, Optional, Tuple, Callable

from maxbloks.terminal.config.config import (
    COLORS, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    LIST_ITEM_HEIGHT, SCROLL_SPEED, PAGE_SCROLL_ITEMS
)
from .font_manager import FontManager


class ButtonHints:
    """
    Displays button hints at the bottom of the screen
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initialize button hints
        
        Args:
            x, y: Position
            width, height: Dimensions
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.font_manager = FontManager.get_instance()
        self.hints = []
        
    def set_hints(self, hints: List[Tuple[str, str]]):
        """
        Set the hints to display
        
        Args:
            hints: List of (button, action) tuples
        """
        self.hints = hints
    
    def draw(self, surface: pygame.Surface):
        """Draw the button hints"""
        pygame.draw.rect(surface, COLORS['panel_bg'], self.rect)
        pygame.draw.line(surface, COLORS['border'], 
                        (self.rect.x, self.rect.y), 
                        (self.rect.right, self.rect.y))
        
        font = self.font_manager.get('small')
        
        x_offset = self.rect.x + 20
        y_center = self.rect.y + self.rect.height // 2
        
        for button, action in self.hints:
            # Draw button
            btn_text = font.render(button, True, COLORS['highlight'])
            surface.blit(btn_text, (x_offset, y_center - btn_text.get_height() // 2))
            x_offset += btn_text.get_width() + 5
            
            # Draw action
            action_text = font.render(action, True, COLORS['text_dim'])
            surface.blit(action_text, (x_offset, y_center - action_text.get_height() // 2))
            x_offset += action_text.get_width() + 25
            
