"""
UI Components Module
Reusable UI elements for the terminal editor
"""

import pygame
from typing import List, Dict, Optional, Tuple, Callable
from config import (
    COLORS, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    LIST_ITEM_HEIGHT, SCROLL_SPEED, PAGE_SCROLL_ITEMS
)


class FontManager:
    """
    Manages fonts for the application
    """
    
    _instance = None
    _fonts = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        pygame.font.init()
        self._load_fonts()
    
    def _load_fonts(self):
        """Load all required fonts"""
        # Try to use a monospace font for terminal feel
        font_names = [
            'DejaVu Sans Mono',
            'Liberation Mono', 
            'Courier New',
            'monospace',
            None  # Fallback to default
        ]
        
        font_name = None
        for name in font_names:
            try:
                test_font = pygame.font.SysFont(name, 16)
                if test_font:
                    font_name = name
                    break
            except:
                continue
        
        self._fonts = {
            'large': pygame.font.SysFont(font_name, FONT_SIZE_LARGE),
            'medium': pygame.font.SysFont(font_name, FONT_SIZE_MEDIUM),
            'small': pygame.font.SysFont(font_name, FONT_SIZE_SMALL),
            'large_bold': pygame.font.SysFont(font_name, FONT_SIZE_LARGE, bold=True),
            'medium_bold': pygame.font.SysFont(font_name, FONT_SIZE_MEDIUM, bold=True),
        }
    
    def get(self, name: str) -> pygame.font.Font:
        """Get a font by name"""
        return self._fonts.get(name, self._fonts['medium'])


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


# Import os for path operations in CommandBuilder
import os