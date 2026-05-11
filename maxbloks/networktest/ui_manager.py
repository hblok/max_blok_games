# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import pygame
from typing import List, Callable, Optional


class UIManager:
    """Manages the pygame UI for the device discovery and pairing"""

    # Colors
    COLOR_BG = (20, 20, 30)
    COLOR_PANEL = (40, 40, 60)
    COLOR_TEXT = (220, 220, 220)
    COLOR_TEXT_DIM = (120, 120, 140)
    COLOR_HIGHLIGHT = (80, 120, 200)
    COLOR_SUCCESS = (80, 200, 120)
    COLOR_WARNING = (200, 180, 80)
    COLOR_ERROR = (200, 80, 80)

    # Keyboard mappings
    KEY_UP = pygame.K_UP
    KEY_DOWN = pygame.K_DOWN
    KEY_LEFT = pygame.K_LEFT
    KEY_RIGHT = pygame.K_RIGHT

    # Accept multiple keys for A/B to be PC-friendly
    KEYS_A = {pygame.K_z, pygame.K_RETURN, pygame.K_SPACE}
    KEYS_B = {pygame.K_x, pygame.K_ESCAPE, pygame.K_BACKSPACE}

    # Gamepad quit buttons (common: 8=Back/Select, 13=Menu/Home on some devices)
    GP_QUIT_BUTTONS = {8, 13}

    def __init__(self, width: int = 640, height: int = 480):
        """
        Initialize UI manager

        Args:
            width: Screen width
            height: Screen height
        """
        pygame.init()
        try:
            pygame.joystick.init()
        except Exception:
            pass

        # Gentle key repeat for keyboard navigation
        try:
            pygame.key.set_repeat(300, 100)
        except Exception:
            pass

        # Display surface (use existing from compat_sdl if present)
        existing = pygame.display.get_surface()
        if existing is not None:
            self.screen = existing
            self.width, self.height = existing.get_size()
        else:
            self.width = width
            self.height = height
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("Network Device Pairing")

        # Compute UI scale and fonts based on device and resolution
        self.ui_scale = self._compute_ui_scale()
        self.font_large = pygame.font.Font(None, self._px(36))
        self.font_medium = pygame.font.Font(None, self._px(28))
        self.font_small = pygame.font.Font(None, self._px(20))

        # State
        self.local_ip = "0.0.0.0"  # nosec
        self.discovered_devices: List[str] = []
        self.connected_devices: List[str] = []
        self.selected_index = 0
        self.status_message = "Starting..."
        self.status_color = self.COLOR_TEXT

        # Callbacks
        self.on_connect_pressed: Optional[Callable[[str], None]] = None
        self.on_disconnect_pressed: Optional[Callable[[str], None]] = None

        # Timing
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize joysticks/controllers (event-based only)
        self.joysticks = []
        try:
            for i in range(pygame.joystick.get_count()):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                self.joysticks.append(joy)
        except Exception:
            self.joysticks = []

    # --------- UI scaling helpers ---------

    def _compute_ui_scale(self) -> float:
        """
        Compute a UI scale factor based on resolution and probable device type.
        - Baseline is 1080p => scale 1.0
        - Below 1080p, scale up (e.g., 720p => ~1.5)
        - Handheld drivers ("mali", "kmsdrm", "fbcon") get a minimum scale bump
        - Optional override via env var UI_SCALE (e.g., UI_SCALE=1.8)
        """
        width, height = self.screen.get_size()
        # Scale relative to vertical resolution to keep consistent sizes
        scale = max(1.0, 1080.0 / float(max(1, height)))

        # Detect likely handheld/embedded drivers and ensure a minimum bump
        try:
            driver = pygame.display.get_driver() or ""
        except Exception:
            driver = ""
        if driver in {"mali", "kmsdrm", "fbcon"}:
            scale = max(scale, 1.35)

        # Allow explicit override
        env = os.environ.get("UI_SCALE")
        if env:
            try:
                override = float(env)
                # Allow range but clamp to keep reasonable sizing
                scale = max(0.8, min(override, 3.0))
            except Exception:
                pass

        return scale

    def _px(self, base_px: int) -> int:
        """Scale a pixel value by the UI scale (with sane minimums)."""
        # Ensure a reasonable minimum per font sizing
        val = int(round(base_px * self.ui_scale))
        return max(val, 12)

    def _s(self, v: int) -> int:
        """Generic spacing scaler."""
        return max(1, int(round(v * self.ui_scale)))

    # --------- Public API ---------

    def set_local_ip(self, ip: str):
        """Set the local IP address to display"""
        self.local_ip = ip

    def set_discovered_devices(self, devices: List[str]):
        """Update the list of discovered devices"""
        self.discovered_devices = devices
        if self.selected_index >= len(devices):
            self.selected_index = max(0, len(devices) - 1)

    def set_connected_devices(self, devices: List[str]):
        """Update the list of connected devices"""
        self.connected_devices = devices

    def set_status(self, message: str, status_type: str = "info"):
        """
        Set status message

        Args:
            message: Status message to display
            status_type: "info", "success", "warning", or "error"
        """
        self.status_message = message

        if status_type == "success":
            self.status_color = self.COLOR_SUCCESS
        elif status_type == "warning":
            self.status_color = self.COLOR_WARNING
        elif status_type == "error":
            self.status_color = self.COLOR_ERROR
        else:
            self.status_color = self.COLOR_TEXT

    def handle_events(self) -> bool:
        """
        Handle pygame events (keyboard + gamepad)

        Returns:
            True if application should continue running, False to quit
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == self.KEY_UP:
                    self._move_selection(-1)
                elif event.key == self.KEY_DOWN:
                    self._move_selection(1)
                elif event.key in self.KEYS_A:
                    self._handle_action_button()
                elif event.key in self.KEYS_B:
                    self._handle_b_button()
                elif event.key == pygame.K_ESCAPE:
                    # ESC quits on desktop
                    return False

            elif event.type == pygame.JOYBUTTONDOWN:
                # Common mapping: A=0, B=1, Back/Select=8, Menu/Home=13
                if event.button == 0:
                    self._handle_action_button()
                elif event.button == 1:
                    self._handle_b_button()
                elif event.button in self.GP_QUIT_BUTTONS:
                    # Handheld 'Menu' or 'Back/Select' quits
                    return False

            elif event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = event.value
                if hat_y == 1:
                    self._move_selection(-1)
                elif hat_y == -1:
                    self._move_selection(1)

        return True

    # --------- Internal actions ---------

    def _handle_b_button(self):
        """Handle B button: disconnect if selected is connected."""
        if len(self.discovered_devices) == 0:
            return
        if self.selected_index < len(self.discovered_devices):
            device_ip = self.discovered_devices[self.selected_index]
            if device_ip in self.connected_devices:
                if self.on_disconnect_pressed:
                    self.on_disconnect_pressed(device_ip)

    def _move_selection(self, delta: int):
        """Move selection up or down"""
        if len(self.discovered_devices) > 0:
            self.selected_index = (self.selected_index + delta) % len(self.discovered_devices)

    def _handle_action_button(self):
        """Handle A button press (connect/disconnect)"""
        if len(self.discovered_devices) == 0:
            return

        if self.selected_index < len(self.discovered_devices):
            device_ip = self.discovered_devices[self.selected_index]

            if device_ip in self.connected_devices:
                if self.on_disconnect_pressed:
                    self.on_disconnect_pressed(device_ip)
            else:
                if self.on_connect_pressed:
                    self.on_connect_pressed(device_ip)

    # --------- Rendering ---------

    def render(self):
        """Render the UI"""
        self.screen.fill(self.COLOR_BG)

        y_offset = self._s(20)

        # Title
        title = self.font_large.render("Device Pairing", True, self.COLOR_TEXT)
        self.screen.blit(title, (self._s(20), y_offset))
        y_offset += self._s(50)

        # Local IP
        ip_text = self.font_medium.render(f"My IP: {self.local_ip}", True, self.COLOR_SUCCESS)
        self.screen.blit(ip_text, (self._s(20), y_offset))
        y_offset += self._s(40)

        # Status
        status_text = self.font_small.render(f"Status: {self.status_message}", True, self.status_color)
        self.screen.blit(status_text, (self._s(20), y_offset))
        y_offset += self._s(35)

        # Separator line
        pygame.draw.line(self.screen, self.COLOR_PANEL, (self._s(20), y_offset), (self.width - self._s(20), y_offset), 2)
        y_offset += self._s(20)

        # Discovered devices section
        header = self.font_medium.render("Discovered Devices:", True, self.COLOR_TEXT)
        self.screen.blit(header, (self._s(20), y_offset))
        y_offset += self._s(35)

        row_h = self._s(30)
        dot_r = max(4, self._s(6))

        if len(self.discovered_devices) == 0:
            no_devices = self.font_small.render("Searching for devices...", True, self.COLOR_TEXT_DIM)
            self.screen.blit(no_devices, (self._s(40), y_offset))
        else:
            for i, device_ip in enumerate(self.discovered_devices):
                is_selected = (i == self.selected_index)
                is_connected = device_ip in self.connected_devices

                # Draw selection highlight
                if is_selected:
                    pygame.draw.rect(
                        self.screen,
                        self.COLOR_HIGHLIGHT,
                        (self._s(30), y_offset - self._s(5), self.width - self._s(60), row_h),
                        border_radius=self._s(5)
                    )

                # Connection status indicator
                status_color = self.COLOR_SUCCESS if is_connected else self.COLOR_TEXT_DIM
                pygame.draw.circle(self.screen, status_color, (self._s(50), y_offset + row_h // 2), dot_r)

                # Device IP
                text_color = self.COLOR_TEXT if is_selected else self.COLOR_TEXT_DIM
                device_text = self.font_small.render(device_ip, True, text_color)
                self.screen.blit(device_text, (self._s(70), y_offset))

                # Connection status text
                status = "CONNECTED" if is_connected else "Press A to connect"
                status_surface = self.font_small.render(status, True, text_color)
                self.screen.blit(status_surface, (self._s(250), y_offset))

                y_offset += self._s(35)

        # Instructions at bottom
        y_offset = self.height - self._s(100)
        pygame.draw.line(self.screen, self.COLOR_PANEL, (self._s(20), y_offset), (self.width - self._s(20), y_offset), 2)
        y_offset += self._s(15)

        instructions = [
            "Controls: ↑/↓ Select | A/Z/ENTER Connect | B/X/ESC Disconnect | Menu(8/13) or ESC to Quit"
        ]

        for instruction in instructions:
            inst_text = self.font_small.render(instruction, True, self.COLOR_TEXT_DIM)
            self.screen.blit(inst_text, (self._s(20), y_offset))
            y_offset += self._s(25)

        pygame.display.flip()

    def update(self, fps: int = 30):
        """Update the display with specified FPS"""
        self.clock.tick(fps)

    def quit(self):
        """Cleanup pygame"""
        try:
            for j in self.joysticks:
                try:
                    j.quit()
                except Exception:
                    pass
            pygame.joystick.quit()
        except Exception:
            pass
        pygame.quit()
