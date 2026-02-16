# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Background rendering and elements management
"""
import pygame
import math
import random
from maxbloks.dogrider.constants import *

class BackgroundManager:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.background_offset = 0
        self.mountain_offset = 0
        self.clouds = []
        self.trees = []
        self.birds = []
        self.grass_patches = []
        self.moles = []
        self.init_elements()
        
    def init_elements(self):
        """Initialize all background elements"""
        # Initialize clouds
        self.clouds = []
        for i in range(6):
            self.clouds.append({
                'x': random.randint(0, self.screen_width * 2),
                'y': random.randint(30, 120),
                'size': random.randint(15, 35),
                'speed': random.uniform(0.3, 0.8)
            })
        
        # Initialize trees
        self.trees = []
        for i in range(8):
            self.trees.append({
                'x': random.randint(self.screen_width, self.screen_width * 3),
                'height': random.randint(40, 80),
                'trunk_width': random.randint(8, 15),
                'crown_size': random.randint(25, 45)
            })
        
        # Initialize birds
        self.birds = []
        for i in range(4):
            self.birds.append({
                'x': random.randint(self.screen_width, self.screen_width * 2),
                'y': random.randint(50, 150),
                'speed': random.uniform(1.5, 3.0),
                'wing_phase': random.uniform(0, math.pi * 2),
                'flight_pattern': random.uniform(0, math.pi * 2)
            })
        
        # Initialize grass patches
        self.grass_patches = []
        for i in range(15):
            self.grass_patches.append({
                'x': random.randint(0, self.screen_width * 3),
                'type': random.choice(['light', 'dark', 'flower']),
                'size': random.randint(20, 60),
                'sway': random.uniform(0, math.pi * 2)
            })
        
        # Initialize moles
        self.moles = []
        
    def reset(self):
        """Reset background state"""
        self.background_offset = 0
        self.mountain_offset = 0
        self.init_elements()
        
    def update(self, game_speed):
        """Update all background elements"""
        # Update clouds
        for cloud in self.clouds:
            cloud['x'] -= cloud['speed']
            if cloud['x'] < -cloud['size'] * 2:
                cloud['x'] = self.screen_width + cloud['size']
                cloud['y'] = random.randint(30, 120)
        
        # Update trees
        for tree in self.trees:
            tree['x'] -= game_speed * 0.7
            if tree['x'] < -tree['crown_size']:
                tree['x'] = self.screen_width + random.randint(50, 200)
                tree['height'] = random.randint(40, 80)
                tree['trunk_width'] = random.randint(8, 15)
                tree['crown_size'] = random.randint(25, 45)
        
        # Update birds
        for bird in self.birds:
            bird['x'] -= bird['speed']
            bird['wing_phase'] += 0.3
            bird['flight_pattern'] += 0.05
            
            if bird['x'] < -20:
                bird['x'] = self.screen_width + random.randint(50, 200)
                bird['y'] = random.randint(50, 150)
                bird['speed'] = random.uniform(1.5, 3.0)
        
        # Update grass patches
        for patch in self.grass_patches:
            patch['x'] -= game_speed * 1.2
            patch['sway'] += 0.1
            
            if patch['x'] < -patch['size']:
                patch['x'] = self.screen_width + random.randint(20, 100)
                patch['type'] = random.choice(['light', 'dark', 'flower'])
                patch['size'] = random.randint(20, 60)
        
        # Spawn rare moles
        if random.random() < 0.001:
            self.moles.append({'x': self.screen_width, 'y': 370, 'phase': 0, 'life': 180})
        
        # Update moles
        for i in range(len(self.moles) - 1, -1, -1):
            mole = self.moles[i]
            mole['x'] -= game_speed
            mole['phase'] += 0.2
            mole['life'] -= 1
            
            if mole['life'] <= 0 or mole['x'] < -20:
                self.moles.pop(i)
        
        # Update offsets
        self.background_offset -= game_speed
        if self.background_offset < -20:
            self.background_offset = 0
            
        self.mountain_offset -= game_speed * 0.3
        if self.mountain_offset < -200:
            self.mountain_offset = 0
    
    def draw(self, screen, game_speed):
        """Draw all background elements"""
        # Sky gradient
        for i in range(self.screen_height):
            ratio = i / self.screen_height
            r = int(SKY_BLUE[0] * (1 - ratio) + GRASS_GREEN[0] * ratio)
            g = int(SKY_BLUE[1] * (1 - ratio) + GRASS_GREEN[1] * ratio)
            b = int(SKY_BLUE[2] * (1 - ratio) + GRASS_GREEN[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, i), (self.screen_width, i))
        
        # Mountains
        mountain_width = 200
        for i in range(math.ceil(self.screen_width / mountain_width)):
            x = self.mountain_offset + i * mountain_width
            points = [(x, 200), (x + 100, 50), (x + mountain_width, 200)]
            pygame.draw.polygon(screen, MOUNTAIN_BLUE, points)
            
        # Clouds
        for cloud in self.clouds:
            x, y, size = int(cloud['x']), int(cloud['y']), cloud['size']
            pygame.draw.circle(screen, WHITE, (x, y), size)
            pygame.draw.circle(screen, WHITE, (x + int(size * 0.6), y), int(size * 0.8))
            pygame.draw.circle(screen, WHITE, (x - int(size * 0.6), y), int(size * 0.6))
        
        # Trees
        for tree in self.trees:
            trunk_x = int(tree['x'])
            trunk_bottom = GROUND_Y
            trunk_top = trunk_bottom - tree['height']
            
            pygame.draw.rect(screen, TREE_BROWN, 
                            (trunk_x - tree['trunk_width']//2, trunk_top, 
                             tree['trunk_width'], tree['height']))
            pygame.draw.circle(screen, TREE_GREEN, (trunk_x, trunk_top), tree['crown_size'])
            pygame.draw.circle(screen, DARK_GREEN, (trunk_x, trunk_top), tree['crown_size'], 3)
        
        # Flying birds
        for bird in self.birds:
            bird['x'] -= bird['speed']
            bird['wing_phase'] += 0.3
            bird['flight_pattern'] += 0.05

            if bird['x'] < -20:
                bird['x'] = self.screen_width + random.randint(50, 200)
                bird['y'] = random.randint(50, 150)
                bird['speed'] = random.uniform(1.5, 3.0)

            y_offset = math.sin(bird['flight_pattern']) * 10
            bird_y = int(bird['y'] + y_offset)
            bird_x = int(bird['x'])

            wing_flap = math.sin(bird['wing_phase']) * 3
            pygame.draw.line(screen, BLACK, (bird_x, bird_y), (bird_x - 8, bird_y - 5 + wing_flap), 2)
            pygame.draw.line(screen, BLACK, (bird_x, bird_y), (bird_x - 8, bird_y + 5 - wing_flap), 2)

        # Ground
        pygame.draw.rect(screen, GRASS_GREEN, (0, 350, self.screen_width, self.screen_height - 350))

        # Foreground grass patches
        for patch in self.grass_patches:
            patch['x'] -= game_speed * 1.2
            patch['sway'] += 0.1

            if patch['x'] < -patch['size']:
                patch['x'] = self.screen_width + random.randint(20, 100)
                patch['type'] = random.choice(['light', 'dark', 'flower'])
                patch['size'] = random.randint(20, 60)

            x, y = int(patch['x']), 350
            size = patch['size']
            sway_offset = math.sin(patch['sway']) * 2

            if patch['type'] == 'light':
                color = LIGHT_GREEN
            elif patch['type'] == 'dark':
                color = DARK_GREEN
            else:
                color = LIGHT_GREEN

            # Draw grass blades
            for i in range(size // 4):
                blade_x = x + i * 4 + sway_offset
                blade_height = random.randint(8, 15)
                pygame.draw.line(screen, color, (blade_x, y), (blade_x + sway_offset, y - blade_height), 2)

            # Add flowers
            if patch['type'] == 'flower' and size > 30:
                flower_x = x + size // 2
                pygame.draw.circle(screen, YELLOW, (flower_x, y - 10), 3)
                pygame.draw.circle(screen, WHITE, (flower_x, y - 10), 2)

        # Very rare moles
        if random.random() < 0.001:
            self.moles.append({'x': self.screen_width, 'y': 370, 'phase': 0, 'life': 180})

        # Update and draw moles
        for i in range(len(self.moles) - 1, -1, -1):
            mole = self.moles[i]
            mole['x'] -= game_speed
            mole['phase'] += 0.2
            mole['life'] -= 1

            if mole['life'] <= 0 or mole['x'] < -20:
                self.moles.pop(i)
                continue

            pop_height = abs(math.sin(mole['phase'])) * 15
            mole_y = mole['y'] - pop_height

            # Draw mole
            pygame.draw.circle(screen, BROWN, (int(mole['x']), int(mole_y)), 8)
            pygame.draw.circle(screen, PINK, (int(mole['x'] + 3), int(mole_y - 2)), 2)
            pygame.draw.circle(screen, BLACK, (int(mole['x'] - 2), int(mole_y - 3)), 1)
            pygame.draw.circle(screen, BLACK, (int(mole['x'] + 1), int(mole_y - 3)), 1)

