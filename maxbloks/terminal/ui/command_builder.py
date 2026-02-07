# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import pygame
from typing import List, Dict, Optional, Tuple, Callable

from maxbloks.terminal.config.config import (
    COLORS, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    LIST_ITEM_HEIGHT, SCROLL_SPEED, PAGE_SCROLL_ITEMS
)
from maxbloks.terminal.ui.font_manager import FontManager


class CommandBuilder:
    """
    Displays the current command being built with removable argument chips
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initialize the command builder display
        
        Args:
            x, y: Position
            width, height: Dimensions
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.command_parts: List[str] = []
        self.font_manager = FontManager.get_instance()
        self.cwd = "~"
        self.status = "Ready"
        self.status_type = "normal"  # normal, running, success, error, live
        self.selected_chip = -1  # -1 means no chip selected, >= 0 is chip index
        self.chip_mode = False  # Whether we're in chip selection mode
        self.chip_rects: List[pygame.Rect] = []  # Store chip rectangles for selection
        
    def set_cwd(self, cwd: str):
        """Set current working directory"""
        # Shorten home directory
        home = os.path.expanduser('~')
        if cwd.startswith(home):
            cwd = '~' + cwd[len(home):]
        self.cwd = cwd
    
    def set_command(self, parts: List[str]):
        """Set command parts"""
        self.command_parts = parts
        self.selected_chip = -1
    
    def add_part(self, part: str):
        """Add a part to the command"""
        self.command_parts.append(part)
    
    def remove_last(self) -> bool:
        """
        Remove the last part
        
        Returns:
            True if a part was removed
        """
        if self.command_parts:
            self.command_parts.pop()
            return True
        return False
    
    def remove_at(self, index: int) -> bool:
        """
        Remove part at specific index
        
        Args:
            index: Index of part to remove (0 is command, 1+ are arguments)
            
        Returns:
            True if a part was removed
        """
        if 0 <= index < len(self.command_parts):
            self.command_parts.pop(index)
            self.selected_chip = -1
            return True
        return False
    
    def remove_selected_chip(self) -> bool:
        """
        Remove the currently selected chip
        
        Returns:
            True if a chip was removed
        """
        if self.chip_mode and self.selected_chip >= 0:
            return self.remove_at(self.selected_chip)
        return False
    
    def enter_chip_mode(self):
        """Enter chip selection mode"""
        if len(self.command_parts) > 1:  # Only if there are arguments
            self.chip_mode = True
            self.selected_chip = 1  # Start at first argument
    
    def exit_chip_mode(self):
        """Exit chip selection mode"""
        self.chip_mode = False
        self.selected_chip = -1
    
    def move_chip_selection(self, direction: int):
        """
        Move chip selection
        
        Args:
            direction: -1 for left, 1 for right
        """
        if not self.chip_mode or len(self.command_parts) <= 1:
            return
        
        self.selected_chip += direction
        # Only allow selecting arguments (index 1+), not the command itself
        self.selected_chip = max(1, min(len(self.command_parts) - 1, self.selected_chip))
    
    def clear(self):
        """Clear the command"""
        self.command_parts = []
        self.selected_chip = -1
        self.chip_mode = False
    
    def get_command(self) -> str:
        """Get the full command string"""
        return ' '.join(self.command_parts)
    
    def get_parts_count(self) -> int:
        """Get number of command parts"""
        return len(self.command_parts)
    
    def set_status(self, status: str, status_type: str = "normal"):
        """Set status message"""
        self.status = status
        self.status_type = status_type
    
    def draw(self, surface: pygame.Surface):
        """Draw the command builder with chip-style arguments"""
        # Draw background
        pygame.draw.rect(surface, COLORS['panel_bg'], self.rect)
        pygame.draw.rect(surface, COLORS['border'], self.rect, 1)
        
        font = self.font_manager.get('medium')
        font_large = self.font_manager.get('large_bold')
        font_small = self.font_manager.get('small')
        
        # Draw CWD
        cwd_text = font_small.render(f"📁 {self.cwd}", True, COLORS['text_dim'])
        surface.blit(cwd_text, (self.rect.x + 10, self.rect.y + 8))
        
        # Draw command prompt and parts
        prompt = font_large.render("$ ", True, COLORS['success'])
        surface.blit(prompt, (self.rect.x + 10, self.rect.y + 32))
        
        x_offset = self.rect.x + 10 + prompt.get_width()
        self.chip_rects = []
        
        if self.command_parts:
            # Draw command (first part) - not as a chip
            cmd_text = font_large.render(self.command_parts[0], True, COLORS['command_text'])
            surface.blit(cmd_text, (x_offset, self.rect.y + 32))
            x_offset += cmd_text.get_width() + 8
            self.chip_rects.append(None)  # Placeholder for command (not selectable as chip)
            
            # Draw arguments as chips
            for i, part in enumerate(self.command_parts[1:], 1):
                chip_padding = 6
                arg_text = font.render(part, True, COLORS['text'])
                chip_width = arg_text.get_width() + chip_padding * 2 + 16  # Extra for X button
                chip_height = 28
                
                chip_rect = pygame.Rect(x_offset, self.rect.y + 34, chip_width, chip_height)
                self.chip_rects.append(chip_rect)
                
                # Draw chip background
                is_selected = self.chip_mode and self.selected_chip == i
                if is_selected:
                    pygame.draw.rect(surface, COLORS['highlight'], chip_rect, border_radius=4)
                    text_color = COLORS['highlight_text']
                else:
                    pygame.draw.rect(surface, COLORS['border'], chip_rect, border_radius=4)
                    text_color = COLORS['argument_text']
                
                # Draw argument text
                surface.blit(font.render(part, True, text_color), 
                           (x_offset + chip_padding, self.rect.y + 37))
                
                # Draw X button on chip
                x_btn_x = x_offset + chip_width - 16
                x_btn_color = COLORS['error'] if is_selected else COLORS['text_dim']
                x_text = font_small.render("×", True, x_btn_color)
                surface.blit(x_text, (x_btn_x, self.rect.y + 36))
                
                x_offset += chip_width + 6
            
            # Draw cursor if not in chip mode
            if not self.chip_mode:
                cursor_rect = pygame.Rect(x_offset, self.rect.y + 34, 2, 26)
                pygame.draw.rect(surface, COLORS['text'], cursor_rect)
        else:
            # Draw placeholder
            placeholder = font.render("Select a command...", True, COLORS['text_dim'])
            surface.blit(placeholder, (x_offset, self.rect.y + 36))
        
        # Draw status with live indicator
        status_colors = {
            'normal': COLORS['text_dim'],
            'running': COLORS['warning'],
            'success': COLORS['success'],
            'error': COLORS['error'],
            'live': COLORS['error'],
        }
        status_color = status_colors.get(self.status_type, COLORS['text_dim'])
        
        # Add live indicator animation
        status_prefix = ""
        if self.status_type == 'live':
            status_prefix = "🔴 "
        
        status_text = font_small.render(f"{status_prefix}{self.status}", True, status_color)
        surface.blit(status_text, (self.rect.right - status_text.get_width() - 10, self.rect.y + 8))
        
        # Draw chip mode hint
        if self.chip_mode:
            hint = font_small.render("←→ Select  B: Remove  Y: Exit", True, COLORS['text_dim'])
            surface.blit(hint, (self.rect.x + 10, self.rect.y + 62))
        elif len(self.command_parts) > 1:
            hint = font_small.render("L: Edit args", True, COLORS['text_dim'])
            surface.blit(hint, (self.rect.x + 10, self.rect.y + 62))
