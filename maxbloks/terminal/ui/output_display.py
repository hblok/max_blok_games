# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
from typing import List, Dict, Optional, Tuple, Callable

from maxbloks.terminal.config.config import (
    COLORS, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    LIST_ITEM_HEIGHT, SCROLL_SPEED, PAGE_SCROLL_ITEMS
)
from .font_manager import FontManager


class OutputDisplay:
    """
    Scrollable output display for command results with live mode support
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initialize the output display
        
        Args:
            x, y: Position
            width, height: Dimensions
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.lines: List[Tuple[str, str]] = []  # (text, color_type)
        self.scroll_offset = 0
        self.font_manager = FontManager.get_instance()
        self.line_height = FONT_SIZE_SMALL + 4
        self.visible_lines = (height - 8) // self.line_height
        self.expanded = False
        
        # Live mode properties
        self.live_mode = False
        self.live_line_count = 0
        self.live_update_time = 0
        self.auto_scroll = True
        
    def set_output(self, stdout: str, stderr: str, return_code: int):
        """
        Set the output content
        
        Args:
            stdout: Standard output text
            stderr: Standard error text
            return_code: Command return code
        """
        self.lines = []
        self.scroll_offset = 0
        self.live_mode = False
        
        # Add stdout lines
        if stdout:
            for line in stdout.split('\n'):
                if line:
                    self.lines.append((line, 'output'))
        
        # Add stderr lines
        if stderr:
            for line in stderr.split('\n'):
                if line:
                    self.lines.append((line, 'error'))
        
        # Add status line
        if return_code == 0:
            self.lines.append(("✓ Command completed successfully", 'success'))
        elif return_code == -1:
            self.lines.append(("✗ Command failed or timed out", 'error'))
        else:
            self.lines.append((f"✗ Command exited with code {return_code}", 'error'))
    
    def set_live_output(self, lines: List[str], is_complete: bool = False):
        """
        Set live output content
        
        Args:
            lines: List of output lines
            is_complete: Whether the command has completed
        """
        self.lines = [(line, 'output') for line in lines]
        self.live_line_count = len(lines)
        self.live_update_time = pygame.time.get_ticks()
        
        if is_complete:
            self.live_mode = False
            self.lines.append(("✓ Live command completed", 'success'))
        else:
            self.live_mode = True
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll and self.lines:
            visible = (self.rect.height - 8) // self.line_height
            self.scroll_offset = max(0, len(self.lines) - visible)
    
    def set_message(self, message: str, msg_type: str = 'output'):
        """
        Set a simple message
        
        Args:
            message: Message text
            msg_type: 'output', 'error', 'success', 'warning'
        """
        self.lines = [(message, msg_type)]
        self.scroll_offset = 0
        self.live_mode = False
    
    def clear(self):
        """Clear the output"""
        self.lines = []
        self.scroll_offset = 0
        self.live_mode = False
    
    def scroll(self, direction: int):
        """
        Scroll the output
        
        Args:
            direction: -1 for up, 1 for down
        """
        max_scroll = max(0, len(self.lines) - self.visible_lines)
        self.scroll_offset += direction * 3
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))
        
        # Disable auto-scroll if user scrolls up
        if direction < 0:
            self.auto_scroll = False
        elif self.scroll_offset >= max_scroll:
            self.auto_scroll = True
    
    def toggle_expanded(self):
        """Toggle expanded view"""
        self.expanded = not self.expanded
    
    def start_live_mode(self):
        """Start live output mode"""
        self.live_mode = True
        self.auto_scroll = True
        self.lines = []
        self.scroll_offset = 0
    
    def stop_live_mode(self):
        """Stop live output mode"""
        self.live_mode = False
    
    def draw(self, surface: pygame.Surface, expanded_rect: Optional[pygame.Rect] = None):
        """
        Draw the output display
        
        Args:
            surface: Surface to draw on
            expanded_rect: Optional expanded rectangle
        """
        draw_rect = expanded_rect if self.expanded and expanded_rect else self.rect
        
        # Recalculate visible lines for current rect
        visible = (draw_rect.height - 8) // self.line_height
        
        # Draw background
        pygame.draw.rect(surface, COLORS['panel_bg'], draw_rect)
        pygame.draw.rect(surface, COLORS['border'], draw_rect, 1)
        
        # Draw title bar
        title_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, 24)
        pygame.draw.rect(surface, COLORS['border'], title_rect)
        
        font_small = self.font_manager.get('small')
        
        # Build title with live indicator
        title_text = "OUTPUT"
        if self.expanded:
            title_text += " (Expanded)"
        
        title = font_small.render(title_text, True, COLORS['text'])
        surface.blit(title, (draw_rect.x + 8, draw_rect.y + 4))
        
        # Draw live indicator
        if self.live_mode:
            # Blinking red dot
            blink = (pygame.time.get_ticks() // 500) % 2 == 0
            if blink:
                live_indicator = font_small.render("🔴 LIVE", True, COLORS['error'])
            else:
                live_indicator = font_small.render("⚫ LIVE", True, COLORS['error'])
            surface.blit(live_indicator, (draw_rect.x + 100, draw_rect.y + 4))
            
            # Line count
            count_text = font_small.render(f"Lines: {self.live_line_count}", True, COLORS['text_dim'])
            surface.blit(count_text, (draw_rect.right - count_text.get_width() - 10, draw_rect.y + 4))
        
        if not self.lines:
            hint = font_small.render("No output yet", True, COLORS['text_dim'])
            surface.blit(hint, (draw_rect.x + 8, draw_rect.y + 30))
            return
        
        # Create clipping region
        content_rect = pygame.Rect(
            draw_rect.x + 4,
            draw_rect.y + 26,
            draw_rect.width - 8,
            draw_rect.height - 30
        )
        surface.set_clip(content_rect)
        
        # Draw lines
        y = draw_rect.y + 28
        for i in range(int(self.scroll_offset), min(len(self.lines), int(self.scroll_offset) + visible)):
            text, color_type = self.lines[i]
            
            # Determine color
            if color_type == 'error':
                color = COLORS['error']
            elif color_type == 'success':
                color = COLORS['success']
            elif color_type == 'warning':
                color = COLORS['warning']
            else:
                color = COLORS['output_text']
            
            # Truncate long lines
            max_chars = (draw_rect.width - 20) // 8
            if len(text) > max_chars:
                text = text[:max_chars - 3] + "..."
            
            text_surface = font_small.render(text, True, color)
            surface.blit(text_surface, (draw_rect.x + 8, y))
            y += self.line_height
        
        surface.set_clip(None)
        
        # Draw scrollbar if needed
        if len(self.lines) > visible:
            self._draw_scrollbar(surface, draw_rect, visible)
    
    def _draw_scrollbar(self, surface: pygame.Surface, rect: pygame.Rect, visible: int):
        """Draw scrollbar"""
        scrollbar_width = 4
        scrollbar_x = rect.right - scrollbar_width - 2
        scrollbar_y = rect.y + 26
        scrollbar_height = rect.height - 30
        
        thumb_ratio = visible / len(self.lines)
        thumb_height = max(15, scrollbar_height * thumb_ratio)
        
        max_scroll = max(1, len(self.lines) - visible)
        scroll_ratio = self.scroll_offset / max_scroll
        thumb_y = scrollbar_y + (scrollbar_height - thumb_height) * scroll_ratio
        
        pygame.draw.rect(surface, COLORS['border'], 
                        (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height),
                        border_radius=2)
        pygame.draw.rect(surface, COLORS['text_dim'],
                        (scrollbar_x, thumb_y, scrollbar_width, thumb_height),
                        border_radius=2)
