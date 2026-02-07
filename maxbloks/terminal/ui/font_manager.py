# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import pygame

from maxbloks.terminal.config.config import *

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

