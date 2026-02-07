# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame
from typing import List, Dict, Optional, Tuple, Callable

from maxbloks.terminal.config.config import (
    COLORS, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    LIST_ITEM_HEIGHT, SCROLL_SPEED, PAGE_SCROLL_ITEMS
)
from .font_manager import FontManager


class ScrollableList:
    """
    A scrollable list component with selection support
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initialize the scrollable list
        
        Args:
            x, y: Position of the list
            width, height: Dimensions of the list
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.items: List[Dict] = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_items = height // LIST_ITEM_HEIGHT
        self.font_manager = FontManager.get_instance()
        self.animation_offset = 0
        self.target_scroll = 0
        
    def set_items(self, items: List[Dict]):
        """
        Set the list items
        
        Args:
            items: List of dicts with 'text', 'desc' (optional), 'type' (optional)
        """
        self.items = items
        self.selected_index = 0
        self.scroll_offset = 0
        self.target_scroll = 0
        
    def move_selection(self, direction: int):
        """
        Move selection up or down
        
        Args:
            direction: -1 for up, 1 for down
        """
        if not self.items:
            return
            
        self.selected_index += direction
        self.selected_index = max(0, min(len(self.items) - 1, self.selected_index))
        
        # Adjust scroll to keep selection visible
        if self.selected_index < self.scroll_offset:
            self.target_scroll = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.visible_items:
            self.target_scroll = self.selected_index - self.visible_items + 1
    
    def page_scroll(self, direction: int):
        """
        Scroll by a page
        
        Args:
            direction: -1 for up, 1 for down
        """
        if not self.items:
            return
            
        self.selected_index += direction * PAGE_SCROLL_ITEMS
        self.selected_index = max(0, min(len(self.items) - 1, self.selected_index))
        
        # Adjust scroll
        if self.selected_index < self.scroll_offset:
            self.target_scroll = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.visible_items:
            self.target_scroll = self.selected_index - self.visible_items + 1
    
    def get_selected(self) -> Optional[Dict]:
        """
        Get the currently selected item
        
        Returns:
            Selected item dict or None
        """
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None
    
    def update(self):
        """Update animations"""
        # Smooth scrolling
        if self.scroll_offset != self.target_scroll:
            diff = self.target_scroll - self.scroll_offset
            self.scroll_offset += diff * 0.3
            if abs(diff) < 0.1:
                self.scroll_offset = self.target_scroll
    
    def draw(self, surface: pygame.Surface):
        """
        Draw the list
        
        Args:
            surface: Surface to draw on
        """
        # Draw background
        pygame.draw.rect(surface, COLORS['panel_bg'], self.rect)
        pygame.draw.rect(surface, COLORS['border'], self.rect, 1)
        
        if not self.items:
            # Draw empty message
            font = self.font_manager.get('medium')
            text = font.render("No items", True, COLORS['text_dim'])
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)
            return
        
        # Create clipping region
        clip_rect = self.rect.inflate(-4, -4)
        surface.set_clip(clip_rect)
        
        font = self.font_manager.get('medium')
        font_small = self.font_manager.get('small')
        
        scroll_int = int(self.scroll_offset)
        
        for i in range(max(0, scroll_int), min(len(self.items), scroll_int + self.visible_items + 1)):
            item = self.items[i]
            y_pos = self.rect.y + (i - self.scroll_offset) * LIST_ITEM_HEIGHT + 2
            
            item_rect = pygame.Rect(
                self.rect.x + 2,
                y_pos,
                self.rect.width - 4,
                LIST_ITEM_HEIGHT - 2
            )
            
            # Draw selection highlight
            if i == self.selected_index:
                pygame.draw.rect(surface, COLORS['highlight'], item_rect, border_radius=4)
                text_color = COLORS['highlight_text']
            else:
                text_color = COLORS['text']
            
            # Determine icon/prefix based on type
            prefix = ""
            if item.get('type') == 'dir':
                prefix = "📁 "
                if i != self.selected_index:
                    text_color = COLORS['command_text']
            elif item.get('type') == 'file':
                prefix = "📄 "
            elif item.get('type') == 'command':
                prefix = "▶ "
                if i != self.selected_index:
                    text_color = COLORS['command_text']
            elif item.get('type') == 'argument':
                prefix = "  "
                if i != self.selected_index:
                    text_color = COLORS['argument_text']
            elif item.get('type') == 'process':
                prefix = "⚙ "
            
            # Draw main text
            text = item.get('text', '')
            text_surface = font.render(f"{prefix}{text}", True, text_color)
            surface.blit(text_surface, (item_rect.x + 8, item_rect.y + 2))
            
            # Draw description if present
            desc = item.get('desc', '')
            if desc:
                desc_color = COLORS['highlight_text'] if i == self.selected_index else COLORS['text_dim']
                desc_surface = font_small.render(desc, True, desc_color)
                desc_x = self.rect.x + self.rect.width - desc_surface.get_width() - 12
                surface.blit(desc_surface, (desc_x, item_rect.y + 6))
        
        # Reset clipping
        surface.set_clip(None)
        
        # Draw scrollbar if needed
        if len(self.items) > self.visible_items:
            self._draw_scrollbar(surface)
    
    def _draw_scrollbar(self, surface: pygame.Surface):
        """Draw the scrollbar"""
        scrollbar_width = 6
        scrollbar_x = self.rect.right - scrollbar_width - 2
        scrollbar_height = self.rect.height - 4
        
        # Calculate thumb size and position
        thumb_ratio = self.visible_items / len(self.items)
        thumb_height = max(20, scrollbar_height * thumb_ratio)
        
        scroll_ratio = self.scroll_offset / max(1, len(self.items) - self.visible_items)
        thumb_y = self.rect.y + 2 + (scrollbar_height - thumb_height) * scroll_ratio
        
        # Draw track
        track_rect = pygame.Rect(scrollbar_x, self.rect.y + 2, scrollbar_width, scrollbar_height)
        pygame.draw.rect(surface, COLORS['border'], track_rect, border_radius=3)
        
        # Draw thumb
        thumb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height)
        pygame.draw.rect(surface, COLORS['text_dim'], thumb_rect, border_radius=3)
