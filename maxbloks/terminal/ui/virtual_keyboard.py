# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Virtual Keyboard Module
On-screen keyboard for text input without physical keyboard
"""

import pygame
from typing import Optional, Callable, List, Tuple
from enum import Enum, auto


class KeyboardMode(Enum):
    """Keyboard input modes"""
    LOWERCASE = auto()
    UPPERCASE = auto()
    NUMBERS = auto()
    SYMBOLS = auto()


class InputType(Enum):
    """Input validation types"""
    TEXT = auto()           # Any text
    NUMERIC = auto()        # Numbers only
    PORT = auto()           # Port number (1-65535)
    URL = auto()            # URL format
    SSH_HOST = auto()       # user@hostname format
    FILENAME = auto()       # Valid filename characters


# Keyboard layouts
LAYOUTS = {
    KeyboardMode.LOWERCASE: [
        ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-'],
        ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '/'],
        ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ':', '@'],
        ['z', 'x', 'c', 'v', 'b', 'n', 'm', '.', '_', '~', '='],
        ['SHIFT', 'SPACE', 'SPACE', 'SPACE', 'SPACE', 'BACK', 'BACK', 'MODE', 'MODE', 'OK', 'OK'],
    ],
    KeyboardMode.UPPERCASE: [
        ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+'],
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '?'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', '"'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '|', '\\'],
        ['SHIFT', 'SPACE', 'SPACE', 'SPACE', 'SPACE', 'BACK', 'BACK', 'MODE', 'MODE', 'OK', 'OK'],
    ],
    KeyboardMode.NUMBERS: [
        ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.'],
        ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-'],
        ['+', '=', '[', ']', '{', '}', '|', '\\', '/', ':', ';'],
        ['"', "'", '<', '>', ',', '.', '?', '`', '~', '_', ' '],
        ['SHIFT', 'SPACE', 'SPACE', 'SPACE', 'SPACE', 'BACK', 'BACK', 'MODE', 'MODE', 'OK', 'OK'],
    ],
    KeyboardMode.SYMBOLS: [
        ['`', '~', '!', '@', '#', '$', '%', '^', '&', '*', '€'],
        ['(', ')', '-', '_', '+', '=', '[', ']', '{', '}', '£'],
        ['|', '\\', '/', ':', ';', '"', "'", '<', '>', ',', '¥'],
        ['.', '?', '©', '®', '™', '°', '±', '×', '÷', '¶', '§'],
        ['SHIFT', 'SPACE', 'SPACE', 'SPACE', 'SPACE', 'BACK', 'BACK', 'MODE', 'MODE', 'OK', 'OK'],
    ],
}

# Mode cycle order
MODE_ORDER = [KeyboardMode.LOWERCASE, KeyboardMode.UPPERCASE, KeyboardMode.NUMBERS, KeyboardMode.SYMBOLS]


class VirtualKeyboard:
    """
    Virtual on-screen keyboard for gamepad input
    """
    
    def __init__(self, screen_width: int, screen_height: int, colors: dict, font_manager):
        """
        Initialize the virtual keyboard
        
        Args:
            screen_width: Screen width
            screen_height: Screen height
            colors: Color dictionary from config
            font_manager: FontManager instance
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.colors = colors
        self.font_manager = font_manager
        
        # Keyboard dimensions
        self.key_width = 70
        self.key_height = 55
        self.key_spacing = 4
        self.padding = 20
        
        # Calculate keyboard size
        self.cols = 11
        self.rows = 5
        self.kb_width = self.cols * (self.key_width + self.key_spacing) - self.key_spacing
        self.kb_height = self.rows * (self.key_height + self.key_spacing) - self.key_spacing
        
        # Position keyboard at bottom center
        self.kb_x = (screen_width - self.kb_width) // 2
        self.kb_y = screen_height - self.kb_height - 80
        
        # Input field dimensions
        self.input_height = 50
        self.input_y = self.kb_y - self.input_height - 40
        self.input_x = self.kb_x
        self.input_width = self.kb_width
        
        # State
        self.visible = False
        self.mode = KeyboardMode.LOWERCASE
        self.selected_row = 0
        self.selected_col = 0
        self.input_text = ""
        self.cursor_pos = 0
        self.max_length = 256
        self.prompt = ""
        self.input_type = InputType.TEXT
        self.callback: Optional[Callable[[Optional[str]], None]] = None
        
        # Animation
        self.cursor_blink = 0
        self.cursor_visible = True
        
        # Special key spans (for wider keys)
        self.special_keys = {
            'SPACE': 4,  # Spans 4 columns
            'BACK': 2,   # Spans 2 columns
            'MODE': 2,   # Spans 2 columns
            'OK': 2,     # Spans 2 columns
            'SHIFT': 1,  # Single column
        }
    
    def show(self, prompt: str, callback: Callable[[Optional[str]], None],
             initial_text: str = "", input_type: InputType = InputType.TEXT,
             max_length: int = 256):
        """
        Show the virtual keyboard
        
        Args:
            prompt: Prompt text to display
            callback: Function to call with result (str or None if cancelled)
            initial_text: Pre-filled text
            input_type: Type of input validation
            max_length: Maximum input length
        """
        self.visible = True
        self.prompt = prompt
        self.callback = callback
        self.input_text = initial_text
        self.cursor_pos = len(initial_text)
        self.input_type = input_type
        self.max_length = max_length
        self.selected_row = 0
        self.selected_col = 0
        
        # Set appropriate starting mode based on input type
        if input_type in (InputType.NUMERIC, InputType.PORT):
            self.mode = KeyboardMode.NUMBERS
        else:
            self.mode = KeyboardMode.LOWERCASE
    
    def hide(self):
        """Hide the keyboard"""
        self.visible = False
        self.callback = None
    
    def _get_current_layout(self) -> List[List[str]]:
        """Get the current keyboard layout"""
        return LAYOUTS[self.mode]
    
    def _get_key_at(self, row: int, col: int) -> Optional[str]:
        """Get the key at the specified position"""
        layout = self._get_current_layout()
        if 0 <= row < len(layout) and 0 <= col < len(layout[row]):
            return layout[row][col]
        return None
    
    def _find_key_start(self, row: int, col: int) -> int:
        """Find the starting column of a key (for multi-column keys)"""
        layout = self._get_current_layout()
        if row >= len(layout):
            return col
        
        key = layout[row][col]
        start = col
        while start > 0 and layout[row][start - 1] == key:
            start -= 1
        return start
    
    def _get_key_width(self, key: str) -> int:
        """Get the display width of a key in columns"""
        return self.special_keys.get(key, 1)
    
    def _validate_char(self, char: str) -> bool:
        """
        Validate if a character is allowed for the current input type
        
        Args:
            char: Character to validate
            
        Returns:
            True if character is allowed
        """
        if self.input_type == InputType.TEXT:
            return True
        elif self.input_type == InputType.NUMERIC:
            return char.isdigit()
        elif self.input_type == InputType.PORT:
            return char.isdigit()
        elif self.input_type == InputType.URL:
            return char.isalnum() or char in '/:.-_?&=#%+@'
        elif self.input_type == InputType.SSH_HOST:
            return char.isalnum() or char in '@.-_'
        elif self.input_type == InputType.FILENAME:
            return char.isalnum() or char in '.-_'
        return True
    
    def _validate_input(self) -> Tuple[bool, str]:
        """
        Validate the complete input
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        text = self.input_text.strip()
        
        if not text:
            return False, "Input cannot be empty"
        
        if self.input_type == InputType.PORT:
            try:
                port = int(text)
                if not (1 <= port <= 65535):
                    return False, "Port must be 1-65535"
            except ValueError:
                return False, "Invalid port number"
        
        elif self.input_type == InputType.URL:
            if not (text.startswith('http://') or text.startswith('https://') or 
                    '.' in text or text.startswith('localhost')):
                return False, "Invalid URL format"
        
        elif self.input_type == InputType.SSH_HOST:
            if '@' in text:
                parts = text.split('@')
                if len(parts) != 2 or not parts[0] or not parts[1]:
                    return False, "Format: user@hostname"
        
        return True, ""
    
    def handle_input(self, action: str) -> bool:
        """
        Handle input action
        
        Args:
            action: Action name (UP, DOWN, LEFT, RIGHT, A, B, X, Y, START)
            
        Returns:
            True if keyboard should remain visible
        """
        if not self.visible:
            return False
        
        layout = self._get_current_layout()
        
        if action == 'UP':
            if self.selected_row > 0:
                self.selected_row -= 1
                # Adjust column to valid position
                self._adjust_column_position()
        
        elif action == 'DOWN':
            if self.selected_row < len(layout) - 1:
                self.selected_row += 1
                self._adjust_column_position()
        
        elif action == 'LEFT':
            # Move to previous key (handling multi-column keys)
            key = self._get_key_at(self.selected_row, self.selected_col)
            start = self._find_key_start(self.selected_row, self.selected_col)
            if start > 0:
                self.selected_col = start - 1
                # Find start of previous key
                self.selected_col = self._find_key_start(self.selected_row, self.selected_col)
        
        elif action == 'RIGHT':
            # Move to next key (handling multi-column keys)
            key = self._get_key_at(self.selected_row, self.selected_col)
            if key:
                key_width = self._get_key_width(key)
                start = self._find_key_start(self.selected_row, self.selected_col)
                next_col = start + key_width
                if next_col < len(layout[self.selected_row]):
                    self.selected_col = next_col
        
        elif action == 'A':
            # Press selected key
            self._press_key()
        
        elif action == 'B':
            # Backspace
            if self.cursor_pos > 0:
                self.input_text = self.input_text[:self.cursor_pos-1] + self.input_text[self.cursor_pos:]
                self.cursor_pos -= 1
        
        elif action == 'X':
            # Confirm input
            is_valid, error = self._validate_input()
            if is_valid:
                if self.callback:
                    self.callback(self.input_text)
                self.hide()
                return False
            # Could show error message here
        
        elif action == 'Y':
            # Toggle mode
            self._cycle_mode()
        
        elif action == 'START':
            # Cancel
            if self.callback:
                self.callback(None)
            self.hide()
            return False
        
        elif action == 'L':
            # Move cursor left
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
        
        elif action == 'R':
            # Move cursor right
            if self.cursor_pos < len(self.input_text):
                self.cursor_pos += 1
        
        return True
    
    def _adjust_column_position(self):
        """Adjust column position when changing rows"""
        layout = self._get_current_layout()
        if self.selected_row < len(layout):
            row = layout[self.selected_row]
            if self.selected_col >= len(row):
                self.selected_col = len(row) - 1
            # Snap to key start
            self.selected_col = self._find_key_start(self.selected_row, self.selected_col)
    
    def _press_key(self):
        """Press the currently selected key"""
        key = self._get_key_at(self.selected_row, self.selected_col)
        if not key:
            return
        
        if key == 'SPACE':
            if len(self.input_text) < self.max_length and self._validate_char(' '):
                self.input_text = self.input_text[:self.cursor_pos] + ' ' + self.input_text[self.cursor_pos:]
                self.cursor_pos += 1
        
        elif key == 'BACK':
            if self.cursor_pos > 0:
                self.input_text = self.input_text[:self.cursor_pos-1] + self.input_text[self.cursor_pos:]
                self.cursor_pos -= 1
        
        elif key == 'SHIFT':
            # Toggle between lowercase and uppercase
            if self.mode == KeyboardMode.LOWERCASE:
                self.mode = KeyboardMode.UPPERCASE
            elif self.mode == KeyboardMode.UPPERCASE:
                self.mode = KeyboardMode.LOWERCASE
        
        elif key == 'MODE':
            self._cycle_mode()
        
        elif key == 'OK':
            is_valid, error = self._validate_input()
            if is_valid:
                if self.callback:
                    self.callback(self.input_text)
                self.hide()
        
        else:
            # Regular character
            if len(self.input_text) < self.max_length and self._validate_char(key):
                self.input_text = self.input_text[:self.cursor_pos] + key + self.input_text[self.cursor_pos:]
                self.cursor_pos += 1
    
    def _cycle_mode(self):
        """Cycle through keyboard modes"""
        current_idx = MODE_ORDER.index(self.mode)
        next_idx = (current_idx + 1) % len(MODE_ORDER)
        self.mode = MODE_ORDER[next_idx]
    
    def update(self):
        """Update animations"""
        self.cursor_blink += 1
        if self.cursor_blink >= 30:
            self.cursor_blink = 0
            self.cursor_visible = not self.cursor_visible
    
    def draw(self, surface: pygame.Surface):
        """
        Draw the virtual keyboard
        
        Args:
            surface: Surface to draw on
        """
        if not self.visible:
            return
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        font_large = self.font_manager.get('large_bold')
        font_medium = self.font_manager.get('medium')
        font_small = self.font_manager.get('small')
        
        # Draw prompt
        prompt_surface = font_medium.render(self.prompt, True, self.colors['text'])
        surface.blit(prompt_surface, (self.input_x, self.input_y - 35))
        
        # Draw input field background
        input_rect = pygame.Rect(self.input_x, self.input_y, self.input_width, self.input_height)
        pygame.draw.rect(surface, self.colors['panel_bg'], input_rect, border_radius=8)
        pygame.draw.rect(surface, self.colors['highlight'], input_rect, 2, border_radius=8)
        
        # Draw input text with cursor
        text_x = self.input_x + 15
        text_y = self.input_y + (self.input_height - font_large.get_height()) // 2
        
        # Calculate visible portion of text
        max_visible_chars = (self.input_width - 30) // 14  # Approximate char width
        
        if len(self.input_text) <= max_visible_chars:
            visible_text = self.input_text
            cursor_offset = self.cursor_pos
            text_start = 0
        else:
            # Scroll text to keep cursor visible
            if self.cursor_pos < max_visible_chars // 2:
                text_start = 0
            elif self.cursor_pos > len(self.input_text) - max_visible_chars // 2:
                text_start = len(self.input_text) - max_visible_chars
            else:
                text_start = self.cursor_pos - max_visible_chars // 2
            
            visible_text = self.input_text[text_start:text_start + max_visible_chars]
            cursor_offset = self.cursor_pos - text_start
        
        # Draw text before cursor
        if cursor_offset > 0:
            before_cursor = visible_text[:cursor_offset]
            before_surface = font_large.render(before_cursor, True, self.colors['text'])
            surface.blit(before_surface, (text_x, text_y))
            cursor_x = text_x + before_surface.get_width()
        else:
            cursor_x = text_x
        
        # Draw cursor
        if self.cursor_visible:
            cursor_rect = pygame.Rect(cursor_x, text_y, 2, font_large.get_height())
            pygame.draw.rect(surface, self.colors['highlight'], cursor_rect)
        
        # Draw text after cursor
        if cursor_offset < len(visible_text):
            after_cursor = visible_text[cursor_offset:]
            after_surface = font_large.render(after_cursor, True, self.colors['text'])
            surface.blit(after_surface, (cursor_x + 4, text_y))
        
        # Draw character count
        count_text = f"{len(self.input_text)}/{self.max_length}"
        count_surface = font_small.render(count_text, True, self.colors['text_dim'])
        surface.blit(count_surface, (self.input_x + self.input_width - count_surface.get_width() - 10,
                                     self.input_y - 30))
        
        # Draw mode indicator
        mode_names = {
            KeyboardMode.LOWERCASE: "abc",
            KeyboardMode.UPPERCASE: "ABC",
            KeyboardMode.NUMBERS: "123",
            KeyboardMode.SYMBOLS: "#$%",
        }
        mode_text = f"Mode: {mode_names[self.mode]}"
        mode_surface = font_small.render(mode_text, True, self.colors['text_dim'])
        surface.blit(mode_surface, (self.input_x, self.input_y + self.input_height + 10))
        
        # Draw keyboard
        layout = self._get_current_layout()
        drawn_keys = set()  # Track drawn multi-column keys
        
        for row_idx, row in enumerate(layout):
            col_offset = 0
            col_idx = 0
            
            while col_idx < len(row):
                key = row[col_idx]
                
                # Skip if already drawn (multi-column key)
                key_id = (row_idx, self._find_key_start(row_idx, col_idx))
                if key_id in drawn_keys:
                    col_idx += 1
                    continue
                
                drawn_keys.add(key_id)
                
                # Calculate key dimensions
                key_span = self._get_key_width(key)
                key_w = key_span * (self.key_width + self.key_spacing) - self.key_spacing
                key_h = self.key_height
                
                # Calculate position
                start_col = self._find_key_start(row_idx, col_idx)
                key_x = self.kb_x + start_col * (self.key_width + self.key_spacing)
                key_y = self.kb_y + row_idx * (self.key_height + self.key_spacing)
                
                key_rect = pygame.Rect(key_x, key_y, key_w, key_h)
                
                # Check if selected
                is_selected = (row_idx == self.selected_row and 
                              self._find_key_start(self.selected_row, self.selected_col) == start_col)
                
                # Draw key background
                if is_selected:
                    pygame.draw.rect(surface, self.colors['highlight'], key_rect, border_radius=6)
                    text_color = self.colors['highlight_text']
                else:
                    pygame.draw.rect(surface, self.colors['panel_bg'], key_rect, border_radius=6)
                    pygame.draw.rect(surface, self.colors['border'], key_rect, 1, border_radius=6)
                    text_color = self.colors['text']
                
                # Special key colors
                if key in ('BACK', 'OK', 'MODE', 'SHIFT', 'SPACE'):
                    if not is_selected:
                        if key == 'OK':
                            text_color = self.colors['success']
                        elif key == 'BACK':
                            text_color = self.colors['error']
                        else:
                            text_color = self.colors['command_text']
                
                # Draw key label
                display_key = key
                if key == 'SPACE':
                    display_key = '␣ SPACE'
                elif key == 'BACK':
                    display_key = '⌫'
                elif key == 'SHIFT':
                    display_key = '⇧'
                elif key == 'MODE':
                    display_key = '🔄'
                elif key == 'OK':
                    display_key = '✓ OK'
                
                key_font = font_small if len(display_key) > 2 else font_medium
                key_surface = key_font.render(display_key, True, text_color)
                key_text_rect = key_surface.get_rect(center=key_rect.center)
                surface.blit(key_surface, key_text_rect)
                
                col_idx += 1
        
        # Draw button hints
        hints_y = self.kb_y + self.kb_height + 15
        hints = [
            ("A", "Type"),
            ("B", "Delete"),
            ("X", "Confirm"),
            ("Y", "Mode"),
            ("START", "Cancel"),
        ]
        
        hint_x = self.kb_x
        for btn, action in hints:
            btn_surface = font_small.render(btn, True, self.colors['highlight'])
            surface.blit(btn_surface, (hint_x, hints_y))
            hint_x += btn_surface.get_width() + 5
            
            action_surface = font_small.render(action, True, self.colors['text_dim'])
            surface.blit(action_surface, (hint_x, hints_y))
            hint_x += action_surface.get_width() + 20
